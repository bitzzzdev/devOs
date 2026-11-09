# Contributing to DEVos

DEVos is an experimental native Linux port for the Realme C11 2021 (RMX3231). Contributions should keep the exact device variant and the separation between stock firmware analysis and DEVos build outputs clear.

## Before changing files

- Read the current project status in `README.md` and the hardware findings in `docs/`.
- Use RMX3231 A.119 as the comparison baseline unless a later user-confirmed package is added with its own inventory.
- Keep proprietary firmware, calibration data, NV data, and extracted vendor binaries out of Git. The repository ignores local firmware output for this reason.
- Never flash or erase partitions, format storage, or change the bootloader lock state as part of a contribution.

## Changes and review

- Keep scripts reproducible and make destructive actions opt-in and explicit.
- Record source URLs, versions, checksums, tool versions, and limitations for firmware research.
- Do not claim hardware support based only on another Realme or Unisoc device.
- Describe what was changed and what remains unverified in the pull request.
- Do not submit stock firmware or device-specific blobs unless their redistribution terms have been established.

The project license is not selected yet. Until then, do not assume that project code may be reused under a particular license.
