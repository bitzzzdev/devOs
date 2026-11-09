# Third-party license notices

The PolyForm Noncommercial license in `LICENSE` applies only to original
DEVos-authored source code. Third-party software and firmware remain under
their own terms.

## Realme SC9863A kernel source

`kernel/realme/sc9863a` is a Git submodule pointing to Realme's public
Android R kernel source. Its license is GPL-2.0 as stated in the submodule's
`COPYING` file. The repository's noncommercial license does not apply to this
submodule or change the rights granted by its GPL license.

## BusyBox

The local initramfs builder downloads Debian's ARM64 `busybox-static`
package. The binary and generated initramfs are excluded from Git. BusyBox is
GPL-2.0-only; see [the dependency notes](rootfs/DEPENDENCIES.md) for the
package version, source record, and distribution obligations.

## Realme firmware

The stock A.119 ZIP and extracted proprietary files are not included in this
repository. Their local inventory is in `firmware/inventory/`. No permission
to redistribute these files has been established.
