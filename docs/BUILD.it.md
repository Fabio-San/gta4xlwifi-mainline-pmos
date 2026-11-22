# BUILD.it.md — Compilazione kernel 7.3 e boot.img (Italiano)

Versione primaria: [BUILD.md](BUILD.md)

## Prerequisiti
WSL2/Ubuntu o Linux x86_64, ~10 GB liberi, strumenti:
```bash
sudo apt install -y git python3 build-essential crossbuild-essential-arm64 \
  device-tree-compiler cpio gzip xz-utils curl wget openssl \
  clang lld llvm bison flex libssl-dev
```

> **Importante**: clonare/buildare in una cartella il cui percorso **non contenga spazi** (es. `~/gta4xlwifi-mainline-pmos`). Il Makefile del kernel con `O=` non gestisce i percorsi con spazi.

## Setup
```bash
git clone https://github.com/Fabio-San/gta4xlwifi-mainline-pmos.git
cd gta4xlwifi-mainline-pmos && git checkout pmos
bash scripts/setup-build-env.sh   # clona kernel 7.3 e applica le patch
```

## Configurazione
`configs/upstream/gta4xl.config` + frammento touch `92-mainline-himax.conf`.
- `CONFIG_MODULES=y`, Panfrost/DPU zero-copy abilitati
- **MFC disabilitato**: nodo `mfc@12c30000` rimosso dal DTS (vedi `reapply-kernel-patches.sh`)

## Build
```bash
bash scripts/build-upstream.sh
# oppure:
python3 scripts/build-upstream.py --slot boot --no-fallback \
  --variant peripherals --persistent --jobs "$(nproc)"
```

## Verifica
```bash
sha256sum artifacts/boot-upstream-peripherals-nofallback-persistent.img
```
SHA atteso: `d71a7d110e93ca35aecbcc51baa72f1daf0eb39fc5fa7e38a38f2a3bda5f1212`

## Note
- L'init è **embedded nel kernel** tramite uniLoader: modificare il ramdisk esterno non serve.
- Se il boot spamma `s5p_mfc_wait_for_done_dev`, esegui `reapply-kernel-patches.sh`.
