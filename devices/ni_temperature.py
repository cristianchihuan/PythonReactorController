import nidaqmx
import logging
from config.settings import DefaultNIComPort

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
        If the device isn't connected, it logs an error and leaves self.task as None.
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
            logging.critical("NI thermocouple connection test failed.")
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