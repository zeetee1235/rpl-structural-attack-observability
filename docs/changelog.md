# Changelog

## [Unreleased] - 2026-02-04

### Fixed
- **ATTACK_RATE Parameter Application**: Fixed critical issue where ATTACK_RATE was not being properly applied to firmware during compilation
  - Problem: ATTACK_RATE showed 0.00 in logs despite being configured (e.g., 0.6)
  - Root cause: Environment variables from Python runner weren't propagating to Cooja's make command
  - Solution: Implemented pre-build firmware strategy in `scripts/run_cooja_headless.py`
    - Firmware is now built with explicit parameters before Cooja starts
    - Clean + make with `ATTACKER_ID=X ATTACK_RATE=Y ROOT_ID=Z`
    - Ensures compile-time constants are baked into binary
  - Verification: ATTACK_RATE=0.6 → actual drop rate 59.1% (statistically matches expected)

### Added
- **Test Scripts**:
  - `scripts/test_firmware_build.sh` - Test firmware compilation with different ATTACK_RATE values
  - `scripts/test_attack_rate.sh` - End-to-end simulation test with attack validation
  
- **Monitoring Scripts**:
  - `scripts/monitor_simulation.sh` - Real-time monitoring of running simulations
  - `scripts/monitor_simulation.py` - Python-based simulation monitor with enhanced features

- **Documentation**:
  - `docs/attack_rate_guide.md` - Comprehensive troubleshooting guide for ATTACK_RATE issues
  - `docs/setup_guide.md` - Detailed setup and usage instructions
  - `docs/changelog.md` - This changelog

- **Scenarios**:
  - `simulations/scenarios/scenario_b_high_exposure_20.csc` - 20-node high exposure scenario

### Changed
- Simplified all .csc scenario files to use basic make commands
- Pre-build strategy handles parameter passing in Python layer
- Updated `.gitignore` to exclude build artifacts (build/, .deps/, obj/)
- Updated README.md with recent changes section
- Enhanced firmware directory path resolution to support both standalone and simulation-relative paths

### Updated
- `contiki-ng-brpl` submodule with BRPL queue management and attack parameter support
  - Added BRPL queue implementation (brpl-queue.c/h)
  - Added RPL-BRPL integration (rpl-brpl.c)
  - Updated rpl-conf.h with BRPL configuration macros
  - Modified rpl-dag.c for BRPL queue operations

## [Initial Release] - 2026-02-03

### Added
- Initial project structure with analysis modules
- Cooja simulation infrastructure
- Basic RPL topology scenarios
- Log parsing utilities
- CLI analysis tool
