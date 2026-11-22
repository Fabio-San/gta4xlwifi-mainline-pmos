#!/usr/bin/env python3
"""Pack a root-owned newc initramfs without requiring host root privileges."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import stat
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def archive(tree, output):
    ino = 0
    with output.open("wb") as out:
        def entry(name, mode, data=b"", rmajor=0, rminor=0):
            nonlocal ino
            ino += 1
            name = name.encode() + b"\0"
            values = [ino, mode, 0, 0, 2 if stat.S_ISDIR(mode) else 1, 0,
                      len(data), 0, 0, rmajor, rminor, len(name), 0]
            header = b"070701" + b"".join(f"{v:08x}".encode() for v in values)
            out.write(header + name)
            out.write(b"\0" * (-(len(header) + len(name)) % 4))
            out.write(data)
            out.write(b"\0" * (-len(data) % 4))

        entry(".", stat.S_IFDIR | 0o755)
        for path in sorted(tree.rglob("*")):
            name = path.relative_to(tree).as_posix()
            info = path.lstat()
            if name in ("dev/console", "dev/null"):
                continue
            if path.is_symlink():
                entry(name, info.st_mode, os.readlink(path).encode())
            elif path.is_dir():
                entry(name, info.st_mode)
            elif path.is_file():
                entry(name, info.st_mode, path.read_bytes())
            else:
                raise RuntimeError(f"Unexpected special file in build tree: {path}")
        entry("dev/console", stat.S_IFCHR | 0o600, rmajor=5, rminor=1)
        entry("dev/null", stat.S_IFCHR | 0o666, rmajor=1, rminor=3)
        entry("TRAILER!!!", 0)
        out.write(b"\0" * (-out.tell() % 512))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["oneshot", "persistent"], default="oneshot")
    p.add_argument("--root", choices=["ramdisk", "cache"], default="ramdisk")
    p.add_argument("--kernel", type=Path, help="Replacement raw arm64 Image")
    p.add_argument("--output", type=Path, help="Separate output, preserving known-good images")
    args = p.parse_args()
    tree = ROOT / "build/alpine"
    shutil.copytree(ROOT / "initramfs", tree, dirs_exist_ok=True)
    for file in [tree / "init", *(tree / "usr/local/sbin").iterdir()]:
        file.chmod(0o755)
    shutil.copy2(tree / "init", tree / "usr/local/sbin/linux-init")
    shutil.copy2(ROOT / "tools/hwctl-aarch64", tree / "init")
    (tree / "init").chmod(0o755)
    if not (tree / "init").read_bytes().startswith(b"\x7fELF"):
        raise RuntimeError("/init must be the static PID 1 supervisor")
    for name in ["init", "bin/busybox", "usr/local/sbin/linux-init",
                 "usr/local/sbin/adbd", "usr/local/sbin/hwctl",
                 "usr/local/sbin/setup-usb", "usr/local/sbin/restore-android"]:
        if not (tree / name).stat().st_mode & stat.S_IXUSR:
            raise RuntimeError(f"Required program is not executable: /{name}")
    (tree / "etc/gta4xl-mode").write_text(args.mode + "\n")
    (tree / "etc/gta4xl-root").write_text(args.root + "\n")
    suffix = "-cache" if args.root == "cache" else ""
    work = ROOT / "build" / (args.mode + suffix)
    work.mkdir(exist_ok=True)
    for file in ["kernel", "dtb"]:
        source = args.kernel if file == "kernel" and args.kernel else ROOT / "build/android-boot" / file
        shutil.copy2(source, work / file)
    archive(tree, work / "ramdisk.cpio")
    output = args.output.resolve() if args.output else ROOT / "artifacts" / f"boot-linux-{args.mode}{suffix}.img"
    subprocess.run([str(ROOT / "tools/magiskboot"), "repack",
                    str(ROOT / "backups/boot-android.img"), str(output)], cwd=work, check=True)
    if output.stat().st_size > 61865984:
        raise RuntimeError("Image exceeds the boot partition")
    print(f"{output}: {output.stat().st_size} bytes; sha256 {hashlib.sha256(output.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
