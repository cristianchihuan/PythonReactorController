import serial
import time
import logging
import binascii
import struct
import crcmod

class WatlowConnection:
    def __init__(self, port='COM4', baudrate=38400, timeout=0.5):
        self.port=port
        self.baudrate=baudrate
        self.timeout=timeout
        self.ser=[]
        self.ConnectionCounter = 0  
        self.FirstTime = True
        self.onoff = False   
        self.crc = crcmod.mkCrcFun(0b10001000000100001)
        
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
            checksum = struct.pack('<H', ~self.crc(writevalue) & 0xffff)
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
            checksum = struct.pack('<H', ~self.crc(writevalue) & 0xffff)
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