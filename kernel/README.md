# Kernel source

`realme/sc9863a` is a Git submodule pointing to Realme's public C11 2021 and Narzo 50i Android R kernel source. It is pinned at commit `654351b0286746330f4a9ca958b2685e6485ec8d`, published on 2022-06-30.

The source reports Linux 4.14.193 and includes the RMX3231 board overlay. It is licensed under the terms in its `COPYING` file. Keep the upstream license and source history intact.

The generic `sprd_sharkl3_defconfig` enables ARM64, initramfs support, compatibility syscalls, ext4, F2FS, and the SC9863A clock driver. The community Lineage tree refers to `RMX3231_defconfig`, but that config is absent from the Realme kernel source. Do not use that name as a kernel build target. The A.119 kernel reports version `4.14.193+-ab453` and embeds IKCONFIG; its extracted config enables initramfs, proc, sysfs, tmpfs, and usermode helpers but disables devtmpfs. Kernel rebuild tooling and a bootloader-safe image test remain pending.

Initialize source after cloning DEVos with:

```sh
git submodule update --init --recursive
```

The current checkout pins this source as a submodule. Initialize it with the command above after cloning the DEVos repository.
