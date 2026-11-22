#!/usr/bin/env python3
"""Check compiled Exynos9610 CPU capacity, cache sharing and OPP metadata."""
import argparse
import json
from pathlib import Path
import struct


def read_fdt(path):
    data = path.read_bytes()
    magic, total, structure, strings, _, _, _, _, string_size, struct_size = struct.unpack_from('>10I', data)
    if magic != 0xd00dfeed or total > len(data):
        raise ValueError('Invalid DTB header')
    names = data[strings:strings + string_size]
    offset, limit = structure, structure + struct_size
    stack, nodes = [], {}
    while offset < limit:
        token = struct.unpack_from('>I', data, offset)[0]
        offset += 4
        if token == 1:
            end = data.index(0, offset)
            stack.append(data[offset:end].decode())
            offset = (end + 4) & ~3
            nodes['/' + '/'.join(stack[1:])] = {}
        elif token == 2:
            stack.pop()
        elif token == 3:
            size, name_offset = struct.unpack_from('>2I', data, offset)
            offset += 8
            end = names.index(0, name_offset)
            name = names[name_offset:end].decode()
            nodes['/' + '/'.join(stack[1:])][name] = data[offset:offset + size]
            offset = (offset + size + 3) & ~3
        elif token == 4:
            continue
        elif token == 9:
            return nodes
        else:
            raise ValueError(f'Invalid FDT token {token}')
    raise ValueError('Missing FDT end token')


def u32(value):
    if len(value) != 4:
        raise ValueError('Expected one u32 cell')
    return struct.unpack('>I', value)[0]


def check(path, config_path):
    nodes = read_fdt(path)
    refs = {u32(props['phandle']): name for name, props in nodes.items() if 'phandle' in props}
    cpus = sorted((name, props) for name, props in nodes.items()
                  if name.startswith('/cpus/cpu@') and props.get('device_type') == b'cpu\0')
    if len(cpus) != 8:
        raise ValueError('Expected exactly eight CPU nodes')
    if {u32(props['reg']) for _, props in cpus} != {0, 1, 2, 3, 256, 257, 258, 259}:
        raise ValueError('CPU addresses must identify both complete clusters')
    reports = []
    for name, props in cpus:
        reg = u32(props['reg'])
        cluster = reg >> 8
        if cluster not in (0, 1) or (reg & 255) > 3:
            raise ValueError(f'Unexpected CPU address in {name}')
        if props['compatible'] != (b'arm,cortex-a53\0', b'arm,cortex-a73\0')[cluster]:
            raise ValueError(f'Unexpected CPU type in {name}')
        raw = u32(props['capacity-dmips-mhz'])
        if raw != (230, 480)[cluster]:
            raise ValueError(f'Incorrect or missing raw capacity on {name}')
        cache = refs[u32(props['next-level-cache'])]
        cache_props = nodes[cache]
        if cache_props['compatible'] != b'cache\0' or u32(cache_props['cache-level']) != 2:
            raise ValueError(f'Invalid L2 cache on {name}')
        if 'cache-unified' not in cache_props:
            raise ValueError(f'L2 must be unified on {name}')
        opp = refs[u32(props['operating-points-v2'])]
        if 'opp-shared' not in nodes[opp]:
            raise ValueError(f'OPP sharing missing for {name}')
        rates = sorted(struct.unpack('>Q', p['opp-hz'])[0] // 1000
                       for n, p in nodes.items()
                       if n.startswith(opp + '/') and 'opp-hz' in p)
        expected = ((403000, 1742000, 13), (936000, 2314000, 15))[cluster]
        if (min(rates), max(rates), len(rates)) != expected:
            raise ValueError(f'CPU OPPs changed for {name}: {rates}')
        reports.append({'cpu': name, 'cluster': cluster, 'raw': raw,
                        'max_kHz': max(rates), 'cache': cache, 'opp': opp})
    for cluster in (0, 1):
        group = [r for r in reports if r['cluster'] == cluster]
        if len(group) != 4 or len({r['cache'] for r in group}) != 1 or len({r['opp'] for r in group}) != 1:
            raise ValueError('Expected four CPUs sharing one cache and one OPP table per cluster')
    if len({r['cache'] for r in reports}) != 2:
        raise ValueError('Little and big clusters must have distinct L2 caches')
    maximum = max(r['raw'] * r['max_kHz'] for r in reports)
    for report in reports:
        report['normalized_capacity'] = report['raw'] * report['max_kHz'] * 1024 // maximum
        if report['normalized_capacity'] != (369, 1024)[report['cluster']]:
            raise ValueError('Unexpected topology normalization')
    config = config_path.read_text()
    for key in ('SMP', 'SCHED_MC', 'CPUFREQ_DT', 'CPU_FREQ_DEFAULT_GOV_SCHEDUTIL',
                'CPU_FREQ_THERMAL', 'DEVFREQ_THERMAL', 'EXYNOS9610_BOOT_THERMAL'):
        if f'CONFIG_{key}=y\n' not in config:
            raise ValueError(f'CONFIG_{key} is required')
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dtb', type=Path)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--quiet', action='store_true')
    args = parser.parse_args()
    try:
        reports = check(args.dtb, args.config)
    except (ValueError, KeyError, struct.error) as error:
        raise SystemExit(f'Topology preflight failed: {error}') from error
    if args.quiet:
        print('CPU topology preflight passed: capacities 369/1024, two L2 domains, stock OPPs')
    else:
        print(json.dumps({'pass': True, 'cpus': reports}, indent=2))


if __name__ == '__main__':
    main()
