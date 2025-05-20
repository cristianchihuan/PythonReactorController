import tkinter
from tkinter import ttk
from config.settings import SP_OUTPUT_PORT_SIGNAL_TYPES

class MFCConfigGUI:
    def __init__(self, parent, brooks1, brooks2=None, have_8comports=False, mfc_names=None):
        self.parent = parent
        self.brooks1 = brooks1
        self.brooks2 = brooks2
        self.have_8comports = have_8comports
        self.mfc_names = mfc_names or []

        # Create a canvas with scrollbar for the entire tab
        self.config_canvas = tkinter.Canvas(parent)
        self.config_scrollbar = tkinter.Scrollbar(parent, orient="vertical", command=self.config_canvas.yview)
        self.config_canvas.configure(yscrollcommand=self.config_scrollbar.set)
        
        # Layout scrollbar and canvas
        self.config_scrollbar.pack(side="right", fill="y")
        self.config_canvas.pack(side="left", fill="both", expand=True)
        
        # Create main frame inside canvas
        self.config_frame = tkinter.Frame(self.config_canvas)
        self.config_canvas.create_window((0, 0), window=self.config_frame, anchor="nw")

        # Create frames for MFC1 and MFC2 (if enabled)
        self.mfc1_config_frame = tkinter.LabelFrame(self.config_frame, text="MFC 1 Configuration", padx=10, pady=10)
        self.mfc1_config_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        if self.have_8comports:
            self.mfc2_config_frame = tkinter.LabelFrame(self.config_frame, text="MFC 2 Configuration", padx=10, pady=10)
            self.mfc2_config_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

        # Initialize dictionaries for storing GUI elements
        self.mfc1_signal_labels = {}
        self.mfc1_signal_values = {}
        self.mfc1_signal_combos = {}
        self.mfc1_config_values = {}
        
        if self.have_8comports:
            self.mfc2_signal_labels = {}
            self.mfc2_signal_values = {}
            self.mfc2_signal_combos = {}
            self.mfc2_config_values = {}

        # Build the GUI elements
        self._build_mfc1_config()
        if self.have_8comports:
            self._build_mfc2_config()

        # Configure scrolling
        self.config_frame.bind("<Configure>", self._on_config_frame_configure)

    def _on_config_frame_configure(self, event):
        """Handle configuration frame resize"""
        self.config_canvas.configure(scrollregion=self.config_canvas.bbox("all"))

    def _build_mfc1_config(self):
        """Build the MFC1 configuration interface"""
        for i in range(4):
            # Channel frame
            channel_frame = tkinter.LabelFrame(self.mfc1_config_frame, text=f"{self.mfc_names[i]} (Channel {i+1})")
            channel_frame.grid(row=i, column=0, columnspan=4, padx=5, pady=5, sticky='nsew')
            
            # Create notebook for SP and PV configs
            config_notebook = ttk.Notebook(channel_frame)
            config_notebook.grid(row=0, column=0, columnspan=4, padx=5, pady=2, sticky='nsew')
            
            # SP Configuration tab
            sp_frame = ttk.Frame(config_notebook)
            config_notebook.add(sp_frame, text='SP Config')
            
            self.mfc1_config_values[i] = {}
            self.mfc1_signal_combos[i] = None
            
            # First handle SP Signal Type specially with combo box and write button
            tkinter.Label(sp_frame, text="SP Signal Type:").grid(row=0, column=0, padx=5, pady=2, sticky='e')
            value_frame = tkinter.Frame(sp_frame)
            value_frame.grid(row=0, column=1, padx=5, pady=2, sticky='w')
            
            value_label = tkinter.Label(value_frame, text="Not Read")
            value_label.pack(side='left')
            self.mfc1_config_values[i]['SP Signal Type'] = value_label
            
            combo = ttk.Combobox(value_frame, values=list(SP_OUTPUT_PORT_SIGNAL_TYPES.values()), width=15)
            combo.pack(side='left', padx=5)
            self.mfc1_signal_combos[i] = combo
            
            write_btn = tkinter.Button(value_frame, text="Write", command=lambda ch=i+1: self.write_mfc1_signal_type(ch), bg='#90EE90')
            write_btn.pack(side='left')
            
            # Then handle all other SP config items
            sp_config_items = ['SP Full Scale', 'SP Function', 'SP Rate', 
                          'SP VOR', 'SP Batch', 'SP Blend', 'SP Source']
            for j, item in enumerate(sp_config_items):
                row = j + 1
                tkinter.Label(sp_frame, text=f"{item}:").grid(row=row//2, column=row%2*2, padx=5, pady=2, sticky='e')
                value_label = tkinter.Label(sp_frame, text="Not Read")
                value_label.grid(row=row//2, column=row%2*2+1, padx=5, pady=2, sticky='w')
                self.mfc1_config_values[i][item] = value_label

            # PV Configuration tab
            pv_frame = ttk.Frame(config_notebook)
            config_notebook.add(pv_frame, text='PV Config')
            
            # Add PV configuration items
            pv_config_items = ['Measure Units', 'Time Base', 'Decimal Point', 
                             'Gas Factor', 'Log Type', 'PV Signal Type', 'PV Full Scale']
            for j, item in enumerate(pv_config_items):
                tkinter.Label(pv_frame, text=f"{item}:").grid(row=j//2, column=j%2*2, padx=5, pady=2, sticky='e')
                value_label = tkinter.Label(pv_frame, text="Not Read")
                value_label.grid(row=j//2, column=j%2*2+1, padx=5, pady=2, sticky='w')
                self.mfc1_config_values[i][item] = value_label

        # Read buttons frame
        button_frame = tkinter.Frame(self.mfc1_config_frame)
        button_frame.grid(row=4, column=0, columnspan=4, pady=10)
        
        self.read_mfc1_sp_config_button = tkinter.Button(button_frame, text="Read SP Config", 
                                                command=self.read_mfc1_config, bg='#90EE90')
        self.read_mfc1_sp_config_button.grid(row=0, column=0, padx=5)
        
        self.read_mfc1_pv_config_button = tkinter.Button(button_frame, text="Read PV Config", 
                                                command=self.read_mfc1_pv_config, bg='#90EE90')
        self.read_mfc1_pv_config_button.grid(row=0, column=1, padx=5)

    def _build_mfc2_config(self):
        """Build the MFC2 configuration interface"""
        if not self.have_8comports:
            return
            
        for i in range(4):
            # Channel frame
            channel_frame = tkinter.LabelFrame(self.mfc2_config_frame, text=f"{self.mfc_names[i+4]} (Channel {i+1})")
            channel_frame.grid(row=i, column=0, columnspan=4, padx=5, pady=5, sticky='nsew')
            
            # Create notebook for SP and PV configs
            config_notebook = ttk.Notebook(channel_frame)
            config_notebook.grid(row=0, column=0, columnspan=4, padx=5, pady=2, sticky='nsew')
            
            # SP Configuration tab
            sp_frame = ttk.Frame(config_notebook)
            config_notebook.add(sp_frame, text='SP Config')
            
            self.mfc2_config_values[i] = {}
            self.mfc2_signal_combos[i] = None
            
            # First handle SP Signal Type specially with combo box and write button
            tkinter.Label(sp_frame, text="SP Signal Type:").grid(row=0, column=0, padx=5, pady=2, sticky='e')
            value_frame = tkinter.Frame(sp_frame)
            value_frame.grid(row=0, column=1, padx=5, pady=2, sticky='w')
            
            value_label = tkinter.Label(value_frame, text="Not Read")
            value_label.pack(side='left')
            self.mfc2_config_values[i]['SP Signal Type'] = value_label
            
            combo = ttk.Combobox(value_frame, values=list(SP_OUTPUT_PORT_SIGNAL_TYPES.values()), width=15)
            combo.pack(side='left', padx=5)
            self.mfc2_signal_combos[i] = combo
            
            write_btn = tkinter.Button(value_frame, text="Write", command=lambda ch=i+1: self.write_mfc2_signal_type(ch), bg='#90EE90')
            write_btn.pack(side='left')
            
            # Then handle all other SP config items
            sp_config_items = ['SP Full Scale', 'SP Function', 'SP Rate', 
                          'SP VOR', 'SP Batch', 'SP Blend', 'SP Source']
            for j, item in enumerate(sp_config_items):
                row = j + 1
                tkinter.Label(sp_frame, text=f"{item}:").grid(row=row//2, column=row%2*2, padx=5, pady=2, sticky='e')
                value_label = tkinter.Label(sp_frame, text="Not Read")
                value_label.grid(row=row//2, column=row%2*2+1, padx=5, pady=2, sticky='w')
                self.mfc2_config_values[i][item] = value_label

            # PV Configuration tab
            pv_frame = ttk.Frame(config_notebook)
            config_notebook.add(pv_frame, text='PV Config')
            
            # Add PV configuration items
            pv_config_items = ['Measure Units', 'Time Base', 'Decimal Point', 
                             'Gas Factor', 'Log Type', 'PV Signal Type', 'PV Full Scale']
            for j, item in enumerate(pv_config_items):
                tkinter.Label(pv_frame, text=f"{item}:").grid(row=j//2, column=j%2*2, padx=5, pady=2, sticky='e')
                value_label = tkinter.Label(pv_frame, text="Not Read")
                value_label.grid(row=j//2, column=j%2*2+1, padx=5, pady=2, sticky='w')
                self.mfc2_config_values[i][item] = value_label

        # Read buttons for MFC2
        button_frame = tkinter.Frame(self.mfc2_config_frame)
        button_frame.grid(row=4, column=0, columnspan=4, pady=10)
        
        self.read_mfc2_config_button = tkinter.Button(button_frame, text="Read SP Config", 
                                                command=self.read_mfc2_config, bg='#90EE90')
        self.read_mfc2_config_button.grid(row=0, column=0, padx=5)
        
        self.read_mfc2_pv_config_button = tkinter.Button(button_frame, text="Read PV Config", 
                                                command=self.read_mfc2_pv_config, bg='#90EE90')
        self.read_mfc2_pv_config_button.grid(row=0, column=1, padx=5)

    def read_mfc1_config(self):
        """Read and display SP configuration for all channels in MFC1"""
        for channel in range(1, 5):
            try:
                config = self.brooks1.ReadSPCONFIG(channel)
                if config:
                    for key, value in config.items():
                        if key != 'Signal Type' and key in self.mfc1_config_values[channel-1]:
                            self.mfc1_config_values[channel-1][key].config(text=value)
            except Exception as e:
                print(f"Error reading SP config for channel {channel}: {str(e)}")

    def read_mfc2_config(self):
        """Read and display SP configuration for all channels in MFC2"""
        if not self.have_8comports:
            return
        for channel in range(1, 5):
            try:
                config = self.brooks2.ReadSPCONFIG(channel)
                if config:
                    for key, value in config.items():
                        if key != 'Signal Type' and key in self.mfc2_config_values[channel-1]:
                            self.mfc2_config_values[channel-1][key].config(text=value)
            except Exception as e:
                print(f"Error reading SP config for channel {channel}: {str(e)}")

    def write_mfc1_signal_type(self, channel):
        """Write signal type for a channel in MFC1"""
        try:
            selected_type = self.mfc1_signal_combos[channel-1].get()
            if not selected_type:
                print("Please select a signal type first")
                return
                
            new_type = self.brooks1.WriteSPSignalType(channel, selected_type)
            if new_type:
                self.mfc1_config_values[channel-1]['SP Signal Type'].config(text=new_type)
                print(f"Successfully wrote signal type {new_type} to channel {channel}")
            else:
                print(f"Failed to write signal type to channel {channel}")
        except ValueError:
            pass
        except Exception as e:
            print(f"Error writing signal type: {str(e)}")

    def write_mfc2_signal_type(self, channel):
        """Write signal type for a channel in MFC2"""
        if not self.have_8comports:
            return
        try:
            selected_type = self.mfc2_signal_combos[channel-1].get()
            if not selected_type:
                print("Please select a signal type first")
                return
                
            new_type = self.brooks2.WriteSPSignalType(channel, selected_type)
            if new_type:
                self.mfc2_signal_values[channel-1].config(text=new_type)
                print(f"Successfully wrote signal type {new_type} to channel {channel}")
            else:
                print(f"Failed to write signal type to channel {channel}")
        except Exception as e:
            print(f"Error writing signal type: {str(e)}")

    def read_mfc1_pv_config(self):
        """Read and display PV configuration for all channels in MFC1"""
        for channel in range(1, 5):
            try:
                config = self.brooks1.ReadPVCONFIG(channel)
                if config:
                    for key, value in config.items():
                        if key in self.mfc1_config_values[channel-1]:
                            self.mfc1_config_values[channel-1][key].config(text=value)
            except Exception as e:
                print(f"Error reading PV config for channel {channel}: {str(e)}")

    def read_mfc2_pv_config(self):
        """Read and display PV configuration for all channels in MFC2"""
        if not self.have_8comports:
            return
        for channel in range(1, 5):
            try:
                config = self.brooks2.ReadPVCONFIG(channel)
                if config:
                    for key, value in config.items():
                        if key in self.mfc2_config_values[channel-1]:
                            self.mfc2_config_values[channel-1][key].config(text=value)
            except Exception as e:
                print(f"Error reading PV config for channel {channel}: {str(e)}") 