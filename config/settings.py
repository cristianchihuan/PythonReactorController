import os
from datetime import datetime
import time
import logging

# Default settings and configuration
SP_WRITE_DELAY = 0.3
TITTLE = "Universal Reactor V5.1.3"

# Default COM ports
DefaultMFC1ComPort = 'COM1'
DefaultMFC2ComPort = 'COM2'
DefaultWatlowComPort = 'COM3'
DefaultViciComPort = 'COM4'
DefaultNIComPort = 'COM5'

# Feature flags
Have8ComPorts = True
HaveWatlow = True
HaveNITemperature = True
HaveDosing = False

# MFC Labels
MFC1label = 'H2'
MFC2label = 'He'
MFC3label = 'O2'
MFC4label = 'C2H4'
MFC5label = 'Empty'
MFC6label = 'Empty'
MFC7label = 'C2H4'
MFC8label = 'Empty'

# MFC Channels
PVChannels = [b'01', b'03', b'05', b'07']
SPChannels = [b'2', b'4', b'6', b'8']

# Signal Types
SP_OUTPUT_PORT_SIGNAL_TYPES = {
    '0': 'Off',
    '1': '0-20 mA',
    '2': '4-20 mA',
    '3': '0-10 V',
    '4': '2-10 V',
    '5': '0-5 V',
    '6': '1-5 V',
}

# MFC Names list
MFCNames = [MFC1label, MFC2label, MFC3label, MFC4label]
if Have8ComPorts:
    MFCNames = MFCNames + [MFC5label, MFC6label, MFC7label, MFC8label]

# Log file settings
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "Glitch_log_{}.csv".format(time.strftime("%Y-%m-%d_%H-%M-%S")))

# Open log file with UTF-8 encoding
logging.getLogger('matplotlib').setLevel(logging.CRITICAL)
logging.getLogger('PIL').setLevel(logging.CRITICAL)
open(log_file, "w", encoding='utf-8').write("Timestamp, b , Line# , Message, Value, Command, Signal_Speed, Channel, SP_Error, raw_response\n") 