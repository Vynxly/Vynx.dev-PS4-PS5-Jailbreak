# Third-party notices

This component preserves the Vynx frontend and combines it with selected code and pinned runtime artifacts from the PS5 homebrew ecosystem. Project names below are credits and provenance, not Vynx branding.

## Vynx jailbreak frontend

- Source: the parent Vynx.dev jailbreak host in this repository.
- Copied into: `frontend/vynx/`.
- License: GNU Affero General Public License v3 (`LICENSE`).
- Vynx-specific changes: automatic PS5 handoff, expanded firmware display, offline-stable Relapse offset URLs, and the bundled compatibility runner.

## ps5-webkit-autoloader

- Source: `https://github.com/itsPLK/ps5-webkit-autoloader`
- Pinned upstream commit: `f5e57c492a4a7b5ccd28ecddb43f8c325cf93aa2` (v0.5.1 main, 2026-09-30).
- License: GNU GPL v3; full text in `licenses/ps5-webkit-autoloader-GPL-3.0.txt`.
- Reused/adapted: native installer HTTP server, app installer, browser launcher, AppCache completeness design, file registry/compression, PC User Guide host, cache-recovery flow, v0.5.1 exploit routing, and build layout.
- Changed: all Vynx-facing names and IDs, title ID, app metadata, icon pipeline, visible UI, versioned Vynx frontend path, automatic compatibility selection, nested route generation, output names, and runtime update behavior.

## Relapse

- Source: `https://github.com/ntfargo/Relapse-Exploit`
- Pinned commit: `d8e6896b5cb33b04f1e038a5d698d3d4aee5947c`.
- License: MIT; full text in `licenses/Relapse-MIT.txt`.
- The Vynx copy retains the current Vynx styling and uses the v0.5.1 offline/autoload integration: stable offset URLs, shared localhost-only elfldr/kexp, and `?autoload=payload.elf` support.

## slopkit / Poops

- Source: `https://github.com/itsPLK/slopkit` (upstream credits Egy, Sonic, Yenyen, Zeco, Gezine, Echostretch, Ufm42, TheFloW, John Tornblom, Flatz, Idlesauce, and PS5 R&D Discord).
- Pinned commit: `e69a21762f8d12479443502ce19ea4a575295c48`.
- Reused through the v0.5.1 autoload patch for supported 7.00–12.00 firmware and the Poops-only 9.05/11.40 cases.
- The pinned tree does not contain a standalone license file; its original credits are preserved in the vendored files and here.

## umtx2

- Source: `https://github.com/idlesauce/umtx2`
- Pinned commit: `a080beb74d9e4bc34f3563798b716bd86b2d6ee0`.
- License notice: `licenses/umtx2-LICENSE.txt`.
- Used for supported PS5 firmware 1.00–5.50.

## Runtime payloads

- `ps5-autoload/shared/elfldr-ps5.elf`: itsPLK ps5-elfldr `v0.26-bb1e117`, SHA-256 `fa3f0c2b778318000982ada05c01bde70ac875c85e4be6fcc9b5ba836f6d1c3c`; GPL v3 text in `licenses/ps5-elfldr-GPL-3.0.txt`.
- `ps5-autoload/shared/kexp-ps5.bin`: itsPLK ps5-kexp `v0.8-24cf6e5`, SHA-256 `4e29cb74ffc1771b16e59d4998517aea32ecded651f814b71dc7ee50abff089f`.
- `ps5-autoload/payloads/payload.elf`: ps5-unified-autoloader `v0.1.5-915a65e`, SHA-256 `c8e36ea06cfd37c5fad356ff9fcd09d3e62065d88170b5119ce8f1eeb3efacac`; GPL v3 text in `licenses/ps5-unified-autoloader-GPL-3.0.txt`.

## Other retained credits

- John Törnblom / ps5-payload-dev: PS5 payload SDK and original app-install/elfldr work.
- Mark Adler: `puff.c` inflate implementation vendored in `src/inflate.c`.
- All upstream exploit and payload credits embedded in the original README/license/source files remain applicable.
