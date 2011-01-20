import math
import usb

nan=float('nan')




def get_serial(udev):
    """Return the serial number of the corresponding usb device"""
    serial=0
    bytes=[]
    size=0
    j=(bytes,size)
    bytesToGet=512
    #c0 c9 00 00 00 00 10 00
    serialData=udev.controlMsg(requestType=0xC0, request=0xC9,buffer=bytesToGet,value=0x00, index=0,timeout= 1000)  
    for i in serialData:
        #Suponemos que el serial es un numero decimal
        serial=serial*10
        serial=serial+(i-48)
    return serial

def find_serials():
    """Return a list containing the serial numbers os the  connected Standa
    controllers
    """
    ser=[]
    for bus in usb.busses():
        devices = bus.devices
        for dev in devices:
            if dev.idVendor==0x10c4 and dev.idProduct==0x0230: 
                udev = dev.open()
                ser.append(get_serial(udev))
    return ser

class Standa:
    def __init__(self,serial):
        """
        Class used to control the Standa 8SMC1 USB stepper motor controller
        """
        self.serial=serial
        self.udev=None
        #print "Activando Carro S/N=",self.serial
        for bus in usb.busses():
            devices = bus.devices
            for dev in devices:
                    if dev.idVendor==0x10c4 and dev.idProduct==0x0230: 
                        udev = dev.open()
                        if serial==get_serial(udev):
                            self.udev=udev
        
        self.pos=nan #Current position is unknown


    def stop(self):
        '''
        Stop the displacement
        '''
        Data=()
        self.udev.controlMsg(requestType=0x40,request=0x07,buffer=Data,value=0,index=0,timeout=1000)
    
    def move(self,POS=0,div=8):#L=128,I=0,div=8):#Velocidad 625 , divisor: 8,4,2,1, carro:serial
        '''
        Move to a given position
        '''
        Data=(0xf9,0xc0,int(math.log(div)))
        I=POS & 0xFFFF
        L=(POS/0x10000) & 0xFFFF
        self.udev.controlMsg(requestType=0x40, request=0x80,buffer=Data,value=L, index=I,timeout= 1000)

    def get_trailer(self):
        '''
        Check if the limit switches are pressed
        '''
        bytesToGet=512
        data=self.udev.controlMsg(requestType=0xC0, request=0x82,buffer=bytesToGet,value=0x001, index=0,timeout= 1000)
        return (data[7]>>6)&3
        
    def _fpark(self):
        """If any of the limit switches is pressed, move slowly the translation
         stage until they are not"""
        
        T=self.get_trailer()
        # The trailer close to the motor is pressed
        if T==2:
            self.move(-10000,8)
            while self.get_trailer():
                pass
            self.stop()
            self.udev.controlMsg(requestType=0x40, request=0x01,buffer=0,value=0x00, index=0,timeout= 1000) 
        # The trailer far from the motor is pressed
        elif T==1:
            self.move(10000,8)
            while self.get_trailer():
                pass
            self.stop()
            

    def park(self, mside=True):
        '''
        Park the translation stage, and set the current position to 0
        
        if mside is true, park the translation stage to the motor side, else
        park it to the opposite side.
        '''
        #Move away from the trailers
        self._fpark()
        
        #which side to park
        if mside: move=10000000
        else:     move=-10000000
        
        bytesToGet=512
        T=self.get_trailer()
        if T==2:
            self.udev.controlMsg(requestType=0x40, request=0x01,buffer=0,value=0x00, index=0,timeout= 1000) 
            return
        else:
            self.udev.controlMsg(requestType=0x40, request=0x01,buffer=0,value=0x00, index=0,timeout= 1000)
            self.move(move,2)
            while not self.get_trailer():
                pass
            self.stop()
            self._fpark()
            self.udev.controlMsg(requestType=0x40, request=0x01,buffer=0,value=0x00, index=0,timeout= 1000)
            
        
        return None 
        


    def get_state(self):
        '''
        Return the translation stage state.
        '''
        bytesToGet=512
        data=self.udev.controlMsg(requestType=0xC0, request=0x82,buffer=bytesToGet,value=0x00, index=0,timeout= 1000) 
        return (data[6]>>3 & 0x02) |  data[7]&0x01 

    def wait(self):
        '''
        Wait intil the translation stage stops
        '''
        while(1):    
            if self.get_state()&1==0: 
                    break
            if self.get_trailer()!=0:
                    self.stop()
                    break
        
        return
