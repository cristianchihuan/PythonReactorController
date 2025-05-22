import tkinter
from tkinter import filedialog, ttk
from tkcalendar import DateEntry  # <-- Add this import (requires tkcalendar)
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy
import time
import matplotlib.dates as mdates
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import style
import pandas as pd

class HistoricalPlotWindow:
    def __init__(self, parent, mfc_names=None, log_file_path=None):
        self.window = tkinter.Toplevel(parent)
        self.window.title("Historical Data Plot")
        self.window.geometry("900x650")
        
        self.mfc_names = mfc_names or []
        self.log_file_path = log_file_path
        
        # Create main frame
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create control frame
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill='x', pady=(0, 10))
        
        # Add instrument selection
        self.instrument_var = tkinter.StringVar()
        self.instrument_combo = ttk.Combobox(self.control_frame, textvariable=self.instrument_var)
        self.instrument_combo.pack(side='left', padx=5)
        self.instrument_combo.bind('<<ComboboxSelected>>', self.update_plot)
        
        # --- Preset Range Dropdown ---
        self.preset_var = tkinter.StringVar(value="Last 1 hour")
        self.preset_options = [
            "All data",
            "Last 10 minutes",
            "Last 1 hour",
            "Last 6 hours",
            "Last 24 hours",
            "Custom"
        ]
        ttk.Label(self.control_frame, text="Time Range:").pack(side='left', padx=(15,2))
        self.preset_combo = ttk.Combobox(self.control_frame, textvariable=self.preset_var, values=self.preset_options, state="readonly", width=15)
        self.preset_combo.pack(side='left', padx=2)
        self.preset_combo.bind('<<ComboboxSelected>>', self.on_preset_change)
        
        # --- Custom Range Frame ---
        self.custom_frame = ttk.Frame(self.control_frame)
        # Start date/time
        ttk.Label(self.custom_frame, text="From:").pack(side='left')
        self.start_date = DateEntry(self.custom_frame, width=10, date_pattern='y-mm-dd')
        self.start_date.pack(side='left', padx=2)
        self.start_time_var = tkinter.StringVar(value="00:00:00")
        self.start_time_entry = ttk.Entry(self.custom_frame, textvariable=self.start_time_var, width=8)
        self.start_time_entry.pack(side='left', padx=2)
        # End date/time
        ttk.Label(self.custom_frame, text="To:").pack(side='left')
        self.end_date = DateEntry(self.custom_frame, width=10, date_pattern='y-mm-dd')
        self.end_date.pack(side='left', padx=2)
        self.end_time_var = tkinter.StringVar(value="23:59:59")
        self.end_time_entry = ttk.Entry(self.custom_frame, textvariable=self.end_time_var, width=8)
        self.end_time_entry.pack(side='left', padx=2)
        
        # Add refresh button
        self.refresh_button = ttk.Button(self.control_frame, text="Refresh", command=self.refresh_data)
        self.refresh_button.pack(side='left', padx=5)
        
        # Create plot frame
        self.plot_frame = ttk.Frame(self.main_frame)
        self.plot_frame.pack(fill='both', expand=True)
        
        # Create figure and canvas
        self.fig = Figure(figsize=(8, 6))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Initialize data
        self.data = None
        self.time_column = None
        
        # Load data if log file path is provided
        if self.log_file_path:
            self.load_data()
            self.update_custom_range_fields()
            self.on_preset_change()
        
    def on_preset_change(self, event=None):
        if self.preset_var.get() == "Custom":
            self.custom_frame.pack(side='left', padx=10)
        else:
            self.custom_frame.pack_forget()
        self.update_plot()

    def update_custom_range_fields(self):
        if self.data is not None:
            times = pd.to_datetime(self.data[self.time_column], format='%m/%d/%y %H:%M:%S', errors='coerce')
            min_dt = times.min()
            max_dt = times.max()
            self.start_date.set_date(min_dt.date())
            self.end_date.set_date(max_dt.date())
            self.start_time_var.set(min_dt.strftime('%H:%M:%S'))
            self.end_time_var.set(max_dt.strftime('%H:%M:%S'))

    def get_time_range(self):
        if self.data is None:
            return None, None
        times = pd.to_datetime(self.data[self.time_column], format='%m/%d/%y %H:%M:%S', errors='coerce')
        preset = self.preset_var.get()
        if preset == "All data":
            return times.min(), times.max()
        elif preset == "Last 10 minutes":
            end_time = times.max()
            start_time = end_time - pd.Timedelta(minutes=10)
            return start_time, end_time
        elif preset == "Last 1 hour":
            end_time = times.max()
            start_time = end_time - pd.Timedelta(hours=1)
            return start_time, end_time
        elif preset == "Last 6 hours":
            end_time = times.max()
            start_time = end_time - pd.Timedelta(hours=6)
            return start_time, end_time
        elif preset == "Last 24 hours":
            end_time = times.max()
            start_time = end_time - pd.Timedelta(hours=24)
            return start_time, end_time
        elif preset == "Custom":
            try:
                start_str = f"{self.start_date.get()} {self.start_time_var.get()}"
                end_str = f"{self.end_date.get()} {self.end_time_var.get()}"
                start_time = pd.to_datetime(start_str, format='%Y-%m-%d %H:%M:%S', errors='coerce')
                end_time = pd.to_datetime(end_str, format='%Y-%m-%d %H:%M:%S', errors='coerce')
                return start_time, end_time
            except Exception:
                return times.min(), times.max()
        else:
            return times.min(), times.max()

    def load_data(self):
        try:
            # Store current selection before reloading
            current_selection = self.instrument_var.get()
            
            # Try reading with utf-8 first
            try:
                self.data = pd.read_csv(self.log_file_path, encoding='utf-8')
            except UnicodeDecodeError:
                # Fallback to latin1 if utf-8 fails
                self.data = pd.read_csv(self.log_file_path, encoding='latin1')
            # Get column names for instrument selection
            columns = self.data.columns.tolist()
            self.time_column = columns[0]  # First column is time
            # Filter out non-data columns
            data_columns = [col for col in columns if col not in ['Time', 'Step Number', 'Time left in step (min)']]
            # Update instrument combo box
            self.instrument_combo['values'] = data_columns
            
            # Restore previous selection if it still exists in the new data
            if current_selection in data_columns:
                self.instrument_combo.set(current_selection)
            elif data_columns:  # If previous selection not available, use first item
                self.instrument_combo.set(data_columns[0])
                
            self.update_custom_range_fields()
            self.update_plot()
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"Error loading data: {str(e)}")

    def refresh_data(self):
        self.load_data()

    def update_plot(self, event=None):
        if self.data is None or self.instrument_var.get() == "":
            return
        self.ax.clear()
        times = pd.to_datetime(self.data[self.time_column], format='%m/%d/%y %H:%M:%S', errors='coerce')
        values = self.data[self.instrument_var.get()]
        start_time, end_time = self.get_time_range()
        if start_time and end_time:
            mask = (times >= start_time) & (times <= end_time)
            times = times[mask]
            values = values[mask]
        self.ax.plot(times, values, 'b-')
        self.ax.set_title(f"{self.instrument_var.get()} vs Time")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel(self.instrument_var.get())
        self.ax.grid(True)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.fig.autofmt_xdate()
        self.canvas.draw()

class PlotsGUI:
    def __init__(self, parent, have_8comports=False, have_watlow=False, have_nitemperature=False, mfc_names=None):
        # Set a modern style
        plt.style.use('bmh')  # Using a built-in style
        
        self.parent = parent
        self.have_8comports = have_8comports
        self.have_watlow = have_watlow
        self.have_nitemperature = have_nitemperature
        self.mfc_names = mfc_names or []
        self.current_log_file = None

        # Add button for historical plots
        self.hist_button = ttk.Button(parent, text="Open Historical Plot", 
                                    command=self.open_historical_plot)
        self.hist_button.pack(side='top', pady=5)

        # determine which channels to plot 
        self.plot_keys = []
        for ch in range(1, 5):
            self.plot_keys.append(f"MFC1-{ch}")
        if self.have_watlow:
            self.plot_keys.append("WATLOW")    
        if self.have_8comports:
            for ch in range(1, 5):
                self.plot_keys.append(f"MFC2-{ch}")
        
        if self.have_nitemperature:
            self.plot_keys.append("NI")

        n = len(self.plot_keys)
        cols = 5
        rows = (n + cols - 1) // cols

        # Create figure with a light background
        fig = Figure(figsize=(cols * 2.5, rows * 2.5), facecolor='#f8f9fa')
        self.axes = {}
        self.lines = {}
        self.setpoint = {}

        # Define a color palette
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']

        for idx, key in enumerate(self.plot_keys):
            ax = fig.add_subplot(rows, cols, idx + 1)
            ax.set_facecolor('#ffffff')
            
            # Set title with better formatting
            if key.startswith("MFC1"):
                ch = int(key.split("-")[1])
                ax.set_title(f"{self.mfc_names[ch-1]} (sccm)", pad=10, fontsize=10, fontweight='bold')
            elif key.startswith("MFC2"):
                ch = int(key.split("-")[1])
                ax.set_title(f"{self.mfc_names[ch+3]} (sccm)", pad=10, fontsize=10, fontweight='bold')
            else:
                ax.set_title(key, pad=10, fontsize=10, fontweight='bold')
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            ax.set_xlabel("Time", fontsize=8)
            ax.tick_params(axis='x', rotation=45, labelsize=8)
            ax.tick_params(axis='y', labelsize=8)
            
            # Add grid
            ax.grid(True, linestyle='--', alpha=0.3)
            
            # Set spine colors
            for spine in ax.spines.values():
                spine.set_color('#cccccc')
            
            self.axes[key] = ax
            # Use different colors for each line
            color = colors[idx % len(colors)]
            self.lines[key], = ax.plot([], [], color=color, linewidth=2, marker='o', markersize=3, alpha=0.8)

        # --- add spacing ---
        fig.tight_layout(pad=2.0)

        self.time_buffer = []
        self.data_buffer = {k: [] for k in self.plot_keys}
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas = canvas

    def set_log_file(self, log_file_path):
        """Set the current log file path"""
        self.current_log_file = log_file_path
        
    def open_historical_plot(self):
        """Open a new window for historical data plotting"""
        if self.current_log_file:
            HistoricalPlotWindow(self.parent, self.mfc_names, self.current_log_file)
        else:
            tkinter.messagebox.showwarning("Warning", "No log file is currently active. Start logging first.")

    def update_plots(self, mfc1_readings=None, mfc2_readings=None, watlow_temp=None, ni_temp=None):
        """Update the plots with new data"""
        t = datetime.now()
        self.time_buffer.append(t)
        
        # read each key
        for key in self.plot_keys:
            try:
                if key.startswith("MFC1"):
                    ch = int(key.split("-")[1])
                    val = float(mfc1_readings[ch-1].strip()) if mfc1_readings and mfc1_readings[ch-1] is not None else numpy.nan
                    val = 0 if val < 0 else val 
                elif key.startswith("MFC2"):
                    ch = int(key.split("-")[1])
                    val = float(mfc2_readings[ch-1].strip()) if mfc2_readings and mfc2_readings[ch-1] is not None else numpy.nan
                    val = 0 if val < 0 else val 
                elif key == "WATLOW":
                    val = watlow_temp if watlow_temp is not None else numpy.nan 
                elif key == "NI":
                    val = ni_temp if ni_temp is not None else numpy.nan 
                else:
                    val = numpy.nan
                
                self.data_buffer[key].append(val)
                
            except Exception as e:
                print(f"Error uploading graphs {key}: {e}")
                self.data_buffer[key].append(numpy.nan)
        
        # keep last 12 points (1 min at 5 s intervals)
        maxlen = 12*60
        if len(self.time_buffer) > maxlen:
            self.time_buffer = self.time_buffer[-maxlen:]
            for k in self.data_buffer:
                self.data_buffer[k] = self.data_buffer[k][-maxlen:]

        # update line data
        xs = self.time_buffer
        for key, line in self.lines.items():
            ys = self.data_buffer[key]
            line.set_data(xs, ys)
            ax = self.axes[key]
            if xs:
                ax.set_xlim(xs[0], xs[-1])
            ax.relim(); ax.autoscale_view()
            # Ensure x-axis labels are rotated
            ax.tick_params(axis='x', rotation=45, labelsize=8)
            ax.figure.tight_layout()
        self.canvas.draw_idle()