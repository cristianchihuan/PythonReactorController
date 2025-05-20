import serial
import time
import logging
import threading
import crcmod
from config.settings import SP_WRITE_DELAY, PVChannels, SPChannels, SP_OUTPUT_PORT_SIGNAL_TYPES

class MFCConnection:
    def __init__(self, port='COM3', baudrate=9600, bytesize=serial.EIGHTBITS, 
                 parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, 
                 timeout=2, write_timeout=2):
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self.write_timeout = write_timeout
        self.ser = []
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
    def Connect(self, port):
        for i in range(3):
            try:
                with self.lock:  # Use lock when connecting
                    self.ser = serial.Serial(port, self.baudrate, self.bytesize, self.parity, 
                                           self.stopbits, self.timeout, self.write_timeout)
                    time.sleep(0.1)
                    self.ser.isOpen()
                    print("MFC Port Opened")
                    self.logger.info("MFC Port Opened %d", i)
                    break
            except Exception as e:
                print("ERROR, MFC port did not open", e)
                self.logger.error("ERROR, MFC port did not open %s", e)
                self.ser = []
            
    def CloseConnection(self):
        try:
            self.ser.close()
            time.sleep(0.1)
            print("MFC Port Closed")
        except Exception as e:
            print("ERROR, MFC port did not close", e)
            logging.critical("ERROR, MFC port did not close", e)
            self.ser = []
            
    def TestMFCConnection(self):
        try:
            if self.ser.isOpen():
                print("MFC serial port is open")
            else:
                print("ERROR, MFC port is not open")
                self.ser = []
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

    def ReadPV(self, channel):
        try:
            with self.lock:  # Use lock for reading PV
                command = b"".join([b'AZ.', PVChannels[channel-1], b'k\r\n'])
                start_time = time.time()
                self.ser.write(command)
                result = self.ser.readline()
                signal_speed = time.time() - start_time
                decoded = result.decode('ascii')
                split = decoded.split(',')
                if split[0] != 'AZ':
                    raise ValueError("Invalid response from MFC")
                flowrate = split[5] if len(split) > 5 else None
                logging.debug(
                    "ReadPV , %s, %s ,  %.4f sec , %s, empty ,%s ",
                    flowrate, command, signal_speed, channel, result
                )
                return flowrate
        except Exception as e:
            logging.debug("Error in MFC Read PV: %s", e)
            print("Error in MFC Read PV")
            return None

    def ReadSP(self, channel):
        try:
            with self.lock:  # Use lock for reading SP
                command = b"".join([b'AZ.', SPChannels[channel-1], b'P1?\r\n'])
                start_time = time.time()
                self.ser.write(command)
                result = self.ser.readline()
                signal_speed = time.time() - start_time
                decoded = result.decode('ascii')
                split = decoded.split(',')
                sp_value = split[4] if len(split) > 4 else None
                logging.debug(
                    "ReadSP ,  %s,  %s,  %.4f sec,  %s, empty, %s",
                    sp_value, command, signal_speed, channel, result
                )
                return sp_value    
        except Exception as e:
            logging.debug("Error in MFC Read SP: %s, %s, %s", e, command, result)
            print("Error in MFC Read SP")
            return None

    def WriteSP(self, channel, value):
        error_detected = False
        try:
            if isinstance(value, (int, float)):
                value = "{:.2f}".format(value)
                value = str(value)
                logging.debug("WriteSP_Int , %s", value)
                
            if isinstance(value, str):
                command = b"".join([b'AZ.', SPChannels[channel-1], b'P1=', value.encode('ascii'), b'\r\n'])
                
                with self.lock:
                    start_time = time.time()
                    time.sleep(SP_WRITE_DELAY)
                    self.ser.write(command)
                    signal_speed = time.time() - start_time
                    result = self.ser.readlines()
                    logging.critical(
                        "WriteSP , %s,  %s ,  %.4f sec ,  %s , empty , %s",
                        value, command, signal_speed, channel, result 
                    )
                    
                    try:
                        decoded = result[0].decode('ascii')
                        parts = decoded.split(',')
                        check_signal_type = parts[2] if len(parts) > 2 else None
                        check_command = parts[3] if len(parts) > 3 else None
                        
                        if check_signal_type != '4':
                            print("Error in response: Invalid signal type")
                            raise ValueError("Invalid SIGNAL type in MFC response")
                        if check_command != 'P01':
                            print("CRITICAL ERROR in MFC Write SP. CHECK OTHER PARAMETERS")
                            error_detected = True
                            raise ValueError("Invalid PARAMETER wrote in MFC response")
                            
                    except Exception as e:
                        print(f"Error parsing MFC response: {e}")

                SP_MFC = self.ReadSP(channel)
                if SP_MFC is None:
                    SP_MFC = self.ReadSP(channel)
                if SP_MFC is not None:
                    SP_MFC = float(SP_MFC)
                    for i in range(3):  
                        if abs(SP_MFC - float(value)) > 0.1:
                            with self.lock:
                                start_time = time.time()
                                self.ser.write(command)
                                time.sleep(SP_WRITE_DELAY)
                                signal_speed = time.time() - start_time
                                result = self.ser.readlines()
                                logging.critical(
                                    "Reattempt_to_Write_SP , %s,  %s ,  %.4f sec ,  %s , empty , %s",
                                    value, command, signal_speed, channel, result 
                                )
                            SP_MFC = self.ReadSP(channel)
                            if SP_MFC is None:
                                continue
                            SP_MFC = float(SP_MFC)
                        else:
                            break
                    print(f"Wrote: {value}, to Channel {channel}")    

        except Exception as e:
            error_detected = True
            logging.critical("Error in MFC Write SP: %s", e)
            print("Error in MFC Write SP")
        
        return error_detected

    def ReadSPSignalType(self, channel):
        try:
            with self.lock:
                command = b''.join([b'AZ.', SPChannels[channel-1], b'P0?\r\n'])
                start_time = time.time()
                self.ser.write(command)

                raw = self.ser.readline()
                print(raw)
                result = raw.decode('ascii').strip()
                elapsed = time.time() - start_time

                parts = result.split(',')
                code_full = parts[4] if len(parts) > 4 else ''
                type = code_full[0] if len(code_full) >= 1 else ''
                print(type)
                
                signal_type = SP_OUTPUT_PORT_SIGNAL_TYPES.get(type, f'Unknown ({type})')
                print(signal_type)
                
                logging.debug(
                    "ReadSPSignalType, %s , cmd=%s , %.4fs , ch=%d , raw=%s",
                    signal_type, command, elapsed, channel, raw
                )
                return signal_type

        except Exception as e:
            logging.debug("Error in MFC ReadSPSignalType: %s", e)
            print("Error reading SP signal type")
            return None

    def WriteSPSignalType(self, channel, signal_type):
        try:
            if signal_type not in SP_OUTPUT_PORT_SIGNAL_TYPES.values():
                raise ValueError(f"Invalid signal type. Must be one of: {list(SP_OUTPUT_PORT_SIGNAL_TYPES.values())}")
            print(signal_type)
            
            type_code = None
            for code, type_str in SP_OUTPUT_PORT_SIGNAL_TYPES.items():
                print(code, type_str, signal_type)
                if type_str == signal_type:
                    type_code = code
                    break

            if type_code is None:
                raise ValueError("Could not find code for signal type")
            print("New signal type", type_code)
            
            command = b"".join([b'AZ.', SPChannels[channel-1], b'P0=', type_code.encode('ascii'),
                              PVChannels[channel-1], b'\r\n'])
            print("The command sent to write the SP signal type", command)
            
            with self.lock:
                start_time = time.time()
                time.sleep(SP_WRITE_DELAY)
                self.ser.write(command)
                signal_speed = time.time() - start_time
                result = self.ser.readlines()
                print("WRITE SP SIGNAL TYPE", result)
                
                logging.debug("WriteSPSignalType , %s , %s , %.4f sec , %s , empty , %s",
                    signal_type, command, signal_speed, channel, result)

            new_type = self.ReadSPSignalType(channel)
            if new_type != signal_type:
                logging.critical(
                    "WriteSPSignalType verification failed. Wanted: %s, Got: %s", signal_type, new_type)
                return None

            return new_type

        except Exception as e:
            logging.critical("Error in MFC Write SP Signal Type: %s", e)
            print("Error writing SP signal type")
            return None

    def ReadSPCONFIG(self, channel):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.lock:
                    command = b"".join([b'AZ.', SPChannels[channel-1], b'v\r\n'])
                    print("The command sent to read the SP config", command)
                    start_time = time.time()
                    self.ser.write(command)
                    
                    config = {
                        'SP Signal Type': 'N/A',
                        'SP Full Scale': 'N/A',
                        'SP Function': 'N/A',
                        'SP Rate': 'N/A',
                        'SP VOR': 'N/A',
                        'SP Batch': 'N/A',
                        'SP Blend': 'N/A',
                        'SP Source': 'N/A'
                    }
                    
                    timeout = time.time() + 5
                    response_lines = []
                    while time.time() < timeout:
                        if self.ser.in_waiting:
                            line = self.ser.readline().decode('ascii', errors='ignore').strip()
                            if line:
                                response_lines.append(line)
                                
                                if '<00>' in line and 'SP Signal Type' in line:
                                    parts = line.split()
                                    config['SP Signal Type'] = parts[-2]
                                elif '<09>' in line and 'SP Full Scale' in line:
                                    parts = line.split()
                                    if len(parts) > 2:
                                        config['SP Full Scale'] = f"{parts[-2]} {parts[-1]}"
                                elif '<02>' in line and 'SP Function' in line:
                                    parts = line.split()
                                    config['SP Function'] = parts[-1]
                                elif '<01>' in line and 'SP Rate' in line:
                                    parts = line.split()
                                    config['SP Rate'] = f"{parts[-2]} {parts[-1]}"
                                elif '<29>' in line and 'SP VOR' in line:
                                    parts = line.split()
                                    config['SP VOR'] = parts[-1]
                                elif '<44>' in line and 'SP Batch' in line:
                                    parts = line.split()
                                    config['SP Batch'] = f"{parts[-2]} {parts[-1]}"
                                elif '<45>' in line and 'SP Blend' in line:
                                    parts = line.split()
                                    config['SP Blend'] = parts[-1]
                                elif '<46>' in line and 'SP Source' in line:
                                    parts = line.split()
                                    config['SP Source'] = parts[-1]
                        
                        if len(response_lines) > 0 and not self.ser.in_waiting:
                            time.sleep(0.1)
                            if not self.ser.in_waiting:
                                break
                    
                    if all(value == 'N/A' for value in config.values()):
                        if attempt < max_retries - 1:
                            print(f"No valid configuration data received on attempt {attempt + 1}, retrying...")
                            time.sleep(0.5)
                            continue
                        else:
                            print("Failed to get valid configuration data after all retries")
                    
                    signal_speed = time.time() - start_time
                    print("The time it took to read the SP config", signal_speed)
                    
                    logging.debug("ReadSPCONFIG , %s , %s , %.4f sec , %s , empty , %s",
                        str(config), command, signal_speed, channel, '\n'.join(response_lines))
                    
                    return config
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Error reading SP CONFIG on attempt {attempt + 1}, retrying: {str(e)}")
                    time.sleep(0.5)
                    continue
                else:
                    logging.debug("Error in MFC Read SP CONFIG after all retries: %s", e)
                    print("Error in MFC Read SP CONFIG after all retries")
                    return None

    def ReadPVCONFIG(self, channel):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                command = b"".join([b'AZ.', PVChannels[channel-1], b'v\r\n'])
                print("The command sent to read the PV config", command)
                start_time = time.time()
                self.ser.write(command)
                
                config = {
                    'Measure Units': 'N/A',
                    'Time Base': 'N/A',
                    'Decimal Point': 'N/A',
                    'Gas Factor': 'N/A',
                    'Log Type': 'N/A',
                    'PV Signal Type': 'N/A',
                    'PV Full Scale': 'N/A'
                }
                
                timeout = time.time() + 5
                response_lines = []
                while time.time() < timeout:
                    if self.ser.in_waiting:
                        line = self.ser.readline().decode('ascii', errors='ignore').strip()
                        if line:
                            response_lines.append(line)
                            
                            if '<04>' in line:
                                parts = line.split()
                                config['Measure Units'] = parts[-1]
                            elif '<10>' in line:
                                parts = line.split()
                                config['Time Base'] = parts[-1]
                            elif '<03>' in line:
                                parts = line.split()
                                config['Decimal Point'] = parts[-1]
                            elif '<27>' in line:
                                parts = line.split()
                                config['Gas Factor'] = parts[-1]
                            elif '<28>' in line:
                                parts = line.split()
                                config['Log Type'] = parts[-1]
                            elif '<00>' in line and 'PV Signal Type' in line:
                                parts = line.split()
                                config['PV Signal Type'] = parts[-2]
                            elif '<09>' in line and 'PV Full Scale' in line:
                                parts = line.split()
                                if len(parts) > 2:
                                    config['PV Full Scale'] = f"{parts[-2]} {parts[-1]}"
                    
                    if len(response_lines) > 0 and not self.ser.in_waiting:
                        time.sleep(0.1)
                        if not self.ser.in_waiting:
                            break
                
                if all(value == 'N/A' for value in config.values()):
                    if attempt < max_retries - 1:
                        print(f"No valid configuration data received on attempt {attempt + 1}, retrying...")
                        time.sleep(0.5)
                        continue
                    else:
                        print("Failed to get valid configuration data after all retries")
                
                signal_speed = time.time() - start_time
                print("The time it took to read the PV config", signal_speed)
                
                logging.debug("ReadPVCONFIG , %s , %s , %.4f sec , %s , empty , %s",
                    str(config), command, signal_speed, channel, '\n'.join(response_lines))
                
                return config
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Error reading PV CONFIG on attempt {attempt + 1}, retrying: {str(e)}")
                    time.sleep(0.5)
                    continue
                else:
                    logging.debug("Error in MFC Read PV CONFIG after all retries: %s", e)
                    print("Error in MFC Read PV CONFIG after all retries")
                    return None 