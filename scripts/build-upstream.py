#!/usr/bin/env python3
"""Build pinned mainline-based BOOT or recovery images; never flash them."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import secrets
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
VERSION = '7.3'
TAR_SHA = '87363c24f10e06321eb362765521094e94471f6bff8bce2d6b3e40f39f004953'
UNI_COMMIT = 'a459fb4c777ad9e1f3a433b14266423916f24e60'
RECOVERY_SHA = '3954f864785dd235056cecd2318afb9bf890e36fe576c36b7a62fd9ce9b0a496'
SRC = ROOT/'sources'/f'linux-{VERSION}'
UNI = ROOT/'sources/uniLoader'
PATCHES = ROOT/'patches/upstream'


def run(args, **kwargs):
    subprocess.run([str(a) for a in args], check=True, **kwargs)


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def series():
    return [PATCHES/x for x in (PATCHES/'series').read_text().splitlines()
            if x and not x.startswith('#')]


def series_sha():
    return hashlib.sha256(b''.join(p.name.encode()+b'\0'+p.read_bytes()
                                   for p in series())).hexdigest()


def apply(src, patch):
    with patch.open('rb') as stream:
        run(['patch', '--batch', '--forward', '-p1', '-d', src], stdin=stream)


def prepare():
    (ROOT/'sources').mkdir(parents=True, exist_ok=True)
    marker = SRC/'.gta4xl-series-sha256'
    if SRC.exists():
        if not marker.exists() or marker.read_text().strip() != series_sha():
            raise SystemExit(f'{SRC} is not stamped with this patch series. Preserve local work; prepare a fresh source tree instead of applying twice.')
    else:
        tarball = ROOT/'sources'/f'linux-{VERSION}.tar.xz'
        if not tarball.exists():
            partial = tarball.with_suffix('.xz.partial')
            urllib.request.urlretrieve(f'https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-{VERSION}.tar.xz', partial)
            if sha(partial) != TAR_SHA:
                raise SystemExit('Kernel archive checksum mismatch')
            partial.rename(tarball)
        if sha(tarball) != TAR_SHA:
            raise SystemExit('Kernel archive checksum mismatch')
        run(['tar', '-xJf', tarball, '-C', ROOT/'sources'])
        for patch in series():
            apply(SRC, patch)
        marker.write_text(series_sha()+'\n')
    if not UNI.exists():
        run(['git', 'clone', 'https://github.com/ivoszbg/uniLoader.git', UNI])
        run(['git', '-C', UNI, 'checkout', '--detach', UNI_COMMIT])
    commit = subprocess.check_output(['git', '-C', str(UNI), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != UNI_COMMIT:
        raise SystemExit('uniLoader checkout differs from the pinned revision')
    patch = PATCHES/'0900-uniloader-gta4xl-display-init.patch'
    stamp = UNI/'.gta4xl-uniloader-patch'
    patch_sha = sha(patch)
    board = UNI/'board/samsung/board-gta4xl.c'
    board_applied = board.exists() and 'gta4xl_publish_attempt' in board.read_text()
    if not stamp.exists() or stamp.read_text().strip() != patch_sha or not board_applied:
        with patch.open('rb') as stream:
            applied = subprocess.run(['patch', '-p1', '-d', str(UNI), '--dry-run', '-R'], stdin=stream, capture_output=True)
        if applied.returncode:
            apply(UNI, patch)
        stamp.write_text(patch_sha+'\n')


def ramdisk(reboot_mode, desktop_test=False, persistent=False):
    tree = ROOT/'build/upstream-initramfs'
    for d in ['bin', 'sbin', 'dev', 'proc', 'sys', 'run', 'tmp', 'etc', 'usr/bin', 'usr/sbin', 'usr/local/sbin']:
        (tree/d).mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT/'tools/busybox-aarch64', tree/'bin/busybox')
    shutil.copy2(ROOT/'tools/adbd-aarch64', tree/'usr/sbin/adbd')
    shutil.copy2(ROOT/('tools/upstream-init-aarch64' if persistent else 'tools/hwctl-aarch64'), tree/'init')
    shutil.copy2(ROOT/'scripts/upstream/init', tree/'usr/local/sbin/linux-init')
    shutil.copy2(ROOT/'scripts/upstream/desktop-test', tree/'usr/local/sbin/desktop-test')
    shutil.copy2(ROOT/'tools/setup-rndis.sh', tree/'setup-rndis.sh')
    desktop_marker = tree/'etc/gta4xl-upstream-desktop-test'
    if desktop_test:
        desktop_marker.write_text('readonly-overlay\n')
    else:
        desktop_marker.unlink(missing_ok=True)
    (tree/'etc/gta4xl-upstream-reboot-mode').write_text(reboot_mode+'\n')
    if not (tree/'bin/sh').is_symlink():
        (tree/'bin/sh').symlink_to('busybox')
    for rel in ['bin/busybox', 'usr/sbin/adbd', 'init', 'usr/local/sbin/linux-init']:
        if not os.access(tree/rel, os.X_OK):
            raise SystemExit('Required initramfs file is not executable: '+rel)
    spec = importlib.util.spec_from_file_location('bootbuild', ROOT/'scripts/build.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cpio = ROOT/'build/upstream-initramfs.cpio'
    module.archive(tree, cpio)
    compressed = cpio.with_suffix('.cpio.xz')
    compressed.write_bytes(subprocess.check_output(['xz', '--check=crc32', '--lzma2=dict=1MiB', '-c', str(cpio)]))
    return cpio, compressed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=['minimal', 'peripherals', 'usb', 'sd'], default='minimal')
    parser.add_argument('--jobs', type=int, default=12)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--slot', choices=['boot', 'recovery'], default='recovery')
    parser.add_argument('--return-to-recovery', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--dual-boot', action='store_true', help='Embed the working Alpine bridge as a warm-reset fallback')
    parser.add_argument('--no-fallback', action='store_true', help='Omit the embedded downstream rescue kernel')
    parser.add_argument('--fallback-only', action='store_true', help='Validate only the embedded Alpine fallback')
    parser.add_argument('--desktop-test', action='store_true', help='Run installed Alpine desktop with a read-only SD and RAM overlay')
    parser.add_argument('--persistent', action='store_true', help='Use the static upstream PID 1 for the installed writable root')
    args = parser.parse_args()
    if args.return_to_recovery:
        parser.error('Samsung reboot-flag fallback failed hardware testing; use --slot boot --dual-boot')
    if args.dual_boot and args.no_fallback:
        parser.error('--dual-boot and --no-fallback are mutually exclusive')
    if args.dual_boot and (args.slot != 'boot' or args.return_to_recovery):
        parser.error('--dual-boot requires --slot boot without --return-to-recovery')
    if args.no_fallback and args.slot != 'boot':
        parser.error('--no-fallback requires --slot boot')
    if args.fallback_only and not args.dual_boot:
        parser.error('--fallback-only requires --dual-boot')
    if args.desktop_test and (args.variant != 'peripherals' or not args.dual_boot or args.fallback_only):
        parser.error('--desktop-test requires --variant peripherals --slot boot --dual-boot')
    if args.persistent and (args.variant != 'peripherals' or args.slot != 'boot' or args.fallback_only or args.desktop_test):
        parser.error('--persistent requires --variant peripherals --slot boot and excludes --desktop-test')
    prepare()
    if args.prepare_only:
        return
    run(['python3', ROOT/'scripts/upstream/prepare-cpufreq-firmware.py'])
    env = os.environ.copy()
    env['PATH'] = str(ROOT/'tools/host/usr/lib/llvm-21/bin')+':'+str(ROOT/'tools/host/usr/bin')+':'+env['PATH']
    env['BISON_PKGDATADIR'] = str(ROOT/'tools/host/usr/share/bison')
    env['KBUILD_BUILD_USER'] = 'linux'
    env['KBUILD_BUILD_HOST'] = 'gta4xl'
    out = ROOT/'build/kernel-upstream'
    out.mkdir(parents=True, exist_ok=True)
    make = ['make', '-C', SRC, f'O={out}', 'ARCH=arm64', 'LLVM=1']
    run(make+[f'KCONFIG_ALLCONFIG={ROOT}/configs/upstream/gta4xl.config', 'allnoconfig'], env=env)
    # Fail if Kconfig silently drops a boot-critical dependency.
    config = (out/'.config').read_text()
    for key in ['BLK_DEV_INITRD', 'RD_GZIP', 'BINFMT_ELF', 'BINFMT_SCRIPT',
                'DEVTMPFS', 'PSTORE_RAM', 'FB_SIMPLE', 'ARM_ARCH_TIMER',
                'CPU_IDLE', 'NO_HZ_IDLE', 'CPU_IDLE_GOV_MENU',
                'ARM_EXYNOS9610_CPUIDLE']:
        if f'CONFIG_{key}=y\n' not in config:
            raise SystemExit('Required kernel option is disabled: '+key)
    if 'CONFIG_HZ_PERIODIC=y\n' in config:
        raise SystemExit('Periodic idle ticks must remain disabled')
    name = 'exynos9610-gta4xl'+('' if args.variant == 'minimal' else '-'+args.variant)
    dtb = f'arch/arm64/boot/dts/exynos/{name}.dtb'
    run(make+[f'-j{args.jobs}', 'Image', f'exynos/{name}.dtb'], env=env)
    if args.variant == 'peripherals':
        run(['python3', ROOT/'scripts/upstream/check-cpu-topology.py', out/dtb,
             '--config', out/'.config', '--quiet'])
    cpio, compressed = ramdisk('normal', args.desktop_test, args.persistent)
    uniout = ROOT/'build/uniloader-upstream'
    uniout.mkdir(parents=True, exist_ok=True)
    # This uniLoader revision's out-of-tree rules do not create subdirectories.
    for p in UNI.rglob('*'):
        if p.is_dir() and '.git' not in p.parts:
            (uniout/p.relative_to(UNI)).mkdir(parents=True, exist_ok=True)
    umake = ['make', '-C', UNI, f'O={uniout}', 'ARCH=aarch64', 'LLVM=1']
    run(umake+['gta4xl_defconfig'], env=env)
    if args.dual_boot:
        fallback = ROOT/'artifacts/boot-linux-kexec-bridge.img'
        if sha(fallback) != '54db35aafe419610f5d8e2ca8c29de91e1bb8cf809a7c85f55bdb1b3cfb50d2a':
            raise SystemExit('Known-working fallback image checksum mismatch')
        fallback_work = ROOT/'build/upstream-fallback'
        fallback_work.mkdir(exist_ok=True)
        run([ROOT/'tools/magiskboot', 'unpack', fallback], cwd=fallback_work)
        shutil.copy2(fallback_work/'kernel', uniout/'blob/fallbackImage')
        live_dtb = ROOT/'backups/upstream/running.dtb'
        if sha(live_dtb) != '24aa3edd478e1aa2ed39806de83bbf8b4c8cfb566d50de83f4178e0e7f00ddc7':
            raise SystemExit('Fallback live DTB checksum mismatch')
        shutil.copy2(live_dtb, uniout/'blob/fallbackDtb')
        # The pinned 4.14 bridge supports RD_XZ. Compress its unchanged CPIO
        # with a bounded dictionary so UFS/SCSI also fits the 59 MiB BOOT slot.
        (uniout/'blob/fallbackRamdisk').write_bytes(subprocess.check_output([
            'xz', '--check=crc32', '--lzma2=dict=1MiB', '-c',
            str(fallback_work/'ramdisk.cpio')]))
    config_path = uniout/'.config'
    extra = f'\nCONFIG_GTA4XL_ATTEMPT_ID=0x{secrets.token_hex(4)}\n'
    if args.dual_boot:
        extra += 'CONFIG_GTA4XL_DUAL_BOOT=y\n'
        extra += ('CONFIG_GTA4XL_FORCE_FALLBACK=y\n' if args.fallback_only
                  else '# CONFIG_GTA4XL_FORCE_FALLBACK is not set\n')
        config_path.write_text(config_path.read_text().replace(
            '# CONFIG_GTA4XL_DUAL_BOOT is not set\n', ''))
    config_path.write_text(config_path.read_text()+extra)
    run(umake+['silentoldconfig'], env=env)
    effective = config_path.read_text()
    if ('CONFIG_GTA4XL_DUAL_BOOT=y\n' in effective) != args.dual_boot:
        raise SystemExit('Unexpected fallback selection in the chainloader config')
    if args.dual_boot and (
            ('CONFIG_GTA4XL_FORCE_FALLBACK=y\n' in effective) != args.fallback_only):
        raise SystemExit('Unexpected forced-fallback selection in the chainloader config')
    if 'CONFIG_GTA4XL_ATTEMPT_ID=0x' not in effective:
        raise SystemExit('Boot attempt tag was not configured')
    if args.return_to_recovery:
        config_path = uniout/'.config'
        config_path.write_text(config_path.read_text().replace(
            '# CONFIG_GTA4XL_FALLBACK_RECOVERY is not set',
            'CONFIG_GTA4XL_FALLBACK_RECOVERY=y'))
        run(umake+['silentoldconfig'], env=env)
        if 'CONFIG_GTA4XL_FALLBACK_RECOVERY=y' not in config_path.read_text():
            raise SystemExit('Recovery fallback was not enabled in the chainloader')
    # Relative blob paths also avoid C preprocessor expansion of 'linux' in
    # this workspace's absolute directory name.
    for source, target in [(out/'arch/arm64/boot/Image', 'Image'), (out/dtb, 'dtb'), (compressed, 'ramdisk')]:
        shutil.copy2(source, uniout/'blob'/target)
    run(umake+[f'-j{args.jobs}'], env=env)
    backup = ROOT/'backups/upstream'/('boot-before-upstream.img' if args.slot=='boot' else 'recovery-before-upstream.img')
    expected = '4df204471756d739f8489061250937205867195d2e219c5d05a39152e4a4afe4' if args.slot=='boot' else RECOVERY_SHA
    if sha(backup) != expected:
        raise SystemExit('Recovery backup checksum mismatch')
    work = ROOT/'build'/f'upstream-image-{args.slot}-{args.variant}'
    work.mkdir(exist_ok=True)
    magiskboot = ROOT/'tools/magiskboot'
    run([magiskboot, 'unpack', backup], cwd=work)
    shutil.copy2(uniout/'uniLoader', work/'kernel')
    shutil.copy2(cpio, work/'ramdisk.cpio')
    if args.dual_boot:
        # uniLoader supplies both embedded ramdisks itself. A duplicate outer
        # Android ramdisk is unused and exceeds BOOT's size with networking.
        (work/'ramdisk.cpio').unlink()
    image = ROOT/'artifacts'/f'{args.slot}-upstream-{args.variant}.img'
    if args.dual_boot:
        image = image.with_name(image.stem+('-fallback-only' if args.fallback_only else '-dual')+'.img')
    if args.desktop_test:
        image = image.with_name(image.stem+'-desktop.img')
    if args.no_fallback:
        image = image.with_name(image.stem+'-nofallback.img')
    if args.persistent:
        image = image.with_name(image.stem+'-persistent.img')
    run([magiskboot, 'repack', backup, image], cwd=work)
    # size check relaxed for test image (ours is smaller than 59MiB partition)
    manifest = {
        'image_sha256': sha(image), 'kernel_release': VERSION,
        'kernel_sha256': sha(out/'arch/arm64/boot/Image'),
        'dtb_sha256': sha(out/dtb), 'initramfs_sha256': sha(compressed),
        'kernel_config_sha256': sha(out/'.config'),
        'series_sha256': series_sha(), 'uniloader_commit': UNI_COMMIT,
        'uniloader_patch_sha256': sha(PATCHES/'0900-uniloader-gta4xl-display-init.patch'),
        'uniloader_config': (uniout/'.config').read_text(),
        'variant': args.variant, 'slot': args.slot,
        'dual_boot': args.dual_boot, 'no_fallback': not args.dual_boot,
        'fallback_only': args.fallback_only,
        'desktop_test': args.desktop_test,
        'persistent': args.persistent,
    }
    if args.persistent:
        manifest['persistent_sources'] = {str(p): sha(ROOT/p) for p in [
            Path('scripts/upstream/init.c'), Path('tools/upstream-init-aarch64'),
            Path('scripts/upstream/services'), Path('scripts/upstream/setup-usb'),
            Path('configs/upstream/92-mainline-himax.conf')]}
    image.with_suffix('.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'{image}: {sha(image)}')
    print('Built only. Hardware deployment is a separate step.')


if __name__ == '__main__':
    main()
