# RPL Node Firmware for Cooja

This directory contains the firmware used by all motes in Cooja simulations.
Roles are determined by node ID (root, attacker, sender).

## Files

- `rpl-node.c`: RPL-lite application with selective forwarding, parent logging, and OBS logs.
- `Makefile`: build configuration with runtime parameters.

## Build flags (Makefile variables)

These can be overridden at build time or via environment variables passed to Cooja.

- `ATTACKER_ID` (default 6)
- `ATTACK_RATE` (default 0.0)
- `ROOT_ID` (default 1)
- `SEND_INTERVAL` seconds (default 30)
- `SEND_JITTER` seconds (default 5)
- `DATA_PORT` (default 3000)
- `ATTACK_STATS_PERIOD` seconds (default 300)
- `BRPL=1` to enable BRPL (adds Queue Option and BRPL OF)

## Compiling

```bash
make TARGET=cooja
```

Example with overrides:

```bash
make TARGET=cooja ATTACKER_ID=6 ATTACK_RATE=0.4 ROOT_ID=1
make TARGET=cooja BRPL=1
```

## Log format

The firmware emits `OBS` logs following `docs/logging_spec.md`.

Notes:
- Parent changes are logged as `OBS ... ev=PARENT parent=...`
- Root logs `ROOT_RX` and `DELAY`
- Attacker logs `DATA_RX`, `DATA_FWD`, `DATA_DROP`, and periodic `ATTACK_STATS`

## Routing protocol

This firmware targets RPL classic by default. If you plan to use BRPL,
provide the BRPL routing driver and update the Makefile accordingly.
