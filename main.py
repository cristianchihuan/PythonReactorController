import os
import sys
import logging
import tkinter as tk
from config.logging_config import setup_logging
from gui.config_gui import ConfigurationGui
from gui.controller_gui import ControllerGui
from devices.mfc_connection import MFCConnection
from devices.watlow_connection import WatlowConnection
from devices.dosing_valve import DosingValve
from devices.ni_temperature import NITemperatureConnection
from config.settings import log_file

def main():
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Open log file with UTF-8 encoding and write header
    open(log_file, "w", encoding='utf-8').write("Timestamp, b , Line# , Message, Value, Command, Signal_Speed, Channel, SP_Error, raw_response\n")
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s,%(lineno)d, %(message)s",
        handlers=[
            logging.FileHandler(log_file)  # Log to file
        ]
    )
    
    # Launch configuration GUI
    root = tk.Tk()
    config_gui = ConfigurationGui(root)
    root.mainloop()
    
    # Get configuration after GUI is closed
    config = config_gui.get_configuration()
    print("Configuration loaded:", config)

    # Convert string boolean values to actual booleans
    def str_to_bool(value):
        if isinstance(value, str):
            return value.lower() == 'true'
        return bool(value)
    
    # Convert configuration values
    config['Have8ComPorts'] = str_to_bool(config.get('Have8ComPorts', False))
    config['HaveWatlow'] = str_to_bool(config.get('HaveWatlow', False))
    config['HaveNITemperature'] = str_to_bool(config.get('HaveNITemperature', False))
    config['HaveDosing'] = str_to_bool(config.get('HaveDosing', False))
    
    # Initialize devices based on configuration
    devices = {}
    
    # Get MFC names from configuration
    mfc_names = config['MFCNames']
    mfc1_names = mfc_names[:4]  # First 4 names for MFC1
    mfc2_names = mfc_names[4:]  # Last 4 names for MFC2
    
    # Initialize MFC1 (always required)
    mfc1 = MFCConnection(port=config.get('DefaultMFC1ComPort'))
    devices['brooks1'] = mfc1
    
    # Initialize MFC2 only if Have8ComPorts is True
    if config['Have8ComPorts']:
        mfc2 = MFCConnection(port=config.get('DefaultMFC2ComPort'))
        devices['brooks2'] = mfc2
    else:
        devices['brooks2'] = None
    
    # Initialize Watlow only if HaveWatlow is True
    if config['HaveWatlow']:
        watlow = WatlowConnection(port=config.get('DefaultWatlowComPort'))
        devices['wt'] = watlow
    else:
        devices['wt'] = None
    
    # Initialize NI Temperature only if HaveNITemperature is True
    if config['HaveNITemperature']:
        ni_temp = NITemperatureConnection(device_name=config.get('DefaultNIComPort'))
        devices['ni'] = ni_temp
    else:
        devices['ni'] = None
    
    # Initialize Dosing Valve only if HaveDosing is True
    if config['HaveDosing']:
        dosing_valve = DosingValve(port=config.get('DefaultViciComPort'))
        devices['va'] = dosing_valve
    else:
        devices['va'] = None
    
    # Launch controller GUI
    controller_root = tk.Tk()
    controller_gui = ControllerGui(controller_root, config, devices, mfc_names)
    controller_root.mainloop()

if __name__ == "__main__":
    main() 