# Boot work

The device-specific Android tree identifies a v2 boot image, an ARM64 kernel, and a separate DTBO image. DEVos is expected to use a minimal Linux initramfs with the stock kernel first, then a rebuilt kernel after configuration and boot compatibility are established.

This is a design direction, not a verified boot-image recipe. The A.119 boot image has not yet been extracted. The phone is already boot-looping, so no boot image will be flashed as part of source analysis.
