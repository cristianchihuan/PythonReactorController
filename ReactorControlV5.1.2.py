
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 23 17:30:55 2021
READ ME:
    before any of this will make any sense you will need to be a little familiar with the packages called, RS-232 communication protocal, and the 0254 unit.

@author: Coogan
Parts taken from https://www.youtube.com/watch?v=CdHDDBTD4QE

Youtube Video for NI USB-TC01 https://www.youtube.com/watch?v=NMMRbPvkzFs.
You need to install this free NI driver software https://nidaqmx-python.readthedocs.io/en/stable/

Change log
v2: Fixed bugs aded profile stuff
v3: Added option for 8 MFCS
v3.1 Added labels for things
v3.2 Add toggle for T controller
v4.1 Now with dosing pieces
v4.2 added logging and SP write delay
This is a copy from v4.2. I will add the Thermocuple Code to this one
Thermocouple added and added option to specify the channel for the NI device. Fixed bugs with Reactor template.04/14/2025 2:03 PM
v 4.3 Added option to specify the channel for the NI device. Fixed bugs with Reactor template.04/14/2025 2:03 PM
v 4.5 Optimized the code and added a few more comments. 04/16/2025 10:45 AM
v 5.1 Universal Code, Temperature Controller bug fixed. 
v 5.1.2 Added logger option on configuration page

"""
# at the very top of your script, before anything else
import sys
if sys.platform == "win32":
    import ctypes

    # fetch the stdin handle (-10) and current mode
    hStdin = ctypes.windll.kernel32.GetStdHandle(-10)
    mode   = ctypes.c_uint()
    ctypes.windll.kernel32.GetConsoleMode(hStdin, ctypes.byref(mode))

    # clear only the Quick Edit bit (0x40)
    ctypes.windll.kernel32.SetConsoleMode(hStdin, mode.value & ~0x40)
# Also install pyserial, serial, pandas, numpy, crcmod, openpyxl
#import nidaqmx.constants
import serial
import tkinter
import pandas
import numpy
import csv
import datetime
import struct
import crcmod
import binascii
import logging, os
import time
import nidaqmx 
from tkinter import filedialog, messagebox, ttk
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import random
# The following command needs to be executed to create a .exe file:
# pyinstaller --onefile --collect-all nidaqmx NewThermocoupleCode.py
# Create a directory for logs if it doesn't exist. AND creates a log file
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "Glitch_log_{}.csv".format(time.strftime("%Y-%m-%d_%H-%M-%S")))
open(log_file, "w").write("Timestamp, b , Line# , Message, Value, Command, Signal_Speed, Channel, SP_Error, raw_response\n")

''' Commented out for now, will add back in later
# Configure logging
Valid_entry = False
print("Please Select Logging configuration. \n Type Y to enable logging \n Type N to disable logging ")
while Valid_entry == False :
    Logging_Enabled = input()
    if Logging_Enabled == "Y":
        logging.basicConfig(
        level=logging.DEBUG,  # Log only CRITICAL messages
        format="%(asctime)s,%(lineno)d, %(message)s",
        handlers=[
            #logging.StreamHandler(),  # Log to console
            logging.FileHandler(log_file)  # Log to file
        ]
        )
        Valid_entry = True
    elif Logging_Enabled == "N":
        logging.basicConfig(
        level=logging.CRITICAL,  # Log only CRITICAL messages
        format="%(asctime)s,%(lineno)d, %(message)s",
        handlers=[
            #logging.StreamHandler(),  # Log to console
            logging.FileHandler(log_file)  # Log to file
        ]
        )
        Valid_entry = True
    else:
        print("Please Select a Valid entry Y or N")
'''

##Begin Settings
SP_WRITE_DELAY = 0.2
TITTLE = "Universal Reactor V5.1.2"

DefaultMFC1ComPort='COM5'
DefaultMFC2ComPort='COM6'
DefaultWatlowComPort='COM8'
DefaultViciComPort='COM7'
DefaultNIComPort='Dev1'

Have8ComPorts = True
HaveWatlow= True
HaveNITemperature = True
HaveDosing=False

MFC1label='H2'
MFC2label='He'
MFC3label='O2'
MFC4label='C2H4'

MFC5label='Empty'
MFC6label='Empty'
MFC7label='C2H4'
MFC8label='Empty'
##End Setttings

PVChannels=[b'01',b'03',b'05',b'07']
SPChannels=[b'2',b'4',b'6',b'8']
crc = crcmod.mkCrcFun(0b10001000000100001)

MFCNames=[MFC1label, MFC2label, MFC3label, MFC4label]
if Have8ComPorts:
    MFCNames=MFCNames + [MFC5label, MFC6label, MFC7label, MFC8label]        

# Set the SP write delay
def Set_SP_Write_Delay(value):
    global SP_WRITE_DELAY
    SP_WRITE_DELAY = value


#Mi had a good manual for this one as well
class PressureTransducer:
    def __init__(self, port='COM4', baudrate=9600, bytesize=serial.SEVENBITS, parity=serial.PARITY_ODD, stopbits=serial.STOPBITS_ONE, timeout=0.3):
        self.port=port
        self.baudrate=baudrate
        self.bytesize=bytesize
        self.parity=parity
        self.stopbits=stopbits
        self.timeout=timeout
        self.ser=[]     

    def Connect(self,port):
        try:
            print(port)
            self.ser = serial.Serial(port, self.baudrate, self.bytesize, self.parity, self.stopbits, self.timeout)
            self.ser.isOpen()
            print("Pressure Port Opened")
        except:
            print("ERROR, Pressure port did not open")
            self.ser=[]

    def CloseConnection(self):
        try:
            self.ser.close()
            print("Pressure Port Closed")
        except:
            print("ERROR, Pressure port did not close")
            self.ser=[]

    def ReadPressure(self):
        try:
            #self.ser.write(b'?AV1\r')
            #self.ser.write(b'?ID\r')
            command='?AV\r'
            print(command)
            print(command.encode('utf-8'))
            
            self.ser.write(b'?ID\r')
          
            #self.write(command.encode('utf-8'))
            
            printed=self.ser.readline()
            print('test')
            #Pressure=printed.decode('ascii')
            
            Pressure=printed.decode('utf-8')
            
            
            print(Pressure)
            return Pressure
        except:
            print("ERROR") 



        #ser.write((data_in).encode('utf-8'))
#See the manual for some hints on this one
class DosingValve:
    def __init__(self, port='COM4', baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.3):
        self.port=port
        self.baudrate=baudrate
        self.bytesize=bytesize
        self.parity=parity
        self.stopbits=stopbits
        self.timeout=timeout
        self.ser=[]     
    
    def Connect(self,port):
        for i in range(3):
            try:
                print(port)
                self.ser = serial.Serial(port, self.baudrate, self.bytesize, self.parity, self.stopbits, self.timeout)
                time.sleep(0.8)
                if not self.ser.isOpen():
                    print("ERROR, Dosing valve port did not open, Reatemting")
                    logging.critical("ERROR, Dosing valve port did not open, Reattempting", i)
                    self.ser.open()
                print("Dosing Valve Port Opened")
                return
            except Exception as e:
                print("ERROR, Dosing valve port did not open. ", e)
                logging.critical("ERROR, Dosing valve port did not open", e)
                self.ser=[]
        """""
        try:
            print(port)
            self.ser = serial.Serial(port, self.baudrate, self.bytesize, self.parity, self.stopbits, self.timeout)
            time.sleep(0.1)
            if not self.ser.isOpen():
                print("ERROR, 6-Way valve port did not open, Reatemting")
                logging.critical("ERROR, 6-way valve port did not open, Reattempting")
                self.ser.open()
            print("6-Way Valve Port Opened")
        except Exception as e:
            print("ERROR, 6-way valve port did not open. ", e)
            logging.critical("ERROR, 6-way valve port did not open", e)
            self.ser=[]
        """""
    def CloseConnection(self):
        try:
            self.ser.close()
            time.sleep(0.1)
            print("6-Way Valve Port Closed")
        except Exception as e:
            print("ERROR, 6-Way valve port did not close")
            logging.critical("ERROR, 6-Way valve port did not close", e)
            self.ser=[]
            
    def Test6portConnection(self):
        try:
            if self.ser.isOpen():
                print("6-Way Valve serial port is open")
            else:
                print("ERROR, 6-Way valve port is not open")
                self.ser=[]
        except:
            print("ERROR, Unknown, probably no connection")

    def ReadState(self):
        try:
            self.ser.write(b'cp\r')
            printed=self.ser.readline()
            position=printed.decode('ascii')
            print(position)
            return position
        except Exception as e:
            print("ERROR in reading state", e)         

    def SetToStateA(self):
        try: 
            self.ser.write(b'go1\r')
            self.ser.write(b'cp\r')
            printed=self.ser.readline()
            print(printed.decode('ascii'))
        except Exception as e:
            print("ERROR in SetToStateA", e)         

    def SetToStateB(self):
        try: 
            self.ser.write(b'go2\r')
            self.ser.write(b'cp\r')
            printed=self.ser.readline()
            print(printed.decode('ascii'))
        except Exception as e:
            print("ERROR in SetToStateB", e)
#See information on the 0254 unit for the read/write of the serial port. This should be in the shared drive
class MFCConnection:
    def __init__(self, port='COM3', baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=2):
        self.port=port
        self.baudrate=baudrate
        self.bytesize=bytesize
        self.parity=parity
        self.stopbits=stopbits
        self.timeout=timeout
        self.ser=[]     
        
    def Connect(self,port):
        for i in range(3):
            try:
                #print(port)
                self.ser = serial.Serial(port, self.baudrate, self.bytesize, self.parity, self.stopbits, self.timeout)
                time.sleep(0.1)
                self.ser.isOpen()
                print("MFC Port Opened")
                logging.critical("MFC Port Opened %d", i)
                break
            except Exception as e:
                print("ERROR, MFC port did not open", e)
                logging.critical("ERROR, MFC port did not open %s", e)
                self.ser=[]
            
    def CloseConnection(self):
        try:
            self.ser.close()
            time.sleep(0.1)
            print("MFC Port Closed")
        except Exception as e:
            print("ERROR, MFC port did not close", e)
            logging.critical("ERROR, MFC port did not close", e)
            self.ser=[]
            
    def TestMFCConnection(self):
        try:
            if self.ser.isOpen():
                print("MFC serial port is open")
            else:
                print("ERROR, MFC port is not open")
                self.ser=[]
        except:
            print("ERROR, Unknown, probably no MFC connection")
            
    def ReadInformation(self):
        try:
            self.ser.write(b'AZI\r\n')
            printed=self.ser.readline()
            print(printed.decode('ascii'))
        except:
            print("ERROR")         
            
    def ReadMenu(self):
        try:
            self.ser.write(b'AZM\r\n')
            printed=self.ser.readlines()
            for line in printed:
                print(line.decode('ascii'))
        except:
            print("ERROR") 

    #Logging is added for debugging purposes. it is only being used to display values on GUI
    def ReadPV(self, channel):
        try:
            command = b"".join([b'AZ.', PVChannels[channel-1], b'k\r\n']) # Construct command
            start_time = time.time()
            self.ser.write(command)  # Write to the MFC
            result = self.ser.readline()  # Read the result
            signal_speed = time.time() - start_time
            decoded = result.decode('ascii')
            split = decoded.split(',')
            if split[0] != 'AZ':
                raise ValueError("Invalid response from MFC")
            flowrate = split[5] if len(split) > 5 else None
            # Group logging into one call
            logging.debug(
                "ReadPV , %s, %s ,  %.4f sec , %s, empty ,%s ",
                flowrate, command, signal_speed, channel, result
            )
            return flowrate
        except Exception as e:
            logging.debug("Error in MFC Read PV: %s", e)
            print("Error in MFC Read PV")
    #Logging is added for debugging purposes.
    def ReadSP(self, channel):
        try:
            # Construct and log the command
            command = b"".join([b'AZ.', SPChannels[channel-1], b'P1?\r\n'])
            start_time = time.time()
            self.ser.write(command)
            result = self.ser.readline()
            signal_speed = time.time() - start_time
            decoded = result.decode('ascii')
            split = decoded.split(',')
            sp_value = split[4] if len(split) > 4 else None
            #SP_error = sp_value - split[5] if len(split) > 5 else None Doesnt work.
            # Grouped logging for ReadSP
            logging.debug(
                "ReadSP ,  %s,  %s,  %.4f sec,  %s, empty, %s",
                sp_value, command, signal_speed, channel, result
            )
            return sp_value    
        except Exception as e:
            logging.debug("Error in MFC Read SP: %s, %s, %s", e, command, result)
            print("Error in MFC Read SP")         
    #Logging is added for debugging purposes. 
    def WriteSP(self, channel, value):
        try:
            # Format numeric value if needed
            if isinstance(value, (int, float)):
                value = "{:.2f}".format(value)
                value=str(value)
                logging.debug("WriteSP_Int , %s", value)
            if isinstance(value, str):
                command = b"".join([b'AZ.', SPChannels[channel-1], b'P01=', value.encode('ascii'), b'\r\n'])
                start_time = time.time()
                time.sleep(SP_WRITE_DELAY)
                self.ser.write(command)
                signal_speed = time.time() - start_time
                result = self.ser.readlines()
                logging.critical(
                    "WriteSP , %s,  %s ,  %.4f sec ,  %s , empty , %s",
                    value, command, signal_speed, channel, result 
                )
                SP_MFC = self.ReadSP(channel)
                if SP_MFC is None:
                    SP_MFC = self.ReadSP(channel)
                SP_MFC = float(SP_MFC)
                for i in range(3):  
                    if abs(SP_MFC - float(value)) > 0.1:
                        start_time = time.time()
                        self.ser.write(command)
                        time.sleep(SP_WRITE_DELAY)
                        signal_speed = time.time() - start_time
                        result = self.ser.readlines()
                        logging.critical(
                        "Reattempt_to_Write_SP , %s,  %s ,  %.4f sec ,  %s , empty , %s",
                        value, command, signal_speed, channel, result 
                    )
                    else:
                        break
                print(f"Wrote: {value}, to Channel {channel}")    


        except Exception as e:
            logging.critical("Error in MFC Write SP: %s", e )
            print("Error in MFC Write SP")

# Temperature controller. SImilar structure as the MFC but with different communication protocol
class WatlowConnection:
    def __init__(self, port='COM4', baudrate=38400, timeout=0.5):
        self.port=port
        self.baudrate=baudrate
        self.timeout=timeout
        self.ser=[]
        self.ConnectionCounter = 0  
        self.FirstTime = True
        self.onoff = False   
        
    def Connect(self,port):
        
        for i in range(3):
            try:
                self.FirstTime = False
                print(port)
                self.port = port
                print("Connecting to Watlow on port attempt", i+1)
                self.ser = serial.Serial(port, self.baudrate, timeout=self.timeout)
                time.sleep(0.8)
                self.ser.isOpen()
                print("Watlow is Connected")
                #print(self.ReadSP())
                logging.critical("Watlow is Connected %d", i)
                break
            except Exception as e:
                print("ERROR, Watlow port did not open" , e)
                logging.critical("ERROR, Watlow port did not open %s" , e)
                self.ser=[]
            
    def CloseConnection(self):
        try:
            self.ser.close()
            time.sleep(0.2)
            print("Watlow port Closed")
        except Exception as e:
            print("ERROR, Watlow port did not close %s", e)
            logging.critical("ERROR, Watlow port did not close %s", e)
            self.ser=[]
            
    def TestWatlowConnection(self):
        try:
            if self.ser.isOpen():
                print("Watlow serial port is open")
            else:
                print("ERROR, Watlow port is not open")
                self.ser=[]
        except:
            print("ERROR, Unknown, probably no Watlow connection")       
            
    def ReadPV(self):
        try:
            if self.ConnectionCounter < 75:
                self.ConnectionCounter += 1
            else:
                #print("Reconnecting to Watlow as a routine check. Don't worry")
                #self.Connect(self.port)
                
                #logging.critical("Reconnecting as a routine check")
                self.ConnectionCounter = 0
            self.ser.write(binascii.unhexlify('55ff0510000006e8010301040101e399'))
            printed=self.ser.readline()
            value=bytes.hex(printed)[30:-4]
            ReadTemp = struct.unpack('>f', binascii.unhexlify(value))[0]
            ReadTemp = (ReadTemp-32)/1.8
            ReadTemp = round(ReadTemp,2)
            logging.debug( "WatlowPV , %f , %s",ReadTemp, value)
            return ReadTemp
        except Exception as e:
            print("ERROR in Read T %s", e) 
            logging.critical("Error in read Temperature %s, %s",e, value)      
            
    def ReadSP(self):
        try:
            self.ser.write(binascii.unhexlify('55ff0510000006e80103010701018776'))
            printed=self.ser.readline()
            value=bytes.hex(printed)[30:-4]
            ReadTemp = struct.unpack('>f', binascii.unhexlify(value))[0]
            ReadTemp = (ReadTemp-32)/1.8
            return ReadTemp
        except:
            print("ERROR in Read SP T")     
            
    def WriteSP(self,value):
        try:
            self.ControlMode('On')
            print("Setting SP to:", value)
            pv = self.ReadPV()
            print("PV is:", pv)
            writevalue = binascii.unhexlify('010407010108') + struct.pack('>f', value*1.8+32)            
            checksum = struct.pack('<H', ~crc(writevalue) & 0xffff)
            SendString = binascii.unhexlify('55ff051000000aec') + writevalue + checksum
            self.ser.write(SendString)
            self.ser.readline()
            self.ser.readline()
            value = self.ReadSP()
            #self.ControlMode('On')
            print('Set point changed to:',value)
        except Exception as e:
            print("ERROR in Write SP T", e) 
            logging.critical("Error in Write Setpoint %s",e)     
          
    def WriteRampRate(self,value):
        try:
            writevalue = binascii.unhexlify('010407110108') + struct.pack('>f', value*9/5)       
            checksum = struct.pack('<H', ~crc(writevalue) & 0xffff)
            SendString = binascii.unhexlify('55ff051000000aec') + writevalue + checksum
            self.ser.write(SendString)
            self.ser.readline()
            self.ser.readline()
            print('Ramp rate set to:', value) 
        except:
            print("ERROR in Write Ramp Rate T")       
        
    def ControlMode(self,OnOff):
        try:
            if OnOff == 'On':
                SendString = binascii.unhexlify('55ff05100300094601140801010f01000a4027')
            elif OnOff == 'Off':
                SendString = binascii.unhexlify('55ff05100300094601140801010f01003ee750')
            self.ser.write(SendString)
            self.ser.readline()
            self.ser.readline()
            if OnOff == 'On':
                print('Control Loop On')
            elif OnOff == 'Off':
                print('Control Loop Off')
        except Exception as e:
            print("ERROR in Write Watlow Control Mode %s" ,e)
            logging.critical("Error in setting Control Mode %s",e)

#New class for NI temperature controller

class NITemperatureConnection:
    """
    Class for managing NI thermocouple connection.
    The connection (NI task) is only created once Connect() is called.
    This allows the application to run even if the device is initially disconnected.
    """
    def __init__(self, device_name="Dev1", channel="ai0",
                 tc_type=nidaqmx.constants.ThermocoupleType.K,
                 min_val=20, max_val=40):
        self.device_name = device_name
        self.channel = channel
        self.physical_channel = f"{device_name}/{channel}"
        self.tc_type = tc_type
        self.min_val = min_val
        self.max_val = max_val
        self.task = None  # Task will be created later upon calling Connect()

    def Connect(self, DeviceName=DefaultNIComPort , Channel='ai0'):
        """
        Attempts to create and configure an NI task for the thermocouple.
        If the device isn’t connected, it logs an error and leaves self.task as None.
        """
        try:
            if self.task is not None:
                self.task.close()
        except Exception as e:
            logging.error("Error closing previous task: %s", e)
        try:
            self.task = nidaqmx.Task()
            self.device_name = DeviceName
            self.physical_channel = f"{DeviceName}/{Channel}"
            #print("Connecting to NI thermocouple on %s", self.physical_channel)
            self.task.ai_channels.add_ai_thrmcpl_chan(
                self.physical_channel,
                min_val=self.min_val,
                max_val=self.max_val,
                units=nidaqmx.constants.TemperatureUnits.DEG_C,
                thermocouple_type=self.tc_type,
                cjc_source=nidaqmx.constants.CJCSource.BUILT_IN
            )
            logging.critical("NI thermocouple on %s connected successfully.", self.physical_channel)
        except Exception as e:
            logging.error("Error connecting NI thermocouple on %s: %s", self.physical_channel, e)
            self.task = None

    def ReadPV(self):
        """
        Reads a single temperature sample from the thermocouple using the persistent task.
        Returns the temperature or None if the device is not connected.
        """
        if self.task is None:
            logging.warning("NI task not connected. Please call Connect() first.")
            return None
        try:
            temperature = self.task.read()
            temperature = round(temperature, 2)
            logging.critical("Temperature read: %.2f °C", temperature)
            #print("NI Temperature read: %.2f °C", temperature)
            return temperature
        except Exception as e:
            logging.critical("Error reading temperature: %s", e)
            return None

    def TestConnection(self):
        """
        Tests the NI thermocouple connection by attempting to read a temperature.
        Returns True if successful, False otherwise.
        """
        self.Connect()
        temperature = self.ReadPV()
        if temperature is not None:
            logging.critical("NI thermocouple connection is good. Temperature: %.2f °C", temperature)
            return True
        else:
            logging.critical("NI thermocouple connection test failed." )
            return False

    def Close(self):
        """
        Closes the NI task if it is connected. This method is safe to call whether or not a task has been created.
        """
        if self.task is not None:
            try:
                self.task.close()
                logging.critical("NI thermocouple task closed successfully.")
            except Exception as e:
                logging.critical("Error closing NI thermocouple task: %s", e)
            finally:
                self.task = None
        else:
            logging.critical("No NI task to close.")
        

class ControllerGui:
    def __init__(self, master):
        self.master = master
        master.title("Reactor Controller GUI")

        # layout master
        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)

        # notebook with two tabs
        self.notebook = ttk.Notebook(master)
        self.notebook.grid(row=0, column=0, sticky='nsew')

        # Tab 1: original controls
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="Controls")

        # Tab 2: live plots
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="Live Plots")

        # build each
        self._build_controls(self.tab1)
        self._build_plots(self.tab2)

        # start periodic tasks
        #self.master.after(0, self.ReadPVs)
        #self.master.after(5000, self._update_plots)

    def _build_controls(self, parent):

            self.TimeLeftSeconds=0
            self.ReachedTempBool=False
            self.LogFile = None
            self.after_id = None
            self.closing = False
            self.WatlowConnectionLoopCounter =0
            self.MFCNames = MFCNames
            print(MFCNames)
            print(self.MFCNames)
            #self.LoggingEnabled = False
            #Frames

            
            
            self.GeneralFrame = tkinter.LabelFrame(parent, text = "GeneralCommands", padx=10, pady=10)
            self.GeneralFrame.grid(row=0, column=0)
        
            self.ProfileControlFrame = tkinter.LabelFrame(parent, text="Profile Controls", padx=10, pady=10)
            self.ProfileControlFrame.grid(row=0, column=1, sticky='nsew', columnspan=2)

            self.MFC1Frame = tkinter.LabelFrame(parent, text = "MFC 1", padx=10, pady=10)
            self.MFC1Frame.grid(row=1, column=0)
            
            if Have8ComPorts:
                #print("Have 8 Com Ports")
                self.MFC2Frame = tkinter.LabelFrame(parent, text = "MFC 2", padx=10, pady=10)
                self.MFC2Frame.grid(row=1, column=1)       

            if HaveWatlow:       
                self.TControllerFrame = tkinter.LabelFrame(parent, text = "T Controller", padx=10, pady=10)
                self.TControllerFrame.grid(row=1, column=2) if Have8ComPorts else self.TControllerFrame.grid(row=1, column=1)      

            if HaveDosing:
                self.DosingValveFrame = tkinter.LabelFrame(parent, text = "Dosing Valve Controller", padx=10, pady=10)
                self.DosingValveFrame.grid(row=1, column=4)    
                
            #self.ProfileControlFrame = tkinter.LabelFrame(self.master, text = "Profile Controls", padx=10, pady=10)
            #self.ProfileControlFrame.grid(row=0, column=1, )       

            #self.OffFrame = tkinter.LabelFrame(self.master, text = "Off Controls", padx=10, pady=10)
            #self.OffFrame.grid(row=1, column=4)   
            
            # ——————————————————————————————————————
            # container that will hold canvas + scrollbar
            self.profile_container = tkinter.LabelFrame(parent, labelanchor= "n", text="Profile Configuration Values", padx=10, pady=10)   
            self.profile_container.grid(row=2, column=0, columnspan=5, sticky="nsew")  # adjust row/col as needed

            # the canvas on which we’ll put the actual frame
            self.profile_canvas = tkinter.Canvas(self.profile_container,borderwidth=0,highlightthickness=0)
            # vertical scrollbar hooked to the canvas
            self.profile_vscroll = tkinter.Scrollbar(self.profile_container,orient="vertical",command=self.profile_canvas.yview)
            self.profile_canvas.configure(yscrollcommand=self.profile_vscroll.set)
            # layout canvas & scrollbar
            self.profile_vscroll.pack(side="right", fill="y")
            self.profile_canvas.pack(side="left", fill="both", expand=True)
            self.ProfilePiecesFrame = tkinter.Frame(self.profile_canvas)
            # put the frame into the canvas
            self._profile_frame_id = self.profile_canvas.create_window((0, 0),window=self.ProfilePiecesFrame,anchor="n")
            # bind to resizing
            self.profile_canvas.bind("<Configure>", self._on_profile_canvas_configure) 
            
            #self.ProfilePiecesFrame= tkinter.LabelFrame(parent, text = "Profile Pieces", padx=10, pady=10)
            #self.ProfilePiecesFrame.grid(row=2, column=0, columnspan=5)    

            #MainFrame
            self.label = tkinter.Label(self.GeneralFrame, text=TITTLE)
            self.label.grid(row=0,column=0,columnspan=2)
            self.close_button = tkinter.Button(self.GeneralFrame, text="Close", command=self.CloseProgram, width=20, height=2, bg='red')
            self.close_button.grid(row=1,column=0,columnspan=2)
            self.ConnectButton = tkinter.Button(self.GeneralFrame, text="Start Everything", command=self.ConnectControllers, bg='#90EE90')
            self.ConnectButton.grid(row=4,column=0,columnspan=2)
            #----Delay for SP write----- #
            self.DelayLabel = tkinter.Label(self.GeneralFrame, text="Set SP_WRITE_DELAY (sec):")
            self.DelayLabel.grid(row=5, column=0, sticky='e')  # align to the right
            self.DelayEntry = tkinter.Entry(self.GeneralFrame)
            self.DelayEntry.grid(row=5, column=1, sticky='w') # align to the left
            self.UpdateDelayButton = tkinter.Button(self.GeneralFrame, text="Update Delay", command=self.update_sp_write_delay, bg='#90EE90')
            self.UpdateDelayButton.grid(row=6, column=0, columnspan=2, pady=5)
            #self.LoggingEnabled = tkinter.Button(self.GeneralFrame, text = "Enable Logging", command = self.EnableLogging, bg = "#90EE90" ) ### Work in progress
            #self.LoggingEnabled.grid(row=5,column=0,columnspan=2)
            #MFC 1 Part
            self.MFCComPort1Label = tkinter.Label(self.MFC1Frame, text = "MFC Com Port")
            self.MFCComPort1Label.grid(row=0,column=0)
            self.MFCComPort1 = tkinter.Entry(self.MFC1Frame, width=10)
            self.MFCComPort1.grid(row=0,column=1)
            self.MFCComPort1.insert(0,DefaultMFC1ComPort)
            self.TestMFCConnection1 = tkinter.Button(self.MFC1Frame, text="Test MFC Connection", command=Brooks1.TestMFCConnection, bg='#90EE90')
            self.TestMFCConnection1.grid(row=0,column=2)
            self.MFCSetButtons1={}
            self.MFCInputButton1={}
            self.ReadFlowPart1={}
            self.ShortTextPiece1={}
            for i in range(4):
                self.MFCInputButton1[i]= tkinter.Entry(self.MFC1Frame, width=5)
                self.MFCInputButton1[i].grid(row=i+1,column=1)
                self.MFCSetButtons1[i] = tkinter.Button(self.MFC1Frame, text="Set " + self.MFCNames[i] + " (" + str(i+1) + ") to", command=lambda i=i: self.WriteMFCSPButton1(i+1))
                self.MFCSetButtons1[i].grid(row=i+1,column=0)
                self.ShortTextPiece1[i]= tkinter.Label(self.MFC1Frame, text="     Current Reading (sccm) :")
                self.ShortTextPiece1[i].grid(row=i+1,column=2)
                self.ReadFlowPart1[i]  = tkinter.Label(self.MFC1Frame, text="N/A")
                self.ReadFlowPart1[i].grid(row=i+1,column=3)
            print(Have8ComPorts)
            if Have8ComPorts:
                #MFC 2 Part
                self.MFCComPort2Label = tkinter.Label(self.MFC2Frame, text = "MFC Com Port")
                self.MFCComPort2Label.grid(row=0,column=0)
                self.MFCComPort2 = tkinter.Entry(self.MFC2Frame, width=10)
                self.MFCComPort2.grid(row=0,column=1)
                self.MFCComPort2.insert(0,DefaultMFC2ComPort)
                #print("made it to inside init")
                self.TestMFCConnection2 = tkinter.Button(self.MFC2Frame, text="Test MFC Connection", command=Brooks2.TestMFCConnection, bg='#90EE90')
                self.TestMFCConnection2.grid(row=0,column=2)
                self.MFCSetButtons2={}
                self.MFCInputButton2={}
                self.ReadFlowPart2={}
                self.ShortTextPiece2={}
                for i in range(4):
                    self.MFCInputButton2[i]= tkinter.Entry(self.MFC2Frame, width=5)
                    self.MFCInputButton2[i].grid(row=i+1,column=1)
                    self.MFCSetButtons2[i] = tkinter.Button(self.MFC2Frame, text="Set " + self.MFCNames[i+4] + " (" + str(i+1) + ") to", command=lambda i=i: self.WriteMFCSPButton2(i+1))
                    self.MFCSetButtons2[i].grid(row=i+1,column=0)
                    self.ShortTextPiece2[i]= tkinter.Label(self.MFC2Frame, text="     Current Reading (sccm) :")
                    self.ShortTextPiece2[i].grid(row=i+1,column=2)
                    self.ReadFlowPart2[i]  = tkinter.Label(self.MFC2Frame, text="N/A")
                    self.ReadFlowPart2[i].grid(row=i+1,column=3)    

            if HaveWatlow:
                #Watlow Part
                self.WatlowComPortLabel = tkinter.Label(self.TControllerFrame, text = "Watlow Com Port")
                self.WatlowComPortLabel.grid(row=0,column=0)
                self.WatlowComPort = tkinter.Entry(self.TControllerFrame, width=10)
                self.WatlowComPort.grid(row=0,column=1)       
                self.WatlowComPort.insert(0,DefaultWatlowComPort)
                self.TestWatlowConnection = tkinter.Button(self.TControllerFrame, text="Test Watlow Connection", command=Wt.TestWatlowConnection, bg='#90EE90')
                self.TestWatlowConnection.grid(row=0,column=2)
                self.TControlOff = tkinter.Button(self.TControllerFrame, text="T Control Off", command = self.ToggleWatlowControl, bg='red')
                self.TControlOff.grid(row=0,column=3)
                self.TempInputButton= tkinter.Entry(self.TControllerFrame, width=5)
                self.TempInputButton.grid(row=1,column=1)
                self.TempSetButtons = tkinter.Button(self.TControllerFrame, text="Set Temperature to", command=self.WriteTempSPButton)
                self.TempSetButtons.grid(row=1,column=0)
                self.TempTextPiece= tkinter.Label(self.TControllerFrame, text="  Current Reading (\N{DEGREE SIGN}C) :")
                self.TempTextPiece.grid(row=1,column=2)
                self.ReadTempPart= tkinter.Label(self.TControllerFrame, text="N/A")
                self.ReadTempPart.grid(row=1,column=3)
                self.RampRateInputButton= tkinter.Entry(self.TControllerFrame, width=5)
                self.RampRateInputButton.grid(row=2,column=1)
                self.RampRateLabel = tkinter.Label(self.TControllerFrame, text="with ramp rate of")
                self.RampRateLabel.grid(row=2,column=0)
                self.SetPointTextPiece= tkinter.Label(self.TControllerFrame, text="  Current Set Point (\N{DEGREE SIGN}C) :")
                self.SetPointTextPiece.grid(row=2,column=2)
                self.SetPointPart= tkinter.Label(self.TControllerFrame, text="N/A")
                self.SetPointPart.grid(row=2,column=3)
                # Creates a row for the NI temperature Indicator
                if HaveNITemperature:
                    self.NITemperaturePortLabel = tkinter.Label(self.TControllerFrame, text="NI Temperature Dev: ")
                    self.NITemperaturePortLabel.grid(row=3, column=0)
                    self.NITemperaturePort = tkinter.Entry(self.TControllerFrame, width=10)
                    self.NITemperaturePort.grid(row=3,column=1)  
                    self.NITemperaturePort.insert(0,DefaultNIComPort)
                    self.TestNIConnection = tkinter.Button(self.TControllerFrame, text="Test NI Connection", command=NI.TestConnection, bg='#90EE90')
                    self.TestNIConnection.grid(row=3,column=2)
                    self.NITemperatureLabel = tkinter.Label(self.TControllerFrame, text="NI Temperature (\N{DEGREE SIGN}C):")
                    self.NITemperatureLabel.grid(row=4, column=0)
                    self.ReadNITemperaturePV = tkinter.Label(self.TControllerFrame, text="N/A", width=10)   
                    self.ReadNITemperaturePV.grid(row=4, column=1)



            #Profile Part
            self.LoadProfile  = tkinter.Button(self.ProfileControlFrame, text="Load Profile", command=self.LoadProfileFile)
            self.LoadProfile.grid(row=0,column=0) 
            self.LoadProfileBool  = tkinter.Label(self.ProfileControlFrame, text="No Profile Loaded")
            self.LoadProfileBool.grid(row=0,column=1)         
            self.StartStop = tkinter.Button(self.ProfileControlFrame, text="Start Profile",command=self.StartStop)
            self.StartStop.grid(row=1,column=0)
            self.ProfileBool = tkinter.Label(self.ProfileControlFrame, text="Profile is Off")
            self.ProfileBool.grid(row=1,column=1)        
            self.StepNumberLabel = tkinter.Label(self.ProfileControlFrame, text="Step Number:")
            self.StepNumberLabel.grid(row=2,column=0)
            self.StepNumber = tkinter.Label(self.ProfileControlFrame, text="No Profile")
            self.StepNumber.grid(row=2,column=1)
            self.TimeLeftText = tkinter.Label(self.ProfileControlFrame, text='Minutes Left:')
            self.TimeLeftText.grid(row=3,column=0)
            self.TimeLeft = tkinter.Label(self.ProfileControlFrame, text='N/A')
            self.TimeLeft.grid(row=3,column=1)
            self.SkipStep = tkinter.Button(self.ProfileControlFrame, text="Skip Step", command=self.SkipStep)
            self.SkipStep.grid(row=4,column=0,columnspan=2) 

            if HaveDosing:
                #Vici Part
                self.ViciComPortLabel = tkinter.Label(self.DosingValveFrame, text = "Com Port")
                self.ViciComPortLabel.grid(row=0,column=0)
                self.ViciComPort = tkinter.Entry(self.DosingValveFrame, width=10)
                self.ViciComPort.grid(row=0,column=1)     
                self.ViciComPort.insert(0,DefaultViciComPort)
                self.TestDosingValveConnection = tkinter.Button(self.DosingValveFrame, text="Test Connection", command=Va.Test6portConnection, bg='#90EE90')
                self.TestDosingValveConnection.grid(row=0,column=2,columnspan=2)
                self.ReadPositionLabel = tkinter.Label(self.DosingValveFrame, text = "Valve Position")
                self.ReadPositionLabel.grid(row=1,column=0)
                self.ReadPosition = tkinter.Label(self.DosingValveFrame, text="N/A")
                self.ReadPosition.grid(row=1,column=1)
                self.GoToPosA = tkinter.Button(self.DosingValveFrame, text="Set to Pos A", command=self.SetPosA, bg='#90EE90')
                self.GoToPosA.grid(row=1,column=2)
                self.GoToPosB = tkinter.Button(self.DosingValveFrame, text="Set to Pos B", command=self.SetPosB, bg='#90EE90')
                self.GoToPosB.grid(row=1,column=3)
                self.DoseTimeLabel = tkinter.Label(self.DosingValveFrame, text = "Dose Time (sec)")
                self.DoseTimeLabel.grid(row=2,column=0)
                self.DoseTime = tkinter.Entry(self.DosingValveFrame, width=10)
                self.DoseTime.grid(row=2,column=1)       
                self.DoseBreakLabel = tkinter.Label(self.DosingValveFrame, text = "Wait Time (min)")
                self.DoseBreakLabel.grid(row=2,column=2)
                self.DoseBreak = tkinter.Entry(self.DosingValveFrame, width=10)
                self.DoseBreak.grid(row=2,column=3)       
                self.NumDoseLabel = tkinter.Label(self.DosingValveFrame, text = "Num of Doses")
                self.NumDoseLabel.grid(row=3,column=0)
                self.NumDose = tkinter.Entry(self.DosingValveFrame, width=10)
                self.NumDose.grid(row=3,column=1)       
                self.DoseNumberLabel = tkinter.Label(self.DosingValveFrame, text="Dose Number:")
                self.DoseNumberLabel.grid(row=3,column=2)
                self.DoseNumber = tkinter.Label(self.DosingValveFrame, text="Not Dosing")
                self.DoseNumber.grid(row=3,column=3)
                self.DoseStartStop = tkinter.Button(self.DosingValveFrame, text="Start Dosing",command=self.DoseStartStop)
                self.DoseStartStop.grid(row=4,column=0)
                self.DoseBool = tkinter.Label(self.DosingValveFrame, text="Dosing is Off")
                self.DoseBool.grid(row=4,column=1)        
                self.DoseTimeText = tkinter.Label(self.DosingValveFrame, text='Seconds Left:')
                self.DoseTimeText.grid(row=4,column=2)
                self.DoseTimeLeft = tkinter.Label(self.DosingValveFrame, text='N/A')
                self.DoseTimeLeft.grid(row=4,column=3)

            #self.master.geometry("800x400")    

    def _on_profile_canvas_configure(self, event):
        # event.width  = new canvas width
        # event.height = new canvas height
        # move the window item to (canvas_width/2, canvas_height/2)
        self.profile_canvas.coords(
            self._profile_frame_id,
            event.width  // 2,
            event.height // 2
        )
    # Builds the plots tab with live data
    def _build_plots(self, parent):
        """"
        Create a grid of plots for each channel. Stores the values in a dictionary.
        """""
        # determine which channels to plot 
        self.plot_keys = []
        for ch in range(1, 5):
            self.plot_keys.append(f"MFC1-{ch}")
        if HaveWatlow:
            self.plot_keys.append("WATLOW")    
        if Have8ComPorts:
            for ch in range(1, 5):
                self.plot_keys.append(f"MFC2-{ch}")
        
        if HaveNITemperature:
            self.plot_keys.append("NI")

        n = len(self.plot_keys)
        cols = 5
        rows = (n + cols - 1) // cols

        # size can stay the same, but layout will manage spacing
        fig = Figure(figsize=(cols * 2, rows * 2))
        self.axes = {}
        self.lines = {}
        self.setpoint = {}

        for idx, key in enumerate(self.plot_keys):
            ax = fig.add_subplot(rows, cols, idx + 1)
            if key.startswith("MFC1"):
                ch = int(key.split("-")[1])
                ax.set_title(f"{self.MFCNames[ch-1]} (sccm)")
            elif key.startswith("MFC2"):
                ch = int(key.split("-")[1])
                ax.set_title(f"{self.MFCNames[ch+3]} (sccm)")
            else:
                ax.set_title(key)
            ax.set_xlabel("Time (s)")
            self.axes[key] = ax
            self.lines[key], = ax.plot([], [])
            #self.setpoint[key], = ax.plot([], [], 'r--', label='Setpoint')

        # --- add spacing ---
        # Option A: automatic
        fig.tight_layout(pad=1.0)

        # Option B: manual control (uncomment if you want to tweak yourself)
        # fig.subplots_adjust(
        #     left=0.05, right=0.98,
        #     top=0.95, bottom=0.05,
        #     wspace=0.4,  # horizontal space between plots
        #     hspace=0.6   # vertical space between plots
        # )

        self.time_buffer = []
        self.data_buffer = {k: [] for k in self.plot_keys}
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas = canvas
    # Update the plots every 5 seconds, it shoudl onlyy be called after reading and storing pvs in self.variables
    def _update_plots(self):
        t = time.time()
        self.time_buffer.append(t)
        # read each key
        for key in self.plot_keys:
            try:
                if key.startswith("MFC1"):
                    ch = int(key.split("-")[1])
                    val = float(self.mfc1_readings[ch-1].strip()) if self.mfc1_readings[ch-1] is not None else numpy.nan
                    val = 0 if val < 0 else val 
                elif key.startswith("MFC2"):
                    ch = int(key.split("-")[1])
                    val = float(self.mfc2_readings[ch-1].strip())  if self.mfc2_readings[ch-1] is not None else numpy.nan
                    val = 0 if val < 0 else val 
                elif key == "WATLOW":
                    val = self.watlow_temp  if self.watlow_temp is not None else numpy.nan 
                elif key == "NI":
                    val = self.ni_temp  if self.ni_temp is not None else numpy.nan 
                else:
                    val = numpy.nan
                
                self.data_buffer[key].append(val)
                
            except Exception as e:
                print(f"Error uploading graphs {key}: {e}")
                self.data_buffer[key].append(numpy.nan)
        
        # keep last 12 points (1 min at 5 s intervals)
        maxlen = 12*60
        if len(self.time_buffer) > maxlen:
            self.time_buffer = self.time_buffer[-maxlen:]
            for k in self.data_buffer:
                self.data_buffer[k] = self.data_buffer[k][-maxlen:]

        # update line data
        t0 = self.time_buffer[0]
        xs = [x - t0 for x in self.time_buffer]
        for key, line in self.lines.items():
            ys = self.data_buffer[key]
            #setpoint = self.setpoint_buffer[key][-1] if self.setpoint_buffer[key] else 0
            line.set_data(xs, ys)
            #self.setpoint[key].set_data(xs, [setpoint] * len(xs))
            ax = self.axes[key]
            ax.set_xlim(0, xs[-1] if xs else 1)
            ax.relim(); ax.autoscale_view()
        self.canvas.draw_idle()

        #self.master.after(5000, self._update_plots)

    def EnableLogging(self):
        self.LoggingEnabled = not self.LoggingEnabled
    def ConnectControllers(self):
        Brooks1.Connect(self.MFCComPort1.get())
        if Have8ComPorts:
            time.sleep(0.3)    
            Brooks2.Connect(self.MFCComPort2.get())
        if HaveWatlow:
            time.sleep(0.3)
            Wt.Connect(self.WatlowComPort.get())
        if HaveNITemperature:
            NI.Connect(self.NITemperaturePort.get())        
        if HaveDosing:
            time.sleep(0.3)
            Va.Connect(self.ViciComPort.get())
        #Sets the logging location
        if self.LogFile is not None:
            self.LogFile.close()
        filedir = tkinter.filedialog.askdirectory()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.result_path = os.path.join(filedir, f"Controller_Log_{timestamp}.csv")              
        self.LogFile = open(self.result_path,'w',newline='', buffering=1) 
        self.File = csv.writer(self.LogFile, dialect='excel')

        #Here is where the Title goes for the logged data
        TitleRow=['Time']
        TitleRow.append('Step Number')
        TitleRow.append('Time left in step (min)')
        if HaveWatlow:
            TitleRow.append('Set Temperature (\N{DEGREE SIGN}C)')
            TitleRow.append('Read Temperature (\N{DEGREE SIGN}C)')
            TitleRow.append('Ramp Rate (\N{DEGREE SIGN}C/min)')
        TitleRow.extend(self.MFCNames)
        if HaveDosing:
            TitleRow.append('Valve Positions')
            TitleRow.append('Pressure (mbar)')
        
        if HaveNITemperature:
            TitleRow.append('NI Temperature (\N{DEGREE SIGN}C)')
        self.File.writerow(TitleRow)   
        #Starts the logging part
        self.ReadPVs()
    def update_sp_write_delay(self):
        """Reads the user input, validates it, and updates the global SP_WRITE_DELAY."""
        try:
            value = float(self.DelayEntry.get())
            Set_SP_Write_Delay(value)  # or directly set the global here
            print("Success", f"SP_WRITE_DELAY set to {value}")
            #print(SP_WRITE_DELAY)
        except ValueError:
            print("Invalid Input", "Please enter a numeric value for SP_WRITE_DELAY.")

    def CloseProgram(self):
        self.closing = True
        self.master.after(100, self.CloseProgram)  # Schedule the close operation
        if self.after_id is not None:        
            try:
                self.master.after_cancel(self.after_id)
            except tkinter.TclError as e:
                # Log the error if desired; the callback might have already been executed or canceled.
                print(f"Error canceling scheduled callback: {e}")
            finally:
                self.after_id = None
        
        for i in range(4):
            channel=i+1
            Brooks1.WriteSP(channel,0)
            if Have8ComPorts:
                Brooks2.WriteSP(channel,0)
        
        if HaveWatlow:
            Wt.ControlMode('Off')
                
        try:
            self.LogFile.close()
        except:
            pass
        
        if HaveWatlow:
            Wt.CloseConnection()
        if HaveNITemperature:
            NI.Close()
        Brooks1.CloseConnection()
        if Have8ComPorts:
            Brooks2.CloseConnection()
        if HaveDosing:
            Va.CloseConnection()
            #close pressure
        self.master.destroy()
    def WriteMFCSPButton1(self,channel):
        MFCValue = self.MFCInputButton1[channel-1].get()
        try: 
            MFCValue = float(MFCValue)         
            Brooks1.WriteSP(channel,MFCValue)
            #Lets add logic to Detect glitches
            MFC_SP = Brooks1.ReadSP(channel)
            SP_error = MFCValue - float(MFC_SP)
            logging.critical("SP_Error,  %s , %.2f, empty, %s", SP_error, SP_WRITE_DELAY,   channel)
        except:
            print("ERROR in Write MFC SP, probably not a number")

    if Have8ComPorts:
        print("Function for MFC2 Defined")     
        def WriteMFCSPButton2(self,channel):
            MFCValue = self.MFCInputButton2[channel-1].get()
            try: 
                MFCValue = float(MFCValue)         
                Brooks2.WriteSP(channel,MFCValue)
            except:
                print("ERROR in Write MFC SP, probably not a number")
            
    if HaveWatlow:
        def WriteTempSPButton(self):
            Tvalue = self.TempInputButton.get()
            RampRate = self.RampRateInputButton.get()
            try: 
                Wt.WriteSP(float(Tvalue))
                Wt.WriteRampRate(float(RampRate))
                #Wt.WriteSP(float(Tvalue))
                #self.SetPointPart.config(text=str(Wt.ReadSP())[:4])
                print('Wrote SP')
            except Exception as e:
                print("ERROR in Write Temp SP, probably not a number: ", e )
        def ToggleWatlowControl(self):
            print("ToggleWatlowControl")
            if self.TControlOff['text'] == 'T Control Off':
                Wt.ControlMode('Off')
                self.TControlOff['text'] = 'T Control On'
                self.TControlOff['bg'] = 'green'
            else:
                Wt.ControlMode('On')
                self.TControlOff['text'] = 'T Control Off'
                self.TControlOff['bg'] = 'red'         
            
    def StartStop(self): #Starts the Profile
        if self.ProfileBool["text"]=="Profile is Off" :
            try:
                self.ImportPorfile[0][0]
                #self.LoadProfileBool["text"]="Profile Loaded"
            except :
                print("Needs a Profile First")                
                
            try:
                self.ProfileBool["text"]="Profile is On"
                self.StartStop["text"]="STOP PROFILE"
                self.StartStop['bg']='red'
                self.StepNumber["text"]=1
                self.SkipStepBool=False
                self.UpdateAllSetPointsInProfile()  
                self.StepEndTime=datetime.datetime.now()
                self.TimeLeft["text"]='Not Reached Temp'
            except:
                print('Error in profile')
                
        #Stops Profile    
        elif self.ProfileBool["text"]=="Profile is On" :
            self.EndProfile()            
        else:
            print("Profile is broke :/")
        
    def StopProfile(self):
        self.setvar(name ="ProfileOn", value = False)   
                
    def LoadProfileFile(self):
        for child in self.ProfilePiecesFrame.winfo_children():
            child.destroy()
        filename = tkinter.filedialog.askopenfilename(initialdir = "/", title = "FileExplorer", filetypes = (("Text files", "*.xlsx*"), ("all files", "*.*")))
        print("Profile file: ",filename)
        self.LoadProfileBool["text"]="Profile Loaded"
        self.ImportPorfile = pandas.read_excel(filename, header=None)       
        
        ColumnHeadingNames = ["Duration (min)"]
        if HaveWatlow:
            ColumnHeadingNames.append("Temperature (\N{DEGREE SIGN}C)")
            ColumnHeadingNames.append("Ramp Rate (\N{DEGREE SIGN}C/min)")
        for mfcName in self.MFCNames:
            ColumnHeadingNames.append(mfcName)      
        #ColumnHeadingNames.append(MFCNames) # Do not use, it appends and array and logic expect individual values
        print("These are the Column Headings", ColumnHeadingNames)    
        [NumRows, NumColumns]=self.ImportPorfile.shape
        print("This is the File shape:", self.ImportPorfile.shape)
        rows = []        
        for i in range(NumRows):
            
            #Make the step number labels
            e = tkinter.Label(self.ProfilePiecesFrame, text = "".join(["Step ", str(i+1)]))
            
            #Make the step labels
            e.grid(row=i+1,column=0)
            rows.append(e)
            cols = []
            for j in range(NumColumns):
                if i==1:
                    e = tkinter.Label(self.ProfilePiecesFrame, text = ColumnHeadingNames[j])
                    e.grid(row=0, column=j+1, padx = 6) 
                e = tkinter.Label(self.ProfilePiecesFrame, text = self.ImportPorfile[j][i])  ####coding here  
                
                #Check that all entries are valid
                if not isinstance(self.ImportPorfile[j][i],numpy.number) :
                    print("Invalid entry detected")
                    
                #back to making step labels        
                e.grid(row=i+1, column=j+1)
                cols.append(e)
            rows.append(cols)
        self.ProfilePiecesFrame.update_idletasks()
        self.profile_canvas.configure(scrollregion=self.profile_canvas.bbox("all")) 
    # Function separated in a different thread to avoid lagginesses in the GUI
    def ReadInstruments(self):
        # Blocking instrument read function.
        #start_time = time.time()
        self.mfc1_readings = [Brooks1.ReadPV(ch) for ch in range(1, 5)]
        #print("Time in Step 1.1: ", time.time() - start_time)
        
        #start_time = time.time()
        # If 8 COM ports are enabled, read the second set (Brooks2)
        self.mfc2_readings = [Brooks2.ReadPV(ch) for ch in range(1, 5)] if Have8ComPorts else []
        #print("Time in Step 1.15: ", time.time() - start_time)
        
        #start_time = time.time()
        # Read temperature values
        #if HaveWatlow and self.WatlowConnectionLoopCounter < 10:
        #    self.WatlowConnectionLoopCounter += 1
        #elif HaveWatlow:
        #    self.WatlowConnectionLoopCounter = 0
        #    self.WriteTempSPButton()
        #print("Time in Step 1.2: ", time.time() - start_time)
        
        #start_time = time.time()
        self.watlow_temp = Wt.ReadPV() if HaveWatlow else None
        #self.watlow_sp = Wt.ReadSP() if HaveWatlow else None
        self.ni_temp = NI.ReadPV() if HaveNITemperature else None
        #print("Time in Step 1.3: ", time.time() - start_time)
        
        # Read dosing valve state
        self.dosing_state = Va.ReadState() if HaveDosing else None
        self._update_plots()  # Update plots with new data

    def ReadInstrumentsInBackground(self):
        # Start the heavy instrument read in a background thread.
        thread = threading.Thread(target=self._threaded_instrument_read)
        thread.daemon = True  # Optional; ensures the thread will close when the main program exits.
        thread.start()
        

    def _threaded_instrument_read(self):
        # Thread target: run the blocking instrument read then schedule GUI update.
        self.ReadInstruments()
        # Schedule the GUI update (including logging & logic) on the main thread:
        self.label.after(0, self.UpdateGUIAfterReading)

    def UpdateGUIAfterReading(self):
        # --- Step 2: Log Data ---
        now = datetime.datetime.now()
        results = [now.strftime("%m/%d/%y %H:%M:%S")]
        results.append(self.StepNumber["text"])
        results.append(self.TimeLeft["text"])
        
        if HaveWatlow:
            results.append(self.SetPointPart['text'])  # the set point value
            results.append(str(self.watlow_temp))
            results.append(str(self.RampRateInputButton.get()))
        
        # Add MFC1 readings
        for value in self.mfc1_readings:
            results.append(str(value))
        
        # Add MFC2 readings if available
        if Have8ComPorts:
            for value in self.mfc2_readings:
                results.append(str(value))
        
        # Add dosing and NI temperature data if available
        if HaveDosing:
            results.append(str(self.dosing_state))
        if HaveNITemperature:
            results.append(str(self.ni_temp))
        
        self.File.writerow(results)
        #print("Data logged.")

        # --- Step 3: Update GUI Elements ---
        # Update Brooks1 channel display labels
        for i in range(4):
            self.ReadFlowPart1[i].config(text=str(self.mfc1_readings[i]))
        
        # Update Brooks2 channels if available
        if Have8ComPorts:
            for i in range(4):
                self.ReadFlowPart2[i].config(text=str(self.mfc2_readings[i]))
        
        # Update temperature displays
        if HaveWatlow:
            self.ReadTempPart.config(text=str(self.watlow_temp))
        if HaveNITemperature:
            self.ReadNITemperaturePV.config(text=str(self.ni_temp))
        
        # Update dosing valve state display
        if HaveDosing:
            self.ReadPosition.config(text=str(self.dosing_state))
        
        print("Succesfully read PVs and logged data")

        # --- Step 4: Process Profile and Dosing Logic ---
        if self.ProfileBool["text"] == "Profile is On":
            #print("Before Profile Logic")
            if self.ReachedTempBool == False:
                print('Waiting for Temperature')
                try:
                    # Check if temperature has been reached
                    if abs(float(self.ReadTempPart['text']) - float(self.SetPointPart['text'])) < 1:
                        self.ReachedTempBool = True
                        # Start the timer for this step
                        minutesforstep = float(self.ImportPorfile[0][self.StepNumber["text"] - 1])
                        print("Waiting %.2f minutes for next step", {minutesforstep} )
                        self.StepEndTime = datetime.datetime.now() + datetime.timedelta(minutes=minutesforstep)
                except Exception as e:
                    print("Error in reading temperature: ", e)
            
            if self.SkipStepBool or ((datetime.datetime.now() > self.StepEndTime) and self.ReachedTempBool):
                self.SkipStepBool = False
                print('Moving to Next Step')
                try:
                    self.StepNumber["text"] = self.StepNumber["text"] + 1
                    self.UpdateAllSetPointsInProfile()
                    self.ReachedTempBool = False
                    self.TimeLeft["text"] = 'Not Reached Temp'
                    # Access next profile value (if any)
                    self.ImportPorfile[0][self.StepNumber["text"] - 1]
                except:
                    self.EndProfile()
            
            if self.ReachedTempBool:
                TimeLeft = self.StepEndTime - datetime.datetime.now()
                self.TimeLeft["text"] = round(TimeLeft.seconds / 60)
        
        if HaveDosing:
            if self.DoseBool["text"] == "Dosing is On":
                if datetime.datetime.now() > self.DoseEndTime:
                    print('Dosing or Undosing')
                    if self.LastDoseFlag:
                        self.EndDosing()
                        self.DoseTimeLeft["text"] = "Done"
                    else:
                        try:
                            self.DoseTimeLeft["text"] = 'Changing'
                            print(self.ReadPosition["text"])
                            if "CPA" in self.ReadPosition["text"]:
                                self.SetPosB()
                                secondsfordose = float(self.DoseTime.get())
                                self.DoseEndTime = datetime.datetime.now() + datetime.timedelta(seconds=secondsfordose)
                                self.DoseNumber["text"] = self.DoseNumber["text"] + 1
                            elif "CPB" in self.ReadPosition["text"]:
                                self.SetPosA()
                                minutesbetweendoses = float(self.DoseBreak.get())
                                self.DoseEndTime = datetime.datetime.now() + datetime.timedelta(minutes=minutesbetweendoses)
                                if self.DoseNumber["text"] >= numpy.floor(float(self.NumDose.get())):
                                    self.LastDoseFlag = True
                                    self.DoseNumber["text"] = "Done"
                            else:
                                print('I cant read the position')
                        except:
                            self.EndDosing()
                else:
                    DoseTimeLeft = self.DoseEndTime - datetime.datetime.now()
                    self.DoseTimeLeft["text"] = round(DoseTimeLeft.seconds)
        
        #print("Scheduling next ReadPVs cycle")
        # Schedule the next cycle of the event loop.
        self.after_id = self.label.after(3000, self.ReadPVs)

    def ReadPVs(self):
        # The main event loop now only starts the background instrument read.
        if getattr(self, 'closing', False):
            return
        self.ReadInstrumentsInBackground()
          
         
    def UpdateAllSetPointsInProfile(self):
        for j in range(4):
            channel=j+1
            ColIndex=j+3
            value = self.ImportPorfile[ColIndex][self.StepNumber["text"]-1]
            self.MFCInputButton1[j].delete(0,"end")
            self.MFCInputButton1[j].insert(0, value)
            self.WriteMFCSPButton1(channel)
            
        
        if Have8ComPorts:
            for j in range(4):
                channel=j+1
                ColIndex=j+3+4
                value = self.ImportPorfile[ColIndex][self.StepNumber["text"]-1]
                self.MFCInputButton2[j].delete(0,"end")
                self.MFCInputButton2[j].insert(0, value)
                self.WriteMFCSPButton2(channel)                        
        
        if HaveWatlow:        
            temp = self.ImportPorfile[1][self.StepNumber["text"]-1]
            ramprate = self.ImportPorfile[2][self.StepNumber["text"]-1]
            self.TempInputButton.delete(0,"end")
            self.TempInputButton.insert(0,temp)
            self.RampRateInputButton.delete(0,"end")
            self.RampRateInputButton.insert(0,ramprate) 
            self.SetPointPart.config(text=temp)
            self.WriteTempSPButton()

        print('Set Points Updated')
        
    def EndProfile(self):
        self.ProfileBool["text"]="Profile is Off"
        self.StartStop["text"]="Start Profile"
        self.StartStop['bg']='SystemButtonFace'
        self.StepNumber["text"]="No Profile"
        self.TimeLeft["text"]='N/A'
        self.SkipStepBool = False
        self.ReachedTempBool = False
        
    def SkipStep(self):
        print('Step Skipped')
        now = time.strftime("%Y-%m-%d_%H-%M-%S")
        logging.critical("Step Mannually skipped at, %s", now)
        self.SkipStepBool=True

    def SetPosA(self):
        Va.SetToStateA()
        self.ReadPosition["text"] = Va.ReadState()
        
    def SetPosB(self):
        Va.SetToStateB()
        self.ReadPosition["text"] = Va.ReadState()
        
    def DoseStartStop(self): #Starts the Dosing Profile            
        if self.DoseBool["text"]=="Dosing is Off" :          
            DosingCheckFlag=True
                   
            try: #make sure all the inputs are usuable floats
                float(self.DoseTime.get()) 
                float(self.NumDose.get())
                float(self.DoseBreak.get())
                print("Entries Are Good")
            except:
                print("Invalid entries for times")
                DosingCheckFlag=False
                
            try:    
                if "CPA" in self.ReadPosition["text"]:
                    print("In pos A")
                else:
                    DosingCheckFlag=False
                    print('Put in Pos A first')
                    
            except:
                print("Must be in pos A to start, couldn't read it")
                DosingCheckFlag=False
                        
            if DosingCheckFlag:
                try:
                    self.DoseStartStop["text"]="STOP DOSING"
                    self.DoseStartStop['bg']='red'
                    self.DoseNumber["text"]=0
                    self.DoseTimeLeft["text"]=5 
                    self.DoseBool["text"]="Dosing is On"
                    self.LastDoseFlag=False
                       
                    minutesfordose=5/60
                    #print(minutesfordose)
                    self.DoseEndTime=datetime.datetime.now()+datetime.timedelta(minutes=minutesfordose)
                except:
                    print('Error in dose')

        #Stops the dosing
        elif self.DoseBool["text"]=="Dosing is On" :          
            self.EndDosing()
            
        else:
            print("Dose is broken ]':")

    def EndDosing(self):
        self.DoseBool["text"]="Dosing is Off"
        self.DoseStartStop["text"]="Start Dosing"
        self.DoseStartStop['bg']='SystemButtonFace'
        self.DoseNumber["text"]="Not Dosing"
        self.DoseTimeLeft["text"]='N/A'

class ConfigurationGui:
    def __init__(self, master):
        self.master = master
        master.title("Configuration Parameters")
        
        # These variables hold our configuration flags
        self.have_8comports = tkinter.BooleanVar(value=True)
        self.have_temperature = tkinter.BooleanVar(value=True)
        self.have_dosing = tkinter.BooleanVar(value=False)
        self.have_nitemperature = tkinter.BooleanVar(value=True)
        self.enable_error_logger = tkinter.BooleanVar(value=True)
        
        # Frame for inputting the names of the MFC ports
        self.mfc_frame = tkinter.LabelFrame(master, text="MFC Port Names", padx=10, pady=10)
        self.mfc_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        
        self.mfc_names_entries = []
        # Create eight entry fields; only the first four are active by default.
        for i in range(8):
            label = tkinter.Label(self.mfc_frame, text=f"MFC Port {i+1} Name:")
            label.grid(row=i, column=0, sticky="e", padx=5, pady=2)
            entry = tkinter.Entry(self.mfc_frame)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.mfc_names_entries.append(entry)
            # Disable ports 5-8 until user enables 8 COM ports
            if i >= 4 and not self.have_8comports.get():
                entry.config(state="disabled")
        #Default values for COM ports

        self.default_COM_ports = tkinter.LabelFrame(master, text = "Default COM Ports", padx=10, pady=10)
        self.default_COM_ports.grid(row=0, column=2, columnspan=2, padx=10, pady=10)
        self.DefaultMFC1ComPortLabel = tkinter.Label(self.default_COM_ports, text = "MFC 1 Com Port")
        self.DefaultMFC1ComPortLabel.grid(row=0,column=0)
        self.DefaultMFC1ComPort = tkinter.Entry(self.default_COM_ports, width=10)
        self.DefaultMFC1ComPort.grid(row=0,column=1)
        self.DefaultMFC1ComPort.insert(0,DefaultMFC1ComPort)
        self.DefaultMFC2ComPortLabel = tkinter.Label(self.default_COM_ports, text = "MFC 2 Com Port")
        self.DefaultMFC2ComPortLabel.grid(row=1,column=0)
        self.DefaultMFC2ComPort = tkinter.Entry(self.default_COM_ports, width=10)
        self.DefaultMFC2ComPort.grid(row=1,column=1)
        self.DefaultMFC2ComPort.insert(0,DefaultMFC2ComPort)
        self.DefaultWatlowComPortLabel = tkinter.Label(self.default_COM_ports, text = "Watlow Com Port")
        self.DefaultWatlowComPortLabel.grid(row=2,column=0)
        self.DefaultWatlowComPort = tkinter.Entry(self.default_COM_ports, width=10)
        self.DefaultWatlowComPort.grid(row=2,column=1)
        self.DefaultWatlowComPort.insert(0,DefaultWatlowComPort)
        self.DefaultNIComPortLabel = tkinter.Label(self.default_COM_ports, text = "NI Com Port")
        self.DefaultNIComPortLabel.grid(row=3,column=0)
        self.DefaultNIComPort = tkinter.Entry(self.default_COM_ports, width=10)
        self.DefaultNIComPort.grid(row=3,column=1)
        self.DefaultNIComPort.insert(0,DefaultNIComPort)
        self.DefaultViciComPortLabel = tkinter.Label(self.default_COM_ports, text = "Vici Com Port")
        self.DefaultViciComPortLabel.grid(row=4,column=0)
        self.DefaultViciComPort = tkinter.Entry(self.default_COM_ports, width=10)
        self.DefaultViciComPort.grid(row=4,column=1)
        self.DefaultViciComPort.insert(0,DefaultViciComPort)

        # Checkbuttons for various configuration options
        self.chk_8com = tkinter.Checkbutton(master, text="Have 8 Com Ports?", variable=self.have_8comports,
                                       command=self.toggle_mfc_fields)
        
        self.chk_8com.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        self.chk_temp = tkinter.Checkbutton(master, text="Have Temperature Controller?", 
                                       variable=self.have_temperature)
        self.chk_temp.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        
        self.chk_dosing = tkinter.Checkbutton(master, text="Have Dosing Controller?", 
                                         variable=self.have_dosing)
        self.chk_dosing.grid(row=3, column=0, sticky="w", padx=10, pady=5)
        
        self.chk_nitemp = tkinter.Checkbutton(master, text="Have NI Temperature?", 
                                         variable=self.have_nitemperature)
        self.chk_nitemp.grid(row=4, column=0, sticky="w", padx=10, pady=5)

        self.chk_error_logger_enable = tkinter.Checkbutton(master, text="Enable Error Logger?", 
                                         variable=self.enable_error_logger)
        self.chk_error_logger_enable.grid(row=5, column=0, sticky="w", padx=10, pady=5)
        

        self.TittleLabel = tkinter.Label(master, text = "Tittle")
        self.TittleLabel.grid(row=6,column=0)
        self.TittleEntry = tkinter.Entry(master, width=25)
        self.TittleEntry.grid(row=6,column=1)
        self.TittleEntry.insert(0,TITTLE)
        # Button to save the user configuration
        self.save_button = tkinter.Button(master, text="Save Configuration", command=self.save_configuration)
        self.save_button.grid(row=7, column=0, columnspan=1, padx=10, pady=10)
        self.upload_button = tkinter.Button(master, text="Upload Configuration", command=self.upload_configuration)
        self.upload_button.grid(row=7, column=1, columnspan=2, padx=10, pady=10)
        
        
        
        # This dictionary will hold the configuration after saving.
        self.configuration = {}
    
    def toggle_mfc_fields(self):
        """
        Enables or disables the extra MFC port name entry fields (ports 5-8)
        based on whether the user has 8 COM ports.
        """
        if self.have_8comports.get():
            # Enable the extra MFC fields.
            for i in range(4, 8):
                self.mfc_names_entries[i].config(state="normal")
        else:
            # Clear and disable the extra MFC fields.
            for i in range(4, 8):
                self.mfc_names_entries[i].delete(0, tkinter.END)
                self.mfc_names_entries[i].config(state="disabled")
    
    def save_configuration(self):
        """
        Collects the configuration parameters entered by the user.
        If "Have 8 COM Ports" is not selected, only the first four MFC names are kept.
        """
        # Get MFC port names based on whether 8 COM ports should be used.
        if self.have_8comports.get():
            mfc_names = [entry.get() for entry in self.mfc_names_entries]
        else:
            mfc_names = [entry.get() for entry in self.mfc_names_entries[:4]]
        
        # Save the configuration into a dictionary.
        self.configuration = {
            'Have8ComPorts': self.have_8comports.get(),
            'HaveWatlow': self.have_temperature.get(),
            'HaveDosing': self.have_dosing.get(),
            'HaveNITemperature': self.have_nitemperature.get(),
            "EnableErrorLogger" : self.enable_error_logger.get(), 
            'MFCNames': mfc_names,
            "DefaultMFC1ComPort": self.DefaultMFC1ComPort.get(),
            "DefaultMFC2ComPort": self.DefaultMFC2ComPort.get(),
            "DefaultWatlowComPort": self.DefaultWatlowComPort.get(),
            "DefaultViciComPort": self.DefaultViciComPort.get(),
            "DefaultNIComPort": self.DefaultNIComPort.get(),
            "Tittle" : self.TittleEntry.get()
        }
        
        # For demonstration, print the configuration.
        print("Configuration Saved:")
        for key, value in self.configuration.items():
            print(f"{key}: {value}")
        
        # Close the configuration window (or you might want to hide it).
        self.master.destroy()
    def upload_configuration(self):
        """
        Opens a file dialog to allow the user to select a configuration file.
        The file is expected to be a plain text (.txt) file with key-value pairs:
        
            Have8ComPorts=True
            HaveWatlow=True
            HaveDosing=False
            HaveNITemperature=True
            MFCNames=COM1,COM2,COM3,COM4,COM5,COM6,COM7,COM8
            
        After reading, the configuration is loaded and the GUI elements are updated.
        """
        # Use filedialog to prompt the user for a configuration file.
        filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not filename:
            return  # User canceled the file selection.
        
        new_config = {}
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue  # Skip empty lines or comments.
                # Expect each line in the format key=value
                if '=' not in line:
                    continue  # Skip lines that do not contain an equals sign.
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                # Convert boolean values appropriately.
                if key in ("Have8ComPorts", "HaveWatlow", "HaveDosing", "HaveNITemperature", "EnableErrorLogger",
                           "DefaultMFC1ComPort", "DefaultMFC2ComPort", "DefaultWatlowComPort",
                           "DefaultViciComPort", "DefaultNIComPort", "Tittle"):
                    print(f"Key: {key}, Value: {value}")
                    new_config[key] = value #in ("true", "1", "yes")
                elif key == "MFCNames":
                    # Split by comma and remove extra whitespace.
                    new_config[key] = [s.strip() for s in value.split(",")]
                else:
                    new_config[key] = value
            # Update the configuration dictionary.
            self.configuration = new_config
            print("Configuration Uploaded:")
            for key, value in self.configuration.items():
                print(f"{key}: {value}")
            
            # Ensure the extra fields are toggled correctly.
            self.toggle_mfc_fields()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload configuration: {e}")
        
        # Close the configuration window after uploading.
        self.master.destroy()


if __name__ == "__main__":
    # Step 1: Launch configuration GUI
    config_root = tkinter.Tk()
    config_app = ConfigurationGui(config_root)
    config_root.mainloop()
    
    # Retrieve configuration from the configuration GUI.
    configuration = config_app.configuration
    TITTLE = configuration.get('Tittle', TITTLE)
    # Step 2: Initialize your controllers based on the configuration
    DefaultMFC1ComPort = configuration.get('DefaultMFC1ComPort', DefaultMFC1ComPort)
    DefaultMFC2ComPort = configuration.get('DefaultMFC2ComPort', DefaultMFC2ComPort)
    DefaultWatlowComPort = configuration.get('DefaultWatlowComPort', DefaultWatlowComPort)
    DefaultViciComPort = configuration.get('DefaultViciComPort', DefaultViciComPort)
    DefaultNIComPort = configuration.get('DefaultNIComPort', DefaultNIComPort)
    Brooks1 = MFCConnection()
    MFCNames = configuration.get('MFCNames', ['MFC1', 'MFC2', 'MFC3', 'MFC4'])
    print(configuration["MFCNames"])
    print(MFCNames)
    if configuration["Have8ComPorts"].lower() == "true":
        Have8ComPorts = True
        Brooks2 = MFCConnection()
    else:
        Have8ComPorts = False
        MFCNames = MFCNames[:4]  # Only keep the first four names if not using 8 COM ports.
    if configuration["HaveWatlow"].lower() == "true":
        HaveWatlow = True
        Wt = WatlowConnection()
    else: 
        HaveWatlow = False
    if configuration["HaveDosing"].lower() == "true":
        HaveDosing = True
        Va = DosingValve()
        Pt = PressureTransducer()
    else:
        HaveDosing = False
    if configuration["HaveNITemperature"].lower() == "true":
        HaveNITemperature = True
        NI = NITemperatureConnection()
    else:
        HaveNITemperature = False
    if configuration["EnableErrorLogger"].lower() == "true":
        print("logger level set to DEBUG")
        new_level =logging.DEBUG
    else:
        print("logger level set to CRITICAL")
        new_level = logging.CRITICAL

    logging.basicConfig(
        level= new_level,  # Log only CRITICAL messages
        format="%(asctime)s,%(lineno)d, %(message)s",
        handlers=[
            #logging.StreamHandler(),  # Log to console
            logging.FileHandler(log_file)  # Log to file
        ]
        )
    
    # Step 3: Launch main Controller GUI
    main_root = tkinter.Tk()
    # Pass the configuration dictionary into the ControllerGui constructor.
    print("Creating GUI")
    main_app = ControllerGui(main_root) #######Need to connect here
    print(HaveNITemperature)
    main_root.mainloop()


#Pt=PressureTransducer()
#Pt.Connect('COM5')
#Pt.ReadPressure()
#Pt.CloseConnection()