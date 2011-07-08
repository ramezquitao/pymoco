import usb
from standa_types import State, goto_data
import time
nan=float('nan')

#No esta definido en pyusb

USB_DIR_IN          = 0x80
USB_DIR_OUT         = 0x00
USB_RECIP_DEVICE    = usb.RECIP_DEVICE
USB_TYPE_VENDOR     = usb.TYPE_VENDOR




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

    def get_state(self):
        bRequestType = USB_DIR_IN | USB_RECIP_DEVICE | USB_TYPE_VENDOR;
        bRequest=0x82
        wValue=  0x0000
        wIndex=  0x0000
        wLength= 0x000B
        data=wLength
        data=self.udev.controlMsg( requestType=bRequestType, 
                                   request=bRequest,
                                   buffer=data,
                                   value=wValue, 
                                   index=wIndex,
                                   timeout= 1000)
        return State(data)  # TODO: pass the board version so the temperature
                            #       can be calculated correctly

    def stop(self):
        '''
        Stop the displacement
        '''
        Data=()
        self.udev.controlMsg(requestType=0x40,request=0x07,buffer=Data,value=0,index=0,timeout=1000)
    
    def move(self,pos, speed=500,div=1):#L=128,I=0,div=8):#Velocidad 625 , divisor: 8,4,2,1, carro:serial
        '''
        Move to a given position
        '''
        bRequestType = USB_DIR_OUT | USB_RECIP_DEVICE | USB_TYPE_VENDOR;
        bRequest = 0x80;
        wLength  = 0x0003 #Data=(0xf9,0xc0,int(math.log(div)))
        #kern_buf = user_to_kernel ( user_buf, *wLength + 4 );
        wIndex   = pos & 0xFFFF            #FIRST_WORD  ( kern_buf );
        wValue   = (pos/0x10000) & 0xFFFF #SECOND_WORD ( kern_buf );
        data=goto_data(pos,div=div,speed=speed)
        #
        self.udev.controlMsg(requestType=bRequestType, request=bRequest,buffer=data,value=wValue, index=wIndex,timeout= 1000)

    def get_trailer(self):
        '''
        Check if the limit switches are pressed
        '''
        st=self.get_state()
        return (st.trailer1,st.trailer2)
    
    def get_current_position(self):
        st=self.get_state()
        return st.cur_pos
        
    def _fpark(self):
        """If any of the limit switches is pressed, move slowly the translation
         stage until they are not"""
        
        ST=self.get_state()
        cp=ST.cur_pos
        
        # The trailer close to the motor is pressed
        if ST.trailer2:
            while any(self.get_trailer()):
                ST=self.get_state()
                cp=ST.cur_pos
                self.move(cp-10000,div=8,speed=500)
                self.wait_nt()
            self.stop()
            #~ self.udev.controlMsg(requestType=0x40, request=0x01,buffer=0,value=0x00, index=0,timeout= 1000) 
        
        # The trailer far from the motor is pressed
        elif ST.trailer1:
            while any(self.get_trailer()):
                ST=self.get_state()
                cp=ST.cur_pos
                self.move(cp+10000,div=8,speed=500)
                self.wait_nt()
            self.stop()
            

    def park(self, mside=True,speed=500, div=1):
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
        
        self.set_current_position(0)
        # The delays in the wait are needed, because some times the run 
        # order is not executed inmediatelly
        #TODO: Check for a flush for tthe USB
        self.wait(0.1)
        
        self.move(move,div=div,speed=speed)
        self.wait(0.1) # wait checking for the trailers
   
        self.move(0,div=8,speed=64)

        while any(self.get_trailer()):    
            pass
        self.stop()
        self.set_current_position(0)    
        self.move(0,div=8,speed=64)
        self.wait(0.1)
        
        return None 
    
    def set_current_position(self, pos=0):
        bRequestType =  USB_DIR_OUT | USB_RECIP_DEVICE | USB_TYPE_VENDOR
        bRequest      = 0x01
        wLength       = 0x0000 
        wValue        = pos >> 16 &0xFFFF
        wIndex        = pos & 0xFFFF
        data=()
        data=self.udev.controlMsg( requestType=bRequestType, 
                                   request=bRequest,
                                   buffer=data,
                                   value=wValue, 
                                   index=wIndex,
                                   timeout= 1000)
        return data
    
    def wait(self,tmr=0):
        '''
        Wait time seconds and then until the translation stage stops
        
        '''
        if time: time.sleep(tmr)
        while self.get_state().run: 
            if any(self.get_trailer())!=False:
                    self.stop()
                    break
        return
        
    def wait_nt(self):
        '''
        Wait intil the translation stage stops does not check the trailers
        '''
        while self.get_state().run:    
            pass
        return
