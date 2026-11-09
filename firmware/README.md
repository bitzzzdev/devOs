# Firmware workspace

Keep the original RMX3231 firmware archive unchanged. Place it in `firmware/original/` when local storage permits, and keep its source URL and SHA-256 in the inventory.

Extract only after the archive identity and format have been checked. Put extracted files in `firmware/extracted/` and inventories in `firmware/inventory/`. Do not use RMX3235, RMX2185, or other device variants here.

Current target: the user confirmed the phone ran RMX3231 A.119. The matching `RMX3231_11.A.119_202310110952.zip` was downloaded from Realme's `rms01.realme.net` host and passed ZIP CRC validation. The workspace filesystem has less free space than the archive size, so the original ZIP and derived 5 GiB `super.img` are currently under `/tmp/DEVos-firmware/`; they are not tracked by Git. The PAC working copy was reshaped into `super.img` to fit temporary storage. Download provenance, package hashes, extraction details, and the full PAC table are in `firmware/inventory/stage-1-2.md` and `firmware/inventory/pac-partitions.tsv`.

Regenerate the PAC table directly from the original ZIP without first writing the 6.3 GB PAC member:

```sh
python3 scripts/inspect_pac.py \
  /tmp/DEVos-firmware/RMX3231_11.A.119_202310110952.zip \
  --member cp_sign/SHARKL3_R11/RMX3231-user-native_SHARKL3_R11.pac
```

Pass `--extract-id BOOT` or another PAC partition ID to extract only that image into the ignored `firmware/extracted/pac/` directory. This parser records PAC CRC fields but does not recompute the PAC-internal CRC. The original ZIP CRC check remains a separate step.
