# AI_WORKFLOW.md — Working with AI assistants on this port

This port was built collaboratively by a human (Fabio-San) and several AI assistants
(Hy4 flash Free / OpenCode, Gemini 4 Hydrogen, ChatGPT Luna 6, Antigravity). This
document captures **how to keep working effectively and safely with AI** on this
project. It is written from field experience, not theory.

> Italian: [AI_WORKFLOW.it.md](AI_WORKFLOW.it.md)

---

## 1. The human sets the direction; the AI does the heavy lifting

The most productive pattern observed here:

- **Human**: decides *what* to try, owns the hardware, runs the flash/reboot cycle,
  reports what appears on screen, and makes the final call on risk.
- **AI**: investigates code, reads logs, writes scripts, reasons about root causes,
  and produces documentation.

Do not let the AI decide to flash something without explicit confirmation. Every
flash in this project was preceded by a clear "flash this?" question and a verified
backup.

## 2. The prompt that worked best with Gemini

The original author used this suffix to force deep, non-hallucinated reasoning:

```
Dai una risposta completa dopo analisi e ragionamenti profondi e sensati, senza inventare nulla
```

("Give a complete answer after deep and sensible analysis and reasoning, inventing nothing.")

Use a similar instruction with any model: ask for **evidence-based answers**, state
that speculation must be labeled as such, and require the model to say "I don't know"
when the logs are insufficient.

## 3. Always give the AI the real evidence

Good prompts include:

- the **exact error text** (copy-paste from `dmesg`, journal, pstore, screen),
- the **SHA256 of the boot image** being used (so both sides know the same build),
- `uname -r`, `cat /etc/os-release`, relevant `dmesg` lines,
- what was **already tried** and what changed between attempts.

Example of a productive prompt:

```
Boot SHA256 d71a7d11... on SM-P610, kernel 7.3. Symptom: "Failed to set up the root
directory for shared mount propagation: Invalid argument". Init script does
mount --make-rshared $M but no mount --bind. Already tried: adding rshared alone.
Give the exact cause and a fix sequence; label anything uncertain.
```

That prompt led to the correct `mount --bind "$M" "$M"` diagnosis.

## 4. Verify AI claims against primary sources

Gemini suggested a "HakiOS A51 port on Exynos 9611". We verified it with the GitHub
API instead of trusting the summary: the repos `oosexgang/hakios-xnu-kernel` and
`speedyg2200/hakios-device-a51` really exist and are active. **Rule: when an AI cites
a repo, file, address or commit, open it.** If it cannot be opened, treat it as
unverified.

## 5. Keep a single source of truth

- This repository is the source of truth for configs, patches and docs.
- Never paste a "final" script only into a chat: commit it here.
- Keep the worklog (`docs/WORKLOG.md`) updated so the next assistant starts from
  facts, not from a stale chat summary.

## 6. Safety rules for AI-assisted flashing

1. The AI must **never** flash anything without explicit human confirmation.
2. Always back up `boot`, `dtbo`, `recovery`, `vbmeta` first.
3. **Never flash `bootloader` or `vbmeta`** on these Samsung devices.
4. After every flash, verify by reading the partition back and comparing SHA256.
5. If a boot fails, restore the known-good image before experimenting further.

## 7. Protect personal data

- Never paste WiFi passwords, device serials, MAC addresses, IP addresses, SSH keys
  or personal files into a prompt or a repo.
- The sterile ROM builder (`scripts/make-sterile-rom.sh`) enforces this with an
  automated sensitive-pattern check before packing.
- When asking for help, replace identifiers with placeholders: `<SERIAL>`, `<IP>`,
  `<SSID>`, `<PASSWORD>`.

## 8. Useful roles for the different assistants observed here

| Assistant | Worked well for |
|---|---|
| Hy4 flash Free (OpenCode) | Code, scripts, iterative debugging, repo/docs |
| Gemini 4 Hydrogen | Deep kernel/VFS reasoning, firmware analysis, cross-checks |
| ChatGPT Luna 6 | Alternative reasoning, second opinions |
| Antigravity | Additional analysis and validation |

Use **two models** for hard problems: ask one for a root cause, then ask the other
to critique it. Agreement increases confidence; disagreement shows where to look.

## 9. Final rule

The AI is a very fast, very confident colleague that sometimes hallucinates. Trust
but verify: logs, hashes and primary sources win over any explanation.
