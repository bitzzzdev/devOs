# Kernel source

`realme/sc9863a` is a Git submodule pointing to Realme's public C11 2021 and Narzo 50i Android R kernel source. It is pinned at commit `654351b0286746330f4a9ca958b2685e6485ec8d`, published on 2022-06-30.

The source reports Linux 4.14.193 and includes the RMX3231 board overlay. It is licensed under the terms in its `COPYING` file. Keep the upstream license and source history intact.

The generic `sprd_sharkl3_defconfig` enables ARM64, initramfs support, compatibility syscalls, ext4, F2FS, and the SC9863A clock driver. The community Lineage tree refers to `RMX3231_defconfig`, but that config is absent from the Realme kernel source. Do not use that name as a kernel build target. The A.119 kernel reports version `4.14.193+-ab453` and embeds IKCONFIG; its extracted config enables initramfs, proc, sysfs, tmpfs, and usermode helpers but disables devtmpfs. Kernel rebuild tooling and a bootloader-safe image test remain pending.

Initialize source after cloning DEVos with:

```sh
git submodule update --init --recursive
```

The current checkout pins this source as a submodule. Initialize it with the command above after cloning the DEVos repository.

## Optional upstream tool environment

These variables are used only by optional utilities in the kernel source.
They are not required by the DEVos initramfs or boot-image build.

| Variable | Upstream use |
| --- | --- |
| `LOG_FILE` | Selects output files in the `pm-graph` suspend and boot analysis tools when run by test scripts. |
| `PERF_EXEC_PATH` | Adds the perf Python helper library to the search path for optional perf scripts. |
| `READELF` | Overrides the `readelf` executable used by the IA-64 unwind checker. |
| `SPHINX_CONF` | Loads an additional Sphinx configuration while building kernel documentation. |
| `SUDO_GID`, `SUDO_UID` | Restore output-file ownership in the optional Intel pstate tracer when invoked through sudo. |
| `SUDO_USER`, `USER` | Identify the invoking/root user in optional `pm-graph` analysis utilities. |

`AVB_INVOCATION_LOGFILE` is separately recognized by the downloaded AOSP
`avbtool.py` and appends its command invocations when set. The DEVos builder
does not set it; see [third-party notices](../THIRD_PARTY_NOTICES.md).
