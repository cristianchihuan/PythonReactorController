import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from config.settings import (
    DefaultMFC1ComPort, DefaultMFC2ComPort, DefaultWatlowComPort,
    DefaultViciComPort, DefaultNIComPort, TITTLE
)

class ConfigurationGui:
    def __init__(self, master):
        self.master = master
        master.title("Configuration Parameters")
        
        # Set default font size
        default_font = ('TkDefaultFont', 10)
        self.master.option_add('*Font', default_font)
        self.master.option_add('*Entry.Font', default_font)
        self.master.option_add('*Button.Font', default_font)
        self.master.option_add('*Label.Font', default_font)
        
        # Configure grid layout
        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)
        
        # Initialize configuration flags
        self.have_8comports = tk.BooleanVar(value=True)
        self.have_temperature = tk.BooleanVar(value=True)
        self.have_dosing = tk.BooleanVar(value=False)
        self.have_nitemperature = tk.BooleanVar(value=True)
        self.enable_error_logger = tk.BooleanVar(value=True)
        
        # Create main frames
        self.mfc_frame = tk.LabelFrame(master, text="MFC Port Names", padx=10, pady=10)
        self.mfc_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
        
        self.default_COM_ports = tk.LabelFrame(master, text="Default COM Ports", padx=10, pady=10)
        self.default_COM_ports.grid(row=0, column=2, columnspan=2, padx=10, pady=10, sticky='nsew')
        
        # Create MFC port name entries
        self.mfc_names_entries = []
        for i in range(8):
            label = tk.Label(self.mfc_frame, text=f"MFC Port {i+1} Name:")
            label.grid(row=i, column=0, sticky="e", padx=5, pady=2)
            entry = tk.Entry(self.mfc_frame)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.mfc_names_entries.append(entry)
            if i >= 4 and not self.have_8comports.get():
                entry.config(state="disabled")
        
        # Create COM port entries
        com_ports = [
            ("MFC 1 Com Port", "DefaultMFC1ComPort", DefaultMFC1ComPort),
            ("MFC 2 Com Port", "DefaultMFC2ComPort", DefaultMFC2ComPort),
            ("Watlow Com Port", "DefaultWatlowComPort", DefaultWatlowComPort),
            ("NI Com Port", "DefaultNIComPort", DefaultNIComPort),
            ("Vici Com Port", "DefaultViciComPort", DefaultViciComPort)
        ]
        
        self.com_port_entries = {}
        for i, (label_text, var_name, default_value) in enumerate(com_ports):
            label = tk.Label(self.default_COM_ports, text=label_text)
            label.grid(row=i, column=0, padx=5, pady=2)
            entry = tk.Entry(self.default_COM_ports, width=10)
            entry.grid(row=i, column=1, padx=5, pady=2)
            entry.insert(0, default_value)
            self.com_port_entries[var_name] = entry
        
        # Configuration checkboxes
        self.chk_8com = tk.Checkbutton(master, text="Have 8 Com Ports?", 
                                     variable=self.have_8comports,
                                     command=self.toggle_mfc_fields)
        self.chk_8com.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        self.chk_temp = tk.Checkbutton(master, text="Have Temperature Controller?", 
                                     variable=self.have_temperature)
        self.chk_temp.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        
        self.chk_dosing = tk.Checkbutton(master, text="Have Dosing Controller?", 
                                       variable=self.have_dosing)
        self.chk_dosing.grid(row=3, column=0, sticky="w", padx=10, pady=5)
        
        self.chk_nitemp = tk.Checkbutton(master, text="Have NI Temperature?", 
                                       variable=self.have_nitemperature)
        self.chk_nitemp.grid(row=4, column=0, sticky="w", padx=10, pady=5)
        
        self.chk_error_logger = tk.Checkbutton(master, text="Enable Error Logger?", 
                                             variable=self.enable_error_logger)
        self.chk_error_logger.grid(row=5, column=0, sticky="w", padx=10, pady=5)
        
        # Title entry
        self.title_label = tk.Label(master, text="Title")
        self.title_label.grid(row=6, column=0)
        self.title_entry = tk.Entry(master, width=25)
        self.title_entry.grid(row=6, column=1)
        self.title_entry.insert(0, TITTLE)
        
        # Buttons
        self.save_button = tk.Button(master, text="Save Configuration", 
                                   command=self.save_configuration,
                                   bg='#90EE90')
        self.save_button.grid(row=7, column=0, columnspan=1, padx=10, pady=10)
        
        self.upload_button = tk.Button(master, text="Upload Configuration", 
                                     command=self.upload_configuration,
                                     bg='#90EE90')
        self.upload_button.grid(row=7, column=1, columnspan=2, padx=10, pady=10)
        
        # Initialize configuration dictionary
        self.configuration = {}
        
        # Set default MFC labels
        default_labels = ['H2', 'He', 'O2', 'C2H4', 'Empty', 'Empty', 'C2H4', 'Empty']
        for i, label in enumerate(default_labels):
            self.mfc_names_entries[i].insert(0, label)

    def toggle_mfc_fields(self):
        """Enables or disables the extra MFC port name entry fields (ports 5-8)"""
        if self.have_8comports.get():
            for i in range(4, 8):
                self.mfc_names_entries[i].config(state="normal")
        else:
            for i in range(4, 8):
                self.mfc_names_entries[i].delete(0, tk.END)
                self.mfc_names_entries[i].config(state="disabled")

    def get_configuration(self):
        """Returns the current configuration as a dictionary"""
        if not hasattr(self, 'configuration') or not self.configuration:
            if self.have_8comports.get():
                mfc_names = [entry.get() for entry in self.mfc_names_entries]
            else:
                mfc_names = [entry.get() for entry in self.mfc_names_entries[:4]]
            
            self.configuration = {
                'Have8ComPorts': self.have_8comports.get(),
                'HaveWatlow': self.have_temperature.get(),
                'HaveDosing': self.have_dosing.get(),
                'HaveNITemperature': self.have_nitemperature.get(),
                'EnableErrorLogger': self.enable_error_logger.get(),
                'MFCNames': mfc_names,
                'DefaultMFC1ComPort': self.com_port_entries['DefaultMFC1ComPort'].get(),
                'DefaultMFC2ComPort': self.com_port_entries['DefaultMFC2ComPort'].get(),
                'DefaultWatlowComPort': self.com_port_entries['DefaultWatlowComPort'].get(),
                'DefaultViciComPort': self.com_port_entries['DefaultViciComPort'].get(),
                'DefaultNIComPort': self.com_port_entries['DefaultNIComPort'].get(),
                'Tittle': self.title_entry.get()
            }
        return self.configuration

    def save_configuration(self):
        """Collects and saves the configuration parameters"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                # Get configuration before destroying window
                self.configuration = self.get_configuration()
                with open(filename, 'w') as f:
                    for key, value in self.configuration.items():
                        if isinstance(value, list):
                            f.write(f"{key}={','.join(value)}\n")
                        else:
                            f.write(f"{key}={value}\n")
                messagebox.showinfo("Success", "Configuration saved successfully!")
                self.master.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")

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
            
            # Update GUI elements based on the new configuration
            if 'Have8ComPorts' in new_config:
                self.have_8comports.set(new_config['Have8ComPorts'].lower() == 'true')
            if 'HaveWatlow' in new_config:
                self.have_temperature.set(new_config['HaveWatlow'].lower() == 'true')
            if 'HaveDosing' in new_config:
                self.have_dosing.set(new_config['HaveDosing'].lower() == 'true')
            if 'HaveNITemperature' in new_config:
                self.have_nitemperature.set(new_config['HaveNITemperature'].lower() == 'true')
            if 'EnableErrorLogger' in new_config:
                self.enable_error_logger.set(new_config['EnableErrorLogger'].lower() == 'true')
            
            # Update MFC names
            if 'MFCNames' in new_config:
                mfc_names = new_config['MFCNames']
                for i, name in enumerate(mfc_names):
                    if i < len(self.mfc_names_entries):
                        self.mfc_names_entries[i].delete(0, tk.END)
                        self.mfc_names_entries[i].insert(0, name)
            
            # Update COM ports
            for key in ['DefaultMFC1ComPort', 'DefaultMFC2ComPort', 'DefaultWatlowComPort',
                       'DefaultViciComPort', 'DefaultNIComPort']:
                if key in new_config:
                    self.com_port_entries[key].delete(0, tk.END)
                    self.com_port_entries[key].insert(0, new_config[key])
            
            # Update title
            if 'Tittle' in new_config:
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, new_config['Tittle'])
            
            # Ensure the extra fields are toggled correctly.
            self.toggle_mfc_fields()
            
            messagebox.showinfo("Success", "Configuration uploaded successfully!")
            self.master.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload configuration: {e}") 