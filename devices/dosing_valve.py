import serial
import time
import logging

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