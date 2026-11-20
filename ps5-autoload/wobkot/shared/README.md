# Bundled Binaries

This directory contains pre-compiled binaries used by the loader for kernel payload execution and ELF loading:

* **`elfldr-ps5-v0.26.elf`**: PS5 ELF loader daemon running on port 9021.
  * Source: [ps5-payload-dev/elfldr](https://github.com/ps5-payload-dev/elfldr) (v0.26)
* **`kexp-v0.8-24cf6e5.bin`**: Kernel shellcode payload implementing pipe bootstrap and mapping the ELF loader.
  * Source: [itsPLK/ps5-kexp](https://github.com/itsPLK/ps5-kexp) (v0.8, commit `24cf6e5`)

These binaries are fetched and launched through `api.prefetchKexp()` and `api.launchKexp()` during the post-kernel-exploit phase.
