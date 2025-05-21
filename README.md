# Reactor Controller

A Python-based control system for managing a reactor setup with multiple mass flow controllers (MFCs), temperature control, and dosing valve control.

## Version Information
- Current Version: V5.1.4 (Refactored)
- Previous Versions:
  - V5.1.3 (Pre-refactoring)
  - V5.1.2 (Pre-refactoring)

## Features

- Configuration GUI for setting up device connections
- Real-time monitoring and control of:
  - Multiple mass flow controllers (MFCs)
  - Temperature control via Watlow controller
  - Temperature monitoring via NI DAQ
  - Dosing valve control via NI DAQ
- Real-time trend plotting
- Comprehensive logging system

## Requirements

- Python 3.7 or higher
- NI-DAQmx driver installed
- Serial ports for MFC and Watlow controllers
- Required Python packages (see requirements.txt)
- PyInstaller (for compilation)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd ReactorController
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Compilation

To create a standalone executable, use the following command:
```bash
python -m PyInstaller --onefile --collect-all nidaqmx --icon=images/icon.ico --name ReactorControl main.py
```

This will create a single executable file named `ReactorControl.exe` in the `dist` directory.

## Usage

1. Run the main script:
```bash
python main.py
```

2. Configure your devices in the configuration GUI:
   - Set COM ports for MFC and Watlow controllers
   - Set NI device name and channels
   - Enable/disable MFCs as needed

3. Use the controller GUI to:
   - Monitor and control MFC flow rates
   - Monitor and control temperature
   - Monitor and control dosing valve
   - View real-time trends

## Directory Structure

```
ReactorController/
├── config/
│   └── settings.py
├── devices/
│   ├── mfc_connection.py
│   ├── watlow_connection.py
│   ├── ni_temperature.py
│   └── dosing_valve.py
├── gui/
│   ├── config_gui.py
│   └── controller_gui.py
├── utils/
│   └── logging_config.py
├── images/
│   └── icon.ico
├── main.py
├── requirements.txt
└── README.md
```

## Logging

Logs are stored in the `logs` directory with timestamps. The logging system captures:
- Device connections and disconnections
- Setpoint changes
- Errors and exceptions
- Communication timing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

The project was performed using funds from Dr. Karim research. All intelectual property
belongs to Dr. Karim