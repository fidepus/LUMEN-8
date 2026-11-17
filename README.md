# LUMEN-8

**Lightroom Utility for Manual Editing and Navigation: 8 Controls**

LUMEN-8 is an open-source, DIY USB hardware controller for adjusting image-development parameters in Adobe Lightroom. It combines eight dedicated parameter buttons, a rotary encoder and a small OLED status display in a compact, 3D-printable enclosure.

The project is currently an active prototype. The Pro Micro firmware, OLED interface, rotary encoder and macOS serial bridge have been brought up on real hardware. The eight-button control panel and final enclosure are still being assembled and tested.

## Project status

| Component | Status |
| --- | --- |
| Arduino Pro Micro firmware | Working prototype |
| OLED display (SH1106, 128×64) | Tested |
| EC11 rotary encoder | Tested |
| macOS serial bridge | Connects successfully |
| Lightroom parameter control | API endpoints tested; end-to-end hardware workflow still needs validation |
| Eight-button panel | In assembly |
| Enclosure | In development |

Expect changes to the hardware, firmware protocol and configuration while the prototype evolves.

## Features

- Eight configurable Lightroom parameters
- Dedicated buttons to select the active parameter
- Rotary encoder for incremental adjustments
- OLED display showing the parameter grid and active selection
- USB serial communication with a Python bridge on macOS
- Central JSON configuration with a provisioning script that generates the firmware's compile-time configuration

## Current parameter layout

| Button | Parameter | Lightroom API property | Default step |
| --- | --- | --- | ---: |
| D7 | Exposure | `Exposure2012` | 0.05 EV |
| D8 | Contrast | `Contrast2012` | 1 |
| D9 | Highlights | `Highlights2012` | 1 |
| D10 | Shadows | `Shadows2012` | 1 |
| D14 | Whites | `Whites2012` | 1 |
| D15 | Blacks | `Blacks2012` | 1 |
| D16 | Temperature | `Temperature` | 50 |
| A0 | Saturation | `Saturation` | 1 |

These are the default values from `config/default.json`. A local `config/user.json` can override them. The actual working configuration may differ.

## Hardware

### Main components

- Arduino Pro Micro compatible board, ATmega32U4, 5 V / 16 MHz, USB-C
- 1.3-inch 128×64 I²C OLED module (SH1106)
- EC11 rotary encoder with push switch
- Eight Cherry MX-compatible momentary switches
- Perfboard, wire, headers and suitable enclosure hardware
- Custom 3D-printed enclosure (design files will be added as they are finalized)

### Pin assignment

| Function | Pro Micro pin |
| --- | --- |
| OLED SDA | D2 |
| OLED SCL | D3 |
| Encoder A | D4 |
| Encoder B | D5 |
| Encoder push | D6 |
| Exposure button | D7 |
| Contrast button | D8 |
| Highlights button | D9 |
| Shadows button | D10 |
| Whites button | D14 |
| Blacks button | D15 |
| Temperature button | D16 |
| Saturation button | A0 |

Buttons and encoder switch are wired between their assigned input pin and GND. Firmware uses the internal pull-up resistors.

**Electrical note:** Pro Micro clones and OLED modules vary. Verify the OLED module's supply-voltage requirements and the voltage of its I²C pull-ups before connecting it. Do not assume that an OLED advertised as accepting 5 V has 5 V-tolerant I²C pins. Use appropriate level shifting where required.

## Software architecture

```text
LUMEN-8/
├── config/
│   ├── default.json
│   └── user.json              # local file; do not commit
├── firmware/
│   ├── platformio.ini
│   └── src/
│       ├── generated_config.h  # generated locally; not committed
│       ├── main.cpp
│       ├── input.cpp
│       ├── input.h
│       ├── display.cpp
│       ├── display.h
│       ├── protocol.cpp
│       └── protocol.h
├── mac/
│   ├── bridge.py
│   ├── device_discovery.py
│   ├── config.py
│   ├── lightroom.py
│   └── logger.py
├── scripts/
│   ├── test_lightroom_api.sh
│   └── provision.py
├── .gitignore
├── README.md
└── requirements.txt
```

The exact contents may change as development continues.

## Requirements

- macOS
- Python 3
- PlatformIO (for firmware builds and uploads)
- Arduino Pro Micro compatible board
- U8g2 library (managed by PlatformIO)
- Python dependency: `pyserial`
- Adobe Lightroom
- A running instance of [lightroom-controller](https://github.com/electerious/lightroom-controller)

LUMEN-8 communicates with the macOS bridge over USB serial. The bridge forwards control events to the local `lightroom-controller` API, expected at `http://localhost:3000` by default.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/fidepus/LUMEN-8.git
cd LUMEN-8
```

### 2. Set up the Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure the controller

Copy the default configuration to a local user configuration if you want to override settings:

```bash
cp config/default.json config/user.json
```

Edit `config/user.json` as needed. This file is intentionally excluded from version control.

### 4. Generate the firmware configuration

```bash
python scripts/provision.py
```

The provisioning script reads the default and user configuration and generates `firmware/src/generated_config.h`. This generated file is intentionally excluded from Git because it can contain local configuration choices. Run provisioning before the first firmware build and again after changing parameter or hardware configuration, then rebuild and flash the firmware.

### 5. Build and upload firmware

With PlatformIO installed:

```bash
cd firmware
pio run -e promicro
pio run -e promicro -t upload --upload-port /dev/cu.usbmodemXXXX
```

The `--auto` mode scans USB serial devices and identifies LUMEN-8 through its firmware response. It does not depend on a fixed `/dev/cu.usbmodem...` name or a particular Arduino VID/PID. For diagnostics, a fixed port can still be selected with `--serial /dev/cu.usbmodemXXXX`.

### 6. Start the macOS bridge

From the repository root:

```bash
source .venv/bin/activate
python mac/bridge.py --auto
```

Make sure Adobe Lightroom and `lightroom-controller` are running and that the API URL in your configuration is correct.

## Configuration

The shared defaults live in `config/default.json`. Local overrides belong in `config/user.json`, which must not be committed.

Parameter configuration includes:

- `label` and `short_label`: names shown in the OLED interface
- `api_name`: property name understood by the Lightroom controller
- `step`: adjustment amount per encoder movement
- `enabled`: whether the parameter is active

The firmware uses generated, compile-time configuration rather than parsing JSON at runtime. This keeps memory use on the ATmega32U4 lower and makes the firmware build deterministic.

## Development notes

- The firmware currently uses the U8g2 library with an SH1106 display driver.
- USB serial runs at 115200 baud.
- The bridge identifies the device with a small ASCII request/response (`LUMEN8:IDENTIFY?` / `LUMEN8:HELLO:1:<firmware-version>`). This is separate from configuration provisioning; no settings are transferred at runtime.
- Automatic discovery probes USB serial interfaces regardless of their specific VID/PID values. Optional VID/PID/serial-number filters can be set in `config/user.json`; a valid LUMEN-8 protocol response is always required.
- The bridge keeps DTR and RTS inactive while probing, to avoid triggering the reset behavior used by some Arduino boards.
- Current-value readback from Lightroom is not implemented.
- The encoder push switch currently reports a press event; no reset action is assigned yet.

## Roadmap

- [x] Implement versioned protocol-based USB identification and automatic re-discovery after connection loss\n- [ ] Verify discovery with the physical Pro Micro and at least one alternative USB-capable Arduino
- [ ] Package the bridge as a macOS `launchd` LaunchAgent: start at login, restart after failures, manage logs, and provide install/uninstall scripts
- [ ] Complete the eight-button perfboard assembly
- [ ] Validate all eight buttons and encoder adjustments end to end in Lightroom
- [ ] Finalize the enclosure and add printable CAD/STL files
- [ ] Add assembly photographs and wiring diagrams
- [ ] Document installation and troubleshooting in more detail
- [ ] Consider current-value feedback and additional interaction modes

## Tests

Run the host-side discovery protocol tests from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

These tests cover response parsing, protocol-version rejection, optional USB filters and probe retries. Physical USB reconnection still needs validation with the target hardware.\n\n## Third-party software

LUMEN-8 uses the [lightroom-controller](https://github.com/electerious/lightroom-controller) project by electerious. That project is distributed under the MIT License. See its repository for its license and notices.

The firmware depends on [U8g2](https://github.com/olikraus/u8g2), which is distributed under its own license. See the upstream project for details.

## License

LUMEN-8 is released under the MIT License. See [LICENSE](LICENSE).

Third-party components remain subject to their respective licenses.
