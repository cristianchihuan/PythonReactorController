import tkinter
from tkinter import filedialog, messagebox, ttk
import datetime
import time
import logging
import threading
import numpy
import pandas
import os
import csv
from config.settings import SP_OUTPUT_PORT_SIGNAL_TYPES, SP_WRITE_DELAY
from .mfc_config_gui import MFCConfigGUI
from .plots_gui import PlotsGUI

class ControllerGui:
    def __init__(self, master, configuration, devices, mfc_names):
        # Validate required devices
        if not devices.get('brooks1'):
            raise ValueError("Primary MFC (brooks1) is required")
        
        # Validate configuration
        required_keys = ['Have8ComPorts', 'HaveWatlow', 'HaveNITemperature', 'HaveDosing']
        for key in required_keys:
            if key not in configuration:
                raise ValueError(f"Missing required configuration key: {key}")
        
        print("Configuration values:")
        print("Have8ComPorts:", configuration.get('Have8ComPorts'), type(configuration.get('Have8ComPorts')))
        print("HaveWatlow:", configuration.get('HaveWatlow'), type(configuration.get('HaveWatlow')))
        print("HaveNITemperature:", configuration.get('HaveNITemperature'), type(configuration.get('HaveNITemperature')))
        print("HaveDosing:", configuration.get('HaveDosing'), type(configuration.get('HaveDosing')))
        
        self.master = master
        self.config = configuration
        self.SPWRITE_DELAY = SP_WRITE_DELAY
        # Convert string configuration values to boolean properly
        def str_to_bool(value):
            if isinstance(value, str):
                return value.lower() == 'true'
            return bool(value)
        
        self.have_8comports = str_to_bool(configuration.get('Have8ComPorts', False))
        self.have_watlow = str_to_bool(configuration.get('HaveWatlow', False))
        self.have_nitemperature = str_to_bool(configuration.get('HaveNITemperature', False))
        self.have_dosing = str_to_bool(configuration.get('HaveDosing', False))
        
        print("Converted boolean values:")
        print("have_8comports:", self.have_8comports, type(self.have_8comports))
        print("have_watlow:", self.have_watlow, type(self.have_watlow))
        print("have_nitemperature:", self.have_nitemperature, type(self.have_nitemperature))
        print("have_dosing:", self.have_dosing, type(self.have_dosing))
        
        # Only store devices that are enabled
        self.brooks1 = devices['brooks1']  # Always required
        self.brooks2 = devices['brooks2'] if self.have_8comports else None
        self.wt = devices['wt'] if self.have_watlow else None
        self.ni = devices['ni'] if self.have_nitemperature else None
        self.va = devices['va'] if self.have_dosing else None
        
        
        # Split MFC names into MFC1 and MFC2 names
        self.mfc1_names = mfc_names[:4]  # First 4 names for MFC1
        self.mfc2_names = mfc_names[4:]  # Last 4 names for MFC2
        self.mfc_names = mfc_names  # Keep full list for compatibility
        
        self.tittle = configuration.get('Tittle', 'Universal Reactor V5.1.2')

        # Initialize readings arrays
        self.mfc1_readings = [None] * 4  # Initialize with None for 4 channels
        self.mfc2_readings = [None] * 4  # Initialize with None for 4 channels
        self.watlow_temp = None
        self.ni_temp = None
        self.dosing_state = None

        # Initialize logging related attributes
        self.LogFile = None
        self.File = None  # Will be initialized in ConnectControllers when logging starts
        self.result_path = None

        # Initialize profile related attributes
        self.TimeLeftSeconds = 0
        self.ReachedTempBool = False
        self.after_id = None
        self.closing = False
        self.WatlowConnectionLoopCounter = 0
        self.SkipStepBool = False
        self.LastDoseFlag = False
        self.ImportPorfile = None

        # Add thread lock for device communication
        self.device_lock = threading.Lock()

        # Add these lines right after master.title
        default_font = ('TkDefaultFont', 10)  # Increase size from default (usually 9 or 10) to 12
        self.master.option_add('*Font', default_font)
        self.master.option_add('*Entry.Font', default_font)
        self.master.option_add('*Button.Font', default_font)
        self.master.option_add('*Label.Font', default_font)

        # layout master
        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)

        # notebook with three tabs
        self.notebook = ttk.Notebook(master)
        self.notebook.grid(row=0, column=0, sticky='nsew')

        # Tab 1: original controls
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="Controls")

        # Tab 2: live plots
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="Snapshoots")

        # Tab 3: MFC Configuration
        self.tab3 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab3, text="MFC Config")

        # build each
        self._build_controls(self.tab1)
        self.plots_gui = PlotsGUI(self.tab2, self.have_8comports, self.have_watlow, self.have_nitemperature, self.mfc_names)
        self.mfc_config_gui = MFCConfigGUI(self.tab3, self.brooks1, self.brooks2, self.have_8comports, self.mfc_names)

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
        self.MFCNames = self.mfc_names
        
        # Create base frames
        self.GeneralFrame = tkinter.LabelFrame(parent, text = "GeneralCommands", padx=10, pady=10)
        self.GeneralFrame.grid(row=0, column=0)
    
        self.ProfileControlFrame = tkinter.LabelFrame(parent, text="Profile Controls", padx=10, pady=10)
        self.ProfileControlFrame.grid(row=0, column=1, sticky='nsew', columnspan=2)

        # MFC1 Frame (always required)
        self.MFC1Frame = tkinter.LabelFrame(parent, text = "MFC 1", padx=10, pady=10)
        self.MFC1Frame.grid(row=1, column=0)
        
        # MFC2 Frame (only if enabled)
        if self.have_8comports:
            self.MFC2Frame = tkinter.LabelFrame(parent, text = "MFC 2", padx=10, pady=10)
            self.MFC2Frame.grid(row=1, column=1)       

        # Temperature Controller Frame (only if enabled)
        print("have watlow", self.have_watlow)
        if self.have_watlow:       
            self.TControllerFrame = tkinter.LabelFrame(parent, text = "T Controller", padx=10, pady=10)
            self.TControllerFrame.grid(row=1, column=2) if self.have_8comports else self.TControllerFrame.grid(row=1, column=1)      

        # Dosing Valve Frame (only if enabled)
        if self.have_dosing:
            self.DosingValveFrame = tkinter.LabelFrame(parent, text = "Dosing Valve Controller", padx=10, pady=10)
            self.DosingValveFrame.grid(row=1, column=4)    
            
        # Profile container setup
        self.profile_container = tkinter.LabelFrame(parent, labelanchor= "n", text="Profile Configuration Values", padx=10, pady=10)   
        self.profile_container.grid(row=2, column=0, columnspan=5, sticky="nsew")

        self.profile_canvas = tkinter.Canvas(self.profile_container,borderwidth=0,highlightthickness=0)
        self.profile_vscroll = tkinter.Scrollbar(self.profile_container,orient="vertical",command=self.profile_canvas.yview)
        self.profile_canvas.configure(yscrollcommand=self.profile_vscroll.set)
        self.profile_vscroll.pack(side="right", fill="y")
        self.profile_canvas.pack(side="left", fill="both", expand=True)
        self.ProfilePiecesFrame = tkinter.Frame(self.profile_canvas)
        self._profile_frame_id = self.profile_canvas.create_window((0, 0),window=self.ProfilePiecesFrame,anchor="n")
        self.profile_canvas.bind("<Configure>", self._on_profile_canvas_configure) 

        # General Frame Controls
        self.label = tkinter.Label(self.GeneralFrame, text=self.tittle)
        self.label.grid(row=0,column=0,columnspan=2)
        self.close_button = tkinter.Button(self.GeneralFrame, text="Close", command=self.CloseProgram, width=20, height=2, bg='red')
        self.close_button.grid(row=1,column=0,columnspan=2)
        self.ConnectButton = tkinter.Button(self.GeneralFrame, text="Start Everything", command=self.ConnectControllers, bg='#90EE90')
        self.ConnectButton.grid(row=4,column=0,columnspan=2)
        
        # Delay settings
        self.DelayLabel = tkinter.Label(self.GeneralFrame, text="Set SP_WRITE_DELAY (sec):")
        self.DelayLabel.grid(row=5, column=0, sticky='e')
        self.DelayEntry = tkinter.Entry(self.GeneralFrame)
        self.DelayEntry.grid(row=5, column=1, sticky='w')
        self.DelayEntry.insert(0,self.SPWRITE_DELAY)
        self.UpdateDelayButton = tkinter.Button(self.GeneralFrame, text="Update Delay", command=self.update_sp_write_delay, bg='#90EE90')
        self.UpdateDelayButton.grid(row=6, column=0, columnspan=2, pady=5)

        # MFC1 Controls (always required)
        self.MFCComPort1Label = tkinter.Label(self.MFC1Frame, text = "MFC Com Port")
        self.MFCComPort1Label.grid(row=0,column=0)
        self.MFCComPort1 = tkinter.Entry(self.MFC1Frame, width=10)
        self.MFCComPort1.grid(row=0,column=1)
        self.MFCComPort1.insert(0,self.config.get('DefaultMFC1ComPort', 'COM1'))
        self.TestMFCConnection1 = tkinter.Button(self.MFC1Frame, text="Test MFC Connection", command=self.brooks1.TestMFCConnection, bg='#90EE90')
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

        # MFC2 Controls (only if enabled)
        if self.have_8comports:
            self.MFCComPort2Label = tkinter.Label(self.MFC2Frame, text = "MFC Com Port")
            self.MFCComPort2Label.grid(row=0,column=0)
            self.MFCComPort2 = tkinter.Entry(self.MFC2Frame, width=10)
            self.MFCComPort2.grid(row=0,column=1)
            self.MFCComPort2.insert(0,self.config.get('DefaultMFC2ComPort', 'COM2'))
            self.TestMFCConnection2 = tkinter.Button(self.MFC2Frame, text="Test MFC Connection", command=self.brooks2.TestMFCConnection, bg='#90EE90')
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

        # Watlow Controls (only if enabled)
        
        if self.have_watlow:
            self.WatlowComPortLabel = tkinter.Label(self.TControllerFrame, text = "Watlow Com Port")
            self.WatlowComPortLabel.grid(row=0,column=0)
            self.WatlowComPort = tkinter.Entry(self.TControllerFrame, width=10)
            self.WatlowComPort.grid(row=0,column=1)       
            self.WatlowComPort.insert(0,self.config.get('DefaultWatlowComPort', 'COM3'))
            self.TestWatlowConnection = tkinter.Button(self.TControllerFrame, text="Test Watlow Connection", command=self.wt.TestWatlowConnection, bg='#90EE90')
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

            # NI Temperature Controls (only if both Watlow and NI are enabled)
            if self.have_nitemperature:
                self.NITemperaturePortLabel = tkinter.Label(self.TControllerFrame, text="NI Temperature Dev: ")
                self.NITemperaturePortLabel.grid(row=3, column=0)
                self.NITemperaturePort = tkinter.Entry(self.TControllerFrame, width=10)
                self.NITemperaturePort.grid(row=3,column=1)  
                self.NITemperaturePort.insert(0,self.config.get('DefaultNIComPort', 'COM4'))
                self.TestNIConnection = tkinter.Button(self.TControllerFrame, text="Test NI Connection", command=self.ni.TestConnection, bg='#90EE90')
                self.TestNIConnection.grid(row=3,column=2)
                self.NITemperatureLabel = tkinter.Label(self.TControllerFrame, text="NI Temperature (\N{DEGREE SIGN}C):")
                self.NITemperatureLabel.grid(row=4, column=0)
                self.ReadNITemperaturePV = tkinter.Label(self.TControllerFrame, text="N/A", width=10)   
                self.ReadNITemperaturePV.grid(row=4, column=1)

        # Profile Controls
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

        # Go to Step Controls
        self.GoToStepLabel = tkinter.Label(self.ProfileControlFrame, text="Go to Step:")
        self.GoToStepLabel.grid(row=5,column=0)
        self.GoToStepEntry = tkinter.Entry(self.ProfileControlFrame, width=5)
        self.GoToStepEntry.grid(row=5,column=1)
        self.GoToStepButton = tkinter.Button(self.ProfileControlFrame, text="Go", command=self.GoToStep, bg='#90EE90')
        self.GoToStepButton.grid(row=6,column=0,columnspan=2)

        # Dosing Valve Controls (only if enabled)
        if self.have_dosing:
            self.ViciComPortLabel = tkinter.Label(self.DosingValveFrame, text = "Com Port")
            self.ViciComPortLabel.grid(row=0,column=0)
            self.ViciComPort = tkinter.Entry(self.DosingValveFrame, width=10)
            self.ViciComPort.grid(row=0,column=1)     
            self.ViciComPort.insert(0,self.config.get('DefaultViciComPort', 'COM5'))
            self.TestDosingValveConnection = tkinter.Button(self.DosingValveFrame, text="Test Connection", command=self.va.Test6portConnection, bg='#90EE90')
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

    def ReadInstruments(self):
        # Blocking instrument read function.
        try:
            with self.device_lock:  # Acquire lock before reading devices
                # Read MFC1 values (always required)
                self.mfc1_readings = [self.brooks1.ReadPV(ch) for ch in range(1, 5)]
                
                # Read MFC2 values only if enabled
                if self.have_8comports and self.brooks2:
                    self.mfc2_readings = [self.brooks2.ReadPV(ch) for ch in range(1, 5)]
                else:
                    self.mfc2_readings = []
                
                # Read Watlow values only if enabled
                if self.have_watlow and self.wt:
                    self.watlow_temp = self.wt.ReadPV()
                else:
                    self.watlow_temp = None
                
                # Read NI Temperature values only if enabled
                if self.have_nitemperature and self.ni:
                    self.ni_temp = self.ni.ReadPV()
                else:
                    self.ni_temp = None
                
                # Read Dosing Valve values only if enabled
                if self.have_dosing and self.va:
                    self.dosing_state = self.va.ReadState()
                else:
                    self.dosing_state = None
                    
                # Update plots with new data
                self.plots_gui.update_plots(self.mfc1_readings, self.mfc2_readings, self.watlow_temp, self.ni_temp)
                
        except Exception as e:
            logging.error("Error reading instruments: %s", str(e))

    def ReadPVs(self):
        self.master.after(0, self.ReadInstrumentsInBackground)
        
    def ReadInstrumentsInBackground(self):
        threading.Thread(target=self._threaded_instrument_read, daemon=True).start()
        
    def _threaded_instrument_read(self):
        self.ReadInstruments()
        self.master.after(0, self.UpdateGUIAfterReading)

    def EnableLogging(self):
        self.LoggingEnabled = not self.LoggingEnabled
    def ConnectControllers(self):
        """Connect to all enabled devices and initialize logging."""
        # Connect to MFC1 (always required)
        self.brooks1.Connect(self.MFCComPort1.get())
        
        # Connect to MFC2 if enabled
        if self.have_8comports:
            time.sleep(0.3)    
            self.brooks2.Connect(self.MFCComPort2.get())
        
        # Connect to Watlow if enabled
        if self.have_watlow:
            time.sleep(0.3)
            self.wt.Connect(self.WatlowComPort.get())
        
        # Connect to NI Temperature if enabled
        if self.have_nitemperature:
            self.ni.Connect(self.NITemperaturePort.get())        
        
        # Connect to Dosing Valve if enabled
        if self.have_dosing:
            time.sleep(0.3)
            self.va.Connect(self.ViciComPort.get())
        
        # Read MFC configurations after connecting
        time.sleep(0.3)  # Give devices time to initialize
        self.mfc_config_gui.read_mfc1_config()     # Read SP config
        self.mfc_config_gui.read_mfc1_pv_config()  # Read PV config
        
        if self.have_8comports:
            time.sleep(0.3)
            self.mfc_config_gui.read_mfc2_config()     # Read SP config
            self.mfc_config_gui.read_mfc2_pv_config()  # Read PV config
            
        # Set up logging
        if self.LogFile is not None:
            self.LogFile.close()
        
        # Get logging directory from user
        filedir = tkinter.filedialog.askdirectory()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.result_path = os.path.join(filedir, f"Controller_Log_{timestamp}.csv")              
        self.LogFile = open(self.result_path, 'w', newline='', buffering=1) 
        self.File = csv.writer(self.LogFile, dialect='excel')

        # Update PlotsGUI with the new log file path
        self.plots_gui.set_log_file(self.result_path)

        # Create title row for logged data
        TitleRow = ['Time']
        TitleRow.append('Step Number')
        TitleRow.append('Time left in step (min)')
        
        if self.have_watlow:
            TitleRow.append('Set Temperature (\N{DEGREE SIGN}C)')
            TitleRow.append('Read Temperature (\N{DEGREE SIGN}C)')
            TitleRow.append('Ramp Rate (\N{DEGREE SIGN}C/min)')
        
        # Add MFC names to title row
        if self.have_8comports:
            TitleRow.extend(self.mfc_names)
        else:
            TitleRow.extend(self.mfc_names[:4])
        
        if self.have_dosing:
            TitleRow.append('Valve Positions')
            TitleRow.append('Pressure (mbar)')
        
        if self.have_nitemperature:
            TitleRow.append('NI Temperature (\N{DEGREE SIGN}C)')
        
        self.File.writerow(TitleRow)   
        
        # Start the logging process
        time.sleep(0.5)
        self.ReadPVs()

    def update_sp_write_delay(self):
        """Reads the user input, validates it, and updates the global SP_WRITE_DELAY."""
        try:
            value = float(self.DelayEntry.get())
            self.SPWRITE_DELAY = value  # or directly set the global here
            print("Success", f"SP_WRITE_DELAY set to {value}")
            #print(SP_WRITE_DELAY)
        except ValueError:
            print("Invalid Input", "Please enter a numeric value for SP_WRITE_DELAY.")

    def CloseProgram(self):
        """Clean up and close the program"""
        if self.ProfileBool["text"] == "Profile is On":
                self.StartStop.invoke()
                time.sleep(0.5)
        
        if not getattr(self, 'closing', False):
            

            self.closing = True
            # Stop any running profile
            
            # Cancel any pending after callbacks
            if self.after_id is not None:        
                try:
                    self.master.after_cancel(self.after_id)
                except tkinter.TclError as e:
                    print(f"Error canceling scheduled callback: {e}")
                finally:
                    self.after_id = None
            
            # Wait for any device operations to complete
            try:
                with self.device_lock:
                    # Set all MFCs to zero
                    for i in range(4):
                        channel = i+1
                        try:
                            self.brooks1.WriteSP(channel, 0)
                            if self.have_8comports:
                                self.brooks2.WriteSP(channel, 0)
                        except Exception as e:
                            print(f"Error setting MFC to zero: {e}")
                    
                    # Turn off temperature control if enabled
                    if self.have_watlow:
                        try:
                            self.wt.ControlMode('Off')
                        except Exception as e:
                            print(f"Error turning off temperature control: {e}")
            except Exception as e:
                print(f"Error during device cleanup: {e}")
            
            # Close log file
            try:
                if self.LogFile is not None:
                    self.LogFile.close()
            except Exception as e:
                print(f"Error closing log file: {e}")
            
            # Close all device connections
            try:
                if self.have_watlow:
                    self.wt.CloseConnection()
                if self.have_nitemperature:
                    self.ni.CloseConnection()
                self.brooks1.CloseConnection()
                if self.have_8comports:
                    self.brooks2.CloseConnection()
                if self.have_dosing:
                    self.va.CloseConnection()
            except Exception as e:
                print(f"Error closing device connections: {e}")
            
            # Force destroy the window
            try:
                self.master.quit()  # Stop the mainloop
                self.master.destroy()  # Destroy the window
            except Exception as e:
                print(f"Error destroying window: {e}")
                # If normal destroy fails, try force quit
                import sys
                sys.exit(0)

    def WriteMFCSPButton1(self, channel):
        MFCValue = self.MFCInputButton1[channel-1].get()
        try: 
            MFCValue = float(MFCValue)         
            error_status = self.brooks1.WriteSP(channel, MFCValue)  # Get error status
            
            # Update the display color and tooltip based on error status
            if error_status:
                self.ReadFlowPart1[channel-1].config(bg='red')  # Highlight in red if error
                # Create tooltip for error
                tooltip_text = f"Error writing setpoint {MFCValue} to channel {channel}\nCHECK SP SIGNAL TYPE IN MFC CONFIGURATION"
                self.ReadFlowPart1[channel-1].bind('<Enter>', lambda e, text=tooltip_text: self.show_tooltip(e, text))
                self.ReadFlowPart1[channel-1].bind('<Leave>', self.hide_tooltip)
                
                # Log error to CSV file
                now = datetime.datetime.now()
                error_row = [now.strftime("%m/%d/%y %H:%M:%S"), "ERROR", "N/A", 
                           f"MFC1 Channel {channel} Setpoint Write Error", 
                           f"Attempted Value: {MFCValue}"]
                self.File.writerow(error_row)
            else:
                self.ReadFlowPart1[channel-1].config(bg='SystemButtonFace')  # Reset to default color
                # Remove tooltip bindings if they exist
                self.ReadFlowPart1[channel-1].unbind('<Enter>')
                self.ReadFlowPart1[channel-1].unbind('<Leave>')
            
            # Lets add logic to Detect glitches
            MFC_SP = self.brooks1.ReadSP(channel)
            SP_error = MFCValue - float(MFC_SP)
            logging.critical("SP_Error,  %s , %.2f, empty, %s", SP_error, SP_WRITE_DELAY, channel)
        except Exception as e:
            print("ERROR in Write MFC SP, probably not a number",e)
            self.ReadFlowPart1[channel-1].config(bg='yellow')  # Highlight in red if error
            # Create tooltip for invalid input error
            tooltip_text = f"Invalid input value: {MFCValue}"
            self.ReadFlowPart1[channel-1].bind('<Enter>', lambda e, text=tooltip_text: self.show_tooltip(e, text))
            self.ReadFlowPart1[channel-1].bind('<Leave>', self.hide_tooltip)
            
            # Log error to CSV file
            now = datetime.datetime.now()
            error_row = [now.strftime("%m/%d/%y %H:%M:%S"), "ERROR", "N/A", 
                       f"MFC1 Channel {channel} Invalid Input", 
                       f"Invalid Value: {MFCValue}"]
            self.File.writerow(error_row)

    def WriteMFCSPButton2(self, channel):
        MFCValue = self.MFCInputButton2[channel-1].get()
        try: 
            MFCValue = float(MFCValue)         
            error_status = self.brooks2.WriteSP(channel, MFCValue)  # Get error status
            
            # Update the display color and tooltip based on error status
            if error_status:
                self.ReadFlowPart2[channel-1].config(bg='red')  # Highlight in red if error
                # Create tooltip for error
                tooltip_text = f"Error writing setpoint {MFCValue} to channel {channel}"
                self.ReadFlowPart2[channel-1].bind('<Enter>', lambda e, text=tooltip_text: self.show_tooltip(e, text))
                self.ReadFlowPart2[channel-1].bind('<Leave>', self.hide_tooltip)
                
                # Log error to CSV file
                now = datetime.datetime.now()
                error_row = [now.strftime("%m/%d/%y %H:%M:%S"), "ERROR", "N/A", 
                           f"MFC2 Channel {channel} Setpoint Write Error", 
                           f"Attempted Value: {MFCValue}"]
                self.File.writerow(error_row)
            else:
                self.ReadFlowPart2[channel-1].config(bg='SystemButtonFace')  # Reset to default color
                # Remove tooltip bindings if they exist
                self.ReadFlowPart2[channel-1].unbind('<Enter>')
                self.ReadFlowPart2[channel-1].unbind('<Leave>')
            
        except:
            print("ERROR in Write MFC SP, probably not a number")
            self.ReadFlowPart2[channel-1].config(bg='red')  # Highlight in red if error
            # Create tooltip for invalid input error
            tooltip_text = f"Invalid input value: {MFCValue}"
            self.ReadFlowPart2[channel-1].bind('<Enter>', lambda e, text=tooltip_text: self.show_tooltip(e, text))
            self.ReadFlowPart2[channel-1].bind('<Leave>', self.hide_tooltip)
            
            # Log error to CSV file
            now = datetime.datetime.now()
            error_row = [now.strftime("%m/%d/%y %H:%M:%S"), "ERROR", "N/A", 
                       f"MFC2 Channel {channel} Invalid Input", 
                       f"Invalid Value: {MFCValue}"]
            self.File.writerow(error_row)

    def show_tooltip(self, event, text):
        """Create a tooltip for a given widget"""
        widget = event.widget
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        
        # Create a toplevel window
        self.tooltip = tkinter.Toplevel(widget)
        # Leaves only the label and removes the app window
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tkinter.Label(self.tooltip, text=text, justify='left',
                            background="#ffffe0", relief='solid', borderwidth=1,
                            font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        """Hide the tooltip"""
        if hasattr(self, 'tooltip'):
            self.tooltip.destroy()

    def WriteTempSPButton(self):
        if not self.have_watlow:
            return
        Tvalue = self.TempInputButton.get()
        RampRate = self.RampRateInputButton.get()
        try: 
            self.wt.WriteSP(float(Tvalue))
            self.wt.WriteRampRate(float(RampRate))
            self.SetPointPart.config(text = Tvalue)
            print('Wrote SP')
            self.TControlOff['text'] = 'T Control Off'
            self.TControlOff['bg'] = 'red'
        except Exception as e:
            print("ERROR in Write Temp SP, probably not a number: ", e )

    def ToggleWatlowControl(self):
        if not self.have_watlow:
            return
        print("ToggleWatlowControl")
        if self.TControlOff['text'] == 'T Control Off':
            self.wt.ControlMode('Off')
            self.TControlOff['text'] = 'T Control On'
            self.TControlOff['bg'] = 'green'
        else:
            self.wt.ControlMode('On')
            self.TControlOff['text'] = 'T Control Off'
            self.TControlOff['bg'] = 'red'

    def StartStop(self): #Starts the Profile
        if self.ProfileBool["text"]=="Profile is Off":
            try:
                self.ImportPorfile[0][0]
            except:
                print("Needs a Profile First")
                return
            try:
                self.ProfileBool["text"]="Profile is On"
                self.StartStop["text"]="STOP PROFILE"
                self.StartStop['bg']='red'
                self.StepNumber["text"]=1
                self.SkipStepBool=False
                self.StepEndTime=datetime.datetime.now()
                self.UpdateAllSetPointsInProfile()  
                self.TimeLeft["text"]='Not Reached Temp'
            except:
                print('Error in profile')
        elif self.ProfileBool["text"]=="Profile is On":
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
        if self.have_watlow:
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

    def UpdateGUIAfterReading(self):
        # --- Step 2: Log Data ---
        now = datetime.datetime.now()
        results = [now.strftime("%m/%d/%y %H:%M:%S")]
        results.append(self.StepNumber["text"])
        results.append(self.TimeLeft["text"])
        if self.have_watlow:
            results.append(self.SetPointPart['text'])  # the set point value
            results.append(str(self.watlow_temp))
            results.append(str(self.RampRateInputButton.get()))
        # Add MFC1 readings
        for value in self.mfc1_readings:
            results.append(str(value))
        # Add MFC2 readings if available
        if self.have_8comports:
            for value in self.mfc2_readings:
                results.append(str(value))
        # Add dosing and NI temperature data if available
        if self.have_dosing:
            results.append(str(self.dosing_state))
        if self.have_nitemperature:
            results.append(str(self.ni_temp))
        self.File.writerow(results)
        #print("Data logged.")
        # --- Step 3: Update GUI Elements ---
        # Update Brooks1 channel display labels
        for i in range(4):
            self.ReadFlowPart1[i].config(text=str(self.mfc1_readings[i]))
        # Update Brooks2 channels if available
        if self.have_8comports:
            for i in range(4):
                self.ReadFlowPart2[i].config(text=str(self.mfc2_readings[i]))
        # Update temperature displays
        if self.have_watlow:
            self.ReadTempPart.config(text=str(self.watlow_temp))
        if self.have_nitemperature:
            self.ReadNITemperaturePV.config(text=str(self.ni_temp))
        # Update dosing valve state display
        if self.have_dosing:
            self.ReadPosition.config(text=str(self.dosing_state))
        print("Succesfully read PVs and logged data")
        # --- Step 4: Process Profile and Dosing Logic ---
        if self.ProfileBool["text"] == "Profile is On":
            if self.ReachedTempBool == False:
                print('Waiting for Temperature')
                try:
                    if not self.have_watlow:
                        print("Watlow not enabled, skipping temperature check")
                        self.ReachedTempBool = True
                        minutesforstep = float(self.ImportPorfile[0][self.StepNumber["text"] - 1])
                        print(f"Waiting {minutesforstep} minutes for next step")
                        self.StepEndTime = datetime.datetime.now() + datetime.timedelta(minutes=minutesforstep)
                    # Check if temperature has been reached                    
                    elif abs(float(self.ReadTempPart['text']) - float(self.SetPointPart['text'])) < 1:
                        self.ReachedTempBool = True
                        # Start the timer for this step
                        minutesforstep = float(self.ImportPorfile[0][self.StepNumber["text"] - 1])
                        print(f"Waiting {minutesforstep} minutes for next step")
                        self.StepEndTime = datetime.datetime.now() + datetime.timedelta(minutes=minutesforstep)
                except Exception as e:
                    print("Error in reading temperature: ", e)
            if self.SkipStepBool or ((datetime.datetime.now() > self.StepEndTime) and self.ReachedTempBool):
                self.SkipStepBool = False
                print('Moving to Next Step :', self.StepNumber["text"] )
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
        if self.have_dosing:
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
        self.after_id = self.label.after(3000, self.ReadPVs)

    def UpdateAllSetPointsInProfile(self):
        # Update GUI elements in main thread
        for j in range(4):
            channel = j+1
            ColIndex = j+3 if self.have_watlow else j+1
            value = self.ImportPorfile[ColIndex][self.StepNumber["text"]-1]
            self.MFCInputButton1[j].delete(0,"end")
            self.MFCInputButton1[j].insert(0, value)
        
        if self.have_8comports:
            for j in range(4):
                channel = j+1
                ColIndex = j+3+4
                value = self.ImportPorfile[ColIndex][self.StepNumber["text"]-1]
                self.MFCInputButton2[j].delete(0,"end")
                self.MFCInputButton2[j].insert(0, value)
        
        if self.have_watlow:        
            temp = self.ImportPorfile[1][self.StepNumber["text"]-1]
            ramprate = self.ImportPorfile[2][self.StepNumber["text"]-1]
            self.TempInputButton.delete(0,"end")
            self.TempInputButton.insert(0,temp)
            self.RampRateInputButton.delete(0,"end")
            self.RampRateInputButton.insert(0,ramprate) 
            self.SetPointPart.config(text=temp)

        # Start background thread for device updates
        if not getattr(self, 'closing', False):
            threading.Thread(target=self._update_devices_in_background, daemon=True).start()
            print('Set Points Updated')

    def _update_devices_in_background(self):
        """Helper method to update device setpoints in background thread"""
        if getattr(self, 'closing', False):
            return
            
        try:
            with self.device_lock:  # Acquire lock before device communication
                # Update MFC1
                for j in range(4):
                    if getattr(self, 'closing', False):
                        return
                    channel = j+1
                    self.WriteMFCSPButton1(channel)
                
                # Update MFC2 if enabled
                if self.have_8comports:
                    for j in range(4):
                        if getattr(self, 'closing', False):
                            return
                        channel = j+1
                        self.WriteMFCSPButton2(channel)
                
                # Update Watlow if enabled
                if self.have_watlow:
                    if not getattr(self, 'closing', False):
                        self.WriteTempSPButton()
                    
        except Exception as e:
            logging.error("Error updating device setpoints: %s", str(e))

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
        self.va.SetToStateA()
        self.ReadValvePosition["text"] = self.va.ReadState()
        
    def SetPosB(self):
        self.va.SetToStateB()
        self.ReadValvePosition["text"] = self.va.ReadState()
        
    def DoseStartStop(self): #Starts the Dosing Profile            
        if self.DoseBool["text"]=="Dosing is Off":
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
                if "CPA" in self.ReadValvePosition["text"]:
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
                    self.DoseEndTime=datetime.datetime.now()+datetime.timedelta(minutes=minutesfordose)
                except:
                    print('Error in dose')
        elif self.DoseBool["text"]=="Dosing is On":
            self.EndDosing()
        else:
            print("Dose is broken ]':")

    def EndDosing(self):
        self.DoseBool["text"]="Dosing is Off"
        self.DoseStartStop["text"]="Start Dosing"
        self.DoseStartStop['bg']='SystemButtonFace'
        self.DoseNumber["text"]="Not Dosing"
        self.DoseTimeLeft["text"]='N/A'

    def GoToStep(self):
        """Moves the profile to a specific step number."""
        try:
            # Check if profile is loaded and running
            if self.ProfileBool["text"] != "Profile is On":
                print("Profile must be running to move to a specific step")
                return

            # Get and validate the target step
            target_step = int(self.GoToStepEntry.get())
            if target_step < 1:
                print("Step number must be positive")
                return

            try:
                # Verify the step exists in the profile
                self.ImportPorfile[0][target_step - 1]
            except:
                print("Step number exceeds profile length")
                return

            # Update step number and reset temperature check
            self.StepNumber["text"] = target_step
            self.ReachedTempBool = False
            self.TimeLeft["text"] = 'Not Reached Temp'
            
            # Update all setpoints for the new step
            self.UpdateAllSetPointsInProfile()
            
            # Log the manual step change
            now = time.strftime("%Y-%m-%d_%H-%M-%S")
            logging.critical("Manually moved to step %d at %s", target_step, now)
            
        except ValueError:
            print("Please enter a valid step number")
        except Exception as e:
            print(f"Error moving to step: {e}")