import tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy
import time
import matplotlib.dates as mdates
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import style

class PlotsGUI:
    def __init__(self, parent, have_8comports=False, have_watlow=False, have_nitemperature=False, mfc_names=None):
        # Set a modern style
        plt.style.use('bmh')  # Using a built-in style
        
        self.parent = parent
        self.have_8comports = have_8comports
        self.have_watlow = have_watlow
        self.have_nitemperature = have_nitemperature
        self.mfc_names = mfc_names or []

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
            #self.setpoint[key], = ax.plot([], [], color=color, linestyle='--', alpha=0.5, label='Setpoint')

        # --- add spacing ---
        fig.tight_layout(pad=2.0)

        self.time_buffer = []
        self.data_buffer = {k: [] for k in self.plot_keys}
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas = canvas

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