# Brainflow Script CHOP for TouchDesigner

## Introduction

This project introduces a real-time EEG data processing pipeline integrated within TouchDesigner via a Script CHOP. It leverages the BrainFlow SDK for device communication, and incorporates signal filtering, re-sampling, FFT transformation, and OSC output functionalities. The core motivation is to allow artists, researchers, and real-time system designers to integrate brain-computer interface (BCI) input directly into generative audiovisual environments without relying on external bridging software.

## Motivation

TouchDesigner is widely used for real-time visuals and interactive systems. However, native support for EEG integration is limited. This script was developed to bridge that gap, offering a robust, flexible, and extensible framework for bringing real-time biosignals into audiovisual workflows. The implementation also provides an accessible entry point for research-grade EEG integration within live creative environments.

## Justification

Many existing EEG-to-creative-system bridges require multiple applications, extensive configuration, or custom networking stacks. By embedding the entire data acquisition, filtering, and forwarding logic within TouchDesigner, this tool simplifies the development process while remaining highly configurable. This script enables low-latency integration with systems such as Wekinator, Max/MSP, Unreal, and Unity via OSC.

## Prototype Description

This project makes extensive use of the BrainFlow SDK for multi-device EEG data acquisition and control. BrainFlow provides a unified API for interacting with a wide range of biosignal hardware, enabling consistent access to streaming, configuration, and metadata across platforms. For more information, visit [https://brainflow.org](https://brainflow.org).

The Script CHOP offers the following key functionalities:
The Script CHOP offers the following key functionalities:

* EEG data acquisition via BrainFlow-compatible devices
* Channel selection and live streaming
* Optional Kalman filtering (fully parameterised)
* Optional FFT transformation
* Custom re-sampling rate
* OSC output of selected time and/or frequency domain data
* Live garbage collection and resource maintenance

Parameter pages include:

* **General Settings**: Device selection, serial port, re-sampling rate
* **Time Settings**: Update interval configuration
* **Filter Settings**: Kalman filter toggle and noise parameters
* **FFT Settings**: FFT toggle
* **OSC Settings**: Address, port, OSC message path, and channels to send

## Supported Devices

This script supports all EEG devices available through the BrainFlow API. The currently supported boards (as of latest BrainFlow release) include, but are not limited to:

* CYTON\_BOARD, CYTON\_DAISY\_BOARD, CYTON\_WIFI\_BOARD
* GANGLION\_BOARD, GANGLION\_WIFI\_BOARD
* MUSE\_2\_BOARD, MUSE\_S\_BOARD, MUSE\_2016\_BOARD
* BRAINBIT\_BOARD, BRAINBIT\_BLED\_BOARD
* NOTION\_1\_BOARD, NOTION\_2\_BOARD
* CROWN\_BOARD
* EMOTIBIT\_BOARD
* FREEEEG32\_BOARD, FREEEEG128\_BOARD
* GFORCE\_PRO\_BOARD, GFORCE\_DUAL\_BOARD
* GALEA\_BOARD, GALEA\_SERIAL\_BOARD, GALEA\_BOARD\_V4
* CALLIBRI\_EEG\_BOARD, CALLIBRI\_EMG\_BOARD, CALLIBRI\_ECG\_BOARD
* AVAVA\_V3\_BOARD
* ANT\_NEURO\_EE\_\* series (e.g. 211, 212, 223, 430, etc.)
* EXPLORE\_8\_CHAN\_BOARD, EXPLORE\_PLUS\_8\_CHAN\_BOARD, EXPLORE\_PLUS\_32\_CHAN\_BOARD
* STREAMING\_BOARD, PLAYBACK\_FILE\_BOARD, SYNTHETIC\_BOARD

The full list is populated dynamically in the UI from the BrainFlow enumeration.

## Tests

The system was tested using a 4-channel BrainBit device over Bluetooth. Functional validation included:

* Successful device connection and data acquisition
* Real-time Kalman filtering with dynamic parameters
* Re-sampling integrity (250Hz target rate)
* FFT accuracy across sample windows
* OSC communication with external software (Wekinator)
* Live parameter updates without requiring script reload

Limitations of testing:

* Only one device type (BrainBit) was tested
* Limited to four EEG channels
* No systematic validation with FFT-based downstream learning models

## Evaluation

The script performs reliably under moderate processing loads and achieves smooth real-time performance on standard consumer hardware (tested on macOS). Kalman filtering significantly improves signal stability. Resampling and FFT functionalities are accurate within numerical precision limits. OSC output is fast and compatible with common UDP-based systems.

However, CPU usage could increase when scaling to high-channel-count devices. The current implementation uses nested loops in Python for Kalman filtering, which may not scale efficiently. FFT results are unnormalised and might require post-processing depending on the target application.

## Future Tests and Design Directions

* Extend testing to devices with higher channel counts (e.g., OpenBCI, Muse S, ANT Neuro)
* Replace looped Kalman filter with a batched vectorised JIT implementation
* Implement OSC bundling for optimised transmission
* Add time synchronisation and timestamp output
* Improve user interface with device-specific channel labelling
* Add support for alternative protocols (e.g., WebSockets or Serial)

## README Elements

### Installation

1. Install dependencies via pip:

```bash
pip install brainflow scipy python-osc numba
```

2. Place the script inside a Script CHOP in TouchDesigner.
3. Enable the script by selecting your board and serial port.

### Dependencies

* brainflow
* scipy
* python-osc
* numba

1. Install dependencies via pip:

```bash
pip install brainflow scipy python-osc numba
```

2. Place the script inside a Script CHOP in TouchDesigner.
3. Enable the script by selecting your board and serial port.

### Requirements

* TouchDesigner (latest build)
* BrainFlow-compatible EEG device (tested with BrainBit only)
* Python 3 (64-bit, matching TouchDesigner Python environment)
	Python packages:

	brainflow

	scipy

	python-osc

	numba

This extension requires the BrainFlow Python package to be installed and accessible within TouchDesigner. It is strongly recommended to manage Python environments using TouchDesigner's built-in environment manager: [TD Python Environment Manager](https://derivative.ca/community-post/introducing-touchdesigner-python-environment-manager-tdpyenvmanager/72024)

* TouchDesigner (latest build)
* BrainFlow-compatible EEG device (tested with BrainBit only)
* Python 3 (64-bit, matching TouchDesigner Python environment)

### Limitations

* Only verified on BrainBit (4-channel EEG)
* Currently uses CPU-heavy loops for filtering
* Does not include visual diagnostics of EEG/FFT signals

### License

MIT License or custom license as applicable.

---

For professional or research usage, please verify stability with your specific EEG device before deployment.
