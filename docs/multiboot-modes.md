# DEVos Multi-Boot Architecture and Operational Modes

## Overview

The DEVos boot candidate implements a multi-boot selector during early kernel initialization. When flashed to the Realme C11 2021 (`RMX3231`) boot partition, the phone boots into the DEVos initramfs before any Android system partitions are touched.

The user can choose between four dedicated operating modes:

1. **Pocket VPS** (Headless Linux micro-server)
2. **Wi-Fi Router** (Access point, DHCP gateway, NAT routing)
3. **Dual Mode** (Pocket VPS + Wi-Fi Router combined)
4. **Regular Barebones** (Stock Android system, full phone functionality)

---

## Boot Mode Selector

### Boot Sequence and Timeout

When the kernel initializes device nodes via `mdev`, `rootfs/init` displays the multi-boot menu on the boot console (`/dev/console`):

```text
================================================================
                  DEVos Multi-Boot Selector
               Hardware: Realme C11 2021 (RMX3231)
================================================================
  [1] Pocket VPS          - Headless Linux server (SSH/RNDIS)
  [2] Wi-Fi Router        - AP hotspot, DHCP gateway, NAT routing
  [3] Dual Mode           - Pocket VPS + Wi-Fi Router combined
  [4] Regular Barebones   - Boot normal Android (Full phone/calls)
================================================================
```

A 5-second countdown runs by default. If no key is pressed, the system automatically launches the default mode specified in `/etc/devos.conf` (Mode 4: Regular Barebones).

### Selecting a Mode

Users can select a mode via:

- Console input: entering `1`, `2`, `3`, or `4` on the interactive terminal.
- Kernel command line: supplying `devos.mode=1`, `devos.mode=2`, `devos.mode=3`, or `devos.mode=4` in fastboot boot arguments (`fastboot boot boot.img --cmdline "devos.mode=1"`).
- Configuration file: changing `DEVOS_DEFAULT_MODE` in `/etc/devos.conf`.

---

## Mode 1: Pocket VPS (Headless Linux Micro-Server)

Pocket VPS transforms the phone into an ultra-low-power, battery-backed Linux micro-server.

### Network Configuration

| Parameter | Value |
| --- | --- |
| Subnet | `192.168.7.0/24` |
| Device IP | `192.168.7.2` |
| Host Gateway IP | `192.168.7.1` (assigned via DHCP) |
| Interface | USB Gadget Ethernet (RNDIS / CDC-Ethernet over USB-C) |

### Services

- Dropbear SSH daemon (or BusyBox shell server) listening on port 22.
- Built-in udhcpd DHCP server leasing `192.168.7.1` to any connected PC or laptop.
- Interactive root console on `/dev/console`.

---

## Mode 2: Wi-Fi Router (Access Point & Gateway NAT)

Wi-Fi Router mode turns the phone into a portable router and access point.

### Network Configuration

| Parameter | Value |
| --- | --- |
| Wireless Interface | `wlan0` / `ap0` |
| Gateway IP | `192.168.43.1` |
| Subnet Mask | `255.255.255.0` |
| DHCP Client Pool | `192.168.43.100` to `192.168.43.200` |
| DNS Server | `192.168.43.1` with upstream fallback `8.8.8.8` |

### Routing and Firewall

- IPv4 packet forwarding enabled via `/proc/sys/net/ipv4/ip_forward`.
- `iptables` NAT masquerade enabled for all forwarded client traffic.

---

## Mode 3: Dual Mode (Pocket VPS + Wi-Fi Router)

Dual mode activates both Pocket VPS and Wi-Fi Router services concurrently.

### Characteristics

- Users connected via Wi-Fi receive DHCP addresses in the `192.168.43.x` range and can reach the Linux server at `192.168.43.1:22`.
- A computer connected via USB receives `192.168.7.1` and accesses the server at `192.168.7.2:22`.
- Traffic between USB, Wi-Fi, and upstream cellular data is routed through the kernel firewall.

---

## Mode 4: Regular Barebones (Stock Android)

Mode 4 boots the phone into standard Android.

### Hardware Functionality

In this mode, the DEVos initramfs hands control over to the stock Android first-stage init binary. The stock Android operating system then mounts the logical partitions (`system`, `vendor`, `product`, `system_ext`) from dynamic partition storage (`super.img`).

All original device hardware functions normally:

- Camera: primary and front selfie cameras operate through the vendor camera HAL.
- Microphone and Audio: audio input, speaker, earpiece, and 3.5 mm jack operate via Unisoc audio HAL.
- Cellular Telephony: calling, SMS, and 4G LTE mobile data operate through Unisoc RIL and modem firmware.
- Wi-Fi and Bluetooth: standard Android networking stack operates with stock firmware.
- Touchscreen and Display: full surface compositor (SurfaceFlinger) and graphics drivers load.

### UPI and Banking Applications

Unified Payments Interface (UPI) applications (such as Google Pay, PhonePe, and Paytm) enforce security checks via Google Play Integrity and SafetyNet APIs.

Because DEVos only replaces the boot partition and leaves all dynamic system partitions on `super.img` completely untouched:

- Stock system binaries, vendor configurations, and application packages remain unmodified.
- If the bootloader is unlocked, basic integrity passes, but CTS profile match may depend on Play Integrity evaluation.
- The phone remains fully usable as a standard smartphone.
