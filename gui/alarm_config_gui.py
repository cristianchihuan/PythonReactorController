import tkinter
from tkinter import ttk, messagebox
import time
# IMPORTANT : THIS CLASS HAS NOT BEEN TESTED YET. DO NOT ATTEMP TO USE IT IF THE 
# NECCESSARY CHANGES HAVE BEEN MADE IN THE CONTROLLER_GUI. 
class AlarmConfigGUI:
    def __init__(self, parent, mfc_names, have_8comports=False):
        self.parent = parent
        self.mfc_names = mfc_names[:4] if not have_8comports else mfc_names
        self.alarms = []  # List to store alarm configurations
        self.alarm_windows = {}  # Dictionary to store active alarm windows
        self.channel_values = {}  # Dictionary to store current channel values
        self.last_alarm_time = {}  # Track when alarms were last shown
        self.max_alarms = 3  # Maximum number of alarms allowed
        
        # Create main frame
        self.main_frame = ttk.Frame(parent)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create alarm list frame
        self.alarm_list_frame = ttk.LabelFrame(self.main_frame, text="Configured Alarms")
        self.alarm_list_frame.pack(fill='x', pady=(0, 10))
        
        # Create new alarm frame
        self.new_alarm_frame = ttk.LabelFrame(self.main_frame, text="New Alarm")
        self.new_alarm_frame.pack(fill='x', pady=(0, 10))
        
        # Channel 1 selection
        ttk.Label(self.new_alarm_frame, text="Channel 1:").grid(row=0, column=0, padx=5, pady=5)
        self.channel1_var = tkinter.StringVar()
        self.channel1_combo = ttk.Combobox(self.new_alarm_frame, textvariable=self.channel1_var, values=self.mfc_names)
        self.channel1_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Threshold 1
        ttk.Label(self.new_alarm_frame, text="Threshold 1:").grid(row=0, column=2, padx=5, pady=5)
        self.threshold1_var = tkinter.StringVar()
        self.threshold1_entry = ttk.Entry(self.new_alarm_frame, textvariable=self.threshold1_var, width=10)
        self.threshold1_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # AND/OR selection
        self.operator_var = tkinter.StringVar(value="AND")
        self.operator_combo = ttk.Combobox(self.new_alarm_frame, textvariable=self.operator_var, 
                                         values=["AND", "OR"], state="readonly", width=5)
        self.operator_combo.grid(row=0, column=4, padx=5, pady=5)
        
        # Channel 2 selection
        ttk.Label(self.new_alarm_frame, text="Channel 2:").grid(row=0, column=5, padx=5, pady=5)
        self.channel2_var = tkinter.StringVar()
        self.channel2_combo = ttk.Combobox(self.new_alarm_frame, textvariable=self.channel2_var, values=self.mfc_names)
        self.channel2_combo.grid(row=0, column=6, padx=5, pady=5)
        
        # Threshold 2
        ttk.Label(self.new_alarm_frame, text="Threshold 2:").grid(row=0, column=7, padx=5, pady=5)
        self.threshold2_var = tkinter.StringVar()
        self.threshold2_entry = ttk.Entry(self.new_alarm_frame, textvariable=self.threshold2_var, width=10)
        self.threshold2_entry.grid(row=0, column=8, padx=5, pady=5)
        
        # Add button
        self.add_button = ttk.Button(self.new_alarm_frame, text="Add Alarm", command=self.add_alarm)
        self.add_button.grid(row=0, column=9, padx=5, pady=5)
        
        # Create alarm list
        self.alarm_list = ttk.Treeview(self.alarm_list_frame, columns=("Enabled", "Channel1", "Threshold1", "Operator", 
                                                                      "Channel2", "Threshold2", "Status"),
                                      show="headings")
        self.alarm_list.heading("Enabled", text="Click to Enable/Disable")
        self.alarm_list.heading("Channel1", text="Channel 1")
        self.alarm_list.heading("Threshold1", text="Threshold 1")
        self.alarm_list.heading("Operator", text="Operator")
        self.alarm_list.heading("Channel2", text="Channel 2")
        self.alarm_list.heading("Threshold2", text="Threshold 2")
        self.alarm_list.heading("Status", text="Status")
        
        # Set column widths
        self.alarm_list.column("Enabled", width=150)  # Made wider to fit the heading
        self.alarm_list.column("Channel1", width=100)
        self.alarm_list.column("Threshold1", width=100)
        self.alarm_list.column("Operator", width=60)
        self.alarm_list.column("Channel2", width=100)
        self.alarm_list.column("Threshold2", width=100)
        self.alarm_list.column("Status", width=100)
        
        self.alarm_list.pack(fill='x', padx=5, pady=5)
        
        # Bind checkbox click event
        self.alarm_list.bind('<ButtonRelease-1>', self.on_alarm_list_click)
        
        # Delete button
        self.delete_button = ttk.Button(self.alarm_list_frame, text="Delete Selected", command=self.delete_alarm)
        self.delete_button.pack(pady=5)
    
    def update_channel_values(self, mfc1_readings, mfc2_readings=None):
        """Update the current values for all channels and check alarms"""
        try:
            # Update MFC1 values
            for i, value in enumerate(mfc1_readings):
                if value is not None:
                    try:
                        float_value = float(value)
                        if float_value >= 0:  # Only accept non-negative values
                            self.channel_values[self.mfc_names[i]] = float_value
                    except (ValueError, TypeError):
                        continue
            
            # Update MFC2 values if available
            if mfc2_readings:
                for i, value in enumerate(mfc2_readings):
                    if value is not None:
                        try:
                            float_value = float(value)
                            if float_value >= 0:  # Only accept non-negative values
                                self.channel_values[self.mfc_names[i + 4]] = float_value
                        except (ValueError, TypeError):
                            continue
            
            # Check all alarms
            self.check_alarms()
        except Exception as e:
            print(f"Error in update_channel_values: {e}")
    
    def check_alarms(self):
        """Check all enabled alarms and show windows for triggered ones"""
        try:
            current_time = time.time()
            for alarm in self.alarms:
                if not alarm['enabled'] or alarm['acknowledged']:
                    continue
                
                # Get current values for channels
                channel1_value = self.channel_values.get(alarm['channel1'])
                channel2_value = self.channel_values.get(alarm['channel2'])
                
                if channel1_value is None or channel2_value is None:
                    continue
                
                # Check conditions
                condition1 = channel1_value > alarm['threshold1']
                condition2 = channel2_value > alarm['threshold2']
                
                if alarm['operator'] == "AND":
                    triggered = condition1 and condition2
                else:  # OR
                    triggered = condition1 or condition2
                
                if triggered:
                    last_time = self.last_alarm_time.get(alarm['id'], 0)
                    if current_time - last_time >= 30:  # 30 seconds have passed
                        self.show_alarm_window(alarm)
                        self.last_alarm_time[alarm['id']] = current_time
        except Exception as e:
            print(f"Error in check_alarms: {e}")
    
    def show_alarm_window(self, alarm):
        """Show alarm window"""
        try:
            # Close existing window if any
            if alarm['id'] in self.alarm_windows:
                try:
                    self.alarm_windows[alarm['id']].destroy()
                except:
                    pass
                del self.alarm_windows[alarm['id']]
            
            # Create new window
            window = tkinter.Toplevel(self.parent)
            window.title("ALARM")
            window.configure(bg='red')
            
            # Set window size and position
            window_width = 400
            window_height = 200
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Make window stay on top
            window.attributes('-topmost', True)
            
            # Create message with larger font
            message = f"ALARM TRIGGERED!\n\n{alarm['channel1']} > {alarm['threshold1']} {alarm['operator']} {alarm['channel2']} > {alarm['threshold2']}"
            label = ttk.Label(window, text=message, background='red', foreground='white', font=('Arial', 12, 'bold'))
            label.pack(padx=20, pady=20)
            
            # Create acknowledge button
            def acknowledge():
                try:
                    alarm['acknowledged'] = True
                    self.update_alarm_list()
                    window.destroy()
                    if alarm['id'] in self.alarm_windows:
                        del self.alarm_windows[alarm['id']]
                    if alarm['id'] in self.last_alarm_time:
                        del self.last_alarm_time[alarm['id']]
                except Exception as e:
                    print(f"Error in acknowledge: {e}")
            
            button = ttk.Button(window, text="ACKNOWLEDGE", command=acknowledge)
            button.pack(pady=20)
            
            # Store window reference
            self.alarm_windows[alarm['id']] = window
            
            # Handle window close
            def on_window_close():
                try:
                    window.destroy()
                    if alarm['id'] in self.alarm_windows:
                        del self.alarm_windows[alarm['id']]
                except Exception as e:
                    print(f"Error in on_window_close: {e}")
            
            window.protocol("WM_DELETE_WINDOW", on_window_close)
            
        except Exception as e:
            print(f"Error in show_alarm_window: {e}")
    
    def on_alarm_list_click(self, event):
        """Handle clicks on the alarm list, specifically for the enable checkbox"""
        try:
            region = self.alarm_list.identify_region(event.x, event.y)
            if region == "cell":
                column = self.alarm_list.identify_column(event.x)
                if column == "#1":  # Enabled column
                    item = self.alarm_list.identify_row(event.y)
                    if item:
                        index = self.alarm_list.index(item)
                        if index < len(self.alarms):
                            self.alarms[index]['enabled'] = not self.alarms[index]['enabled']
                            if not self.alarms[index]['enabled']:
                                # If disabling alarm, clean up its resources
                                alarm_id = self.alarms[index]['id']
                                if alarm_id in self.alarm_windows:
                                    try:
                                        self.alarm_windows[alarm_id].destroy()
                                    except:
                                        pass
                                    del self.alarm_windows[alarm_id]
                                if alarm_id in self.last_alarm_time:
                                    del self.last_alarm_time[alarm_id]
                            self.update_alarm_list()
        except Exception as e:
            print(f"Error in on_alarm_list_click: {e}")
    
    def add_alarm(self):
        try:
            # Check if we've reached the maximum number of alarms
            if len(self.alarms) >= self.max_alarms:
                messagebox.showerror("Error", f"Maximum number of alarms ({self.max_alarms}) reached")
                return
                
            channel1 = self.channel1_var.get()
            try:
                threshold1 = float(self.threshold1_var.get())
                if threshold1 < 0:
                    messagebox.showerror("Error", "Threshold values must be positive")
                    return
            except ValueError:
                messagebox.showerror("Error", "Please enter valid threshold values")
                return
                
            operator = self.operator_var.get()
            channel2 = self.channel2_var.get()
            
            try:
                threshold2 = float(self.threshold2_var.get())
                if threshold2 < 0:
                    messagebox.showerror("Error", "Threshold values must be positive")
                    return
            except ValueError:
                messagebox.showerror("Error", "Please enter valid threshold values")
                return
            
            if not all([channel1, channel2]):
                messagebox.showerror("Error", "Please select both channels")
                return
            
            if channel1 == channel2:
                messagebox.showerror("Error", "Please select different channels")
                return
            
            alarm = {
                'id': len(self.alarms),  # Unique ID for each alarm
                'channel1': channel1,
                'threshold1': threshold1,
                'operator': operator,
                'channel2': channel2,
                'threshold2': threshold2,
                'enabled': True,  # Default to enabled
                'acknowledged': False
            }
            
            self.alarms.append(alarm)
            self.update_alarm_list()
            
            # Clear inputs
            self.channel1_var.set('')
            self.channel2_var.set('')
            self.threshold1_var.set('')
            self.threshold2_var.set('')
            
        except Exception as e:
            print(f"Error in add_alarm: {e}")
            messagebox.showerror("Error", "An error occurred while adding the alarm")
    
    def delete_alarm(self):
        try:
            selected = self.alarm_list.selection()
            if not selected:
                return
            
            for item in selected:
                index = self.alarm_list.index(item)
                if index < len(self.alarms):
                    # Clean up alarm resources
                    alarm_id = self.alarms[index]['id']
                    if alarm_id in self.alarm_windows:
                        try:
                            self.alarm_windows[alarm_id].destroy()
                        except:
                            pass
                        del self.alarm_windows[alarm_id]
                    if alarm_id in self.last_alarm_time:
                        del self.last_alarm_time[alarm_id]
                    self.alarms.pop(index)
            
            self.update_alarm_list()
        except Exception as e:
            print(f"Error in delete_alarm: {e}")
    
    def update_alarm_list(self):
        try:
            for item in self.alarm_list.get_children():
                self.alarm_list.delete(item)
            
            for alarm in self.alarms:
                status = "Acknowledged" if alarm['acknowledged'] else "Active"
                enabled_text = "✓ ENABLED" if alarm['enabled'] else "✗ DISABLED"
                
                self.alarm_list.insert('', 'end', values=(
                    enabled_text,
                    alarm['channel1'],
                    alarm['threshold1'],
                    alarm['operator'],
                    alarm['channel2'],
                    alarm['threshold2'],
                    status
                ))
        except Exception as e:
            print(f"Error in update_alarm_list: {e}")  