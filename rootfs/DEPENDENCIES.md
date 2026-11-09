# Rootfs dependency licenses

## BusyBox

The initial ARM64 initramfs includes Debian's `busybox-static` package,
version `1:1.37.0-6+b9`. The package copyright notice identifies BusyBox
under GNU GPL version 2 only. The builder downloads and verifies the
Debian package but does not modify the BusyBox executable.

The binary is kept in the ignored local cache and generated image. If DEVos
distributes an initramfs containing it, the distribution must include the
GPL-2.0 license notice and satisfy the corresponding source-code terms.
The Debian package record links to the source package and copyright notice:
[Debian Trixie BusyBox](https://packages.debian.org/trixie/busybox-static).

The DEVos-authored source files have a separate license in the repository's
`LICENSE`. That license does not replace BusyBox's GPL-2.0 terms.
