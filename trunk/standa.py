import usb
from standa_types import *
import time
nan=float('nan')

#No esta definido en pyusb

USB_DIR_IN          = 0x80
USB_DIR_OUT         = 0x00

USB_RECIP_DEVICE    = usb.RECIP_DEVICE
USB_RECIP_ENDPOINT  = usb.RECIP_ENDPOINT
USB_RECIP_INTERFACE  = usb.RECIP_INTERFACE

USB_TYPE_VENDOR     = usb.TYPE_VENDOR
USB_TYPE_STANDARD   = usb.TYPE_STANDARD


GET_STATUS_DEVICE		=1
GET_STATUS_ENDPOINT		=2
GET_STATUS_INTERFACE	=3

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
        self.version= int(self.get_version(),16)
        
        self.serial = int(self.get_serial())
        self.pos=nan #Current position is unknown
        print "**", self.set_mode( Mode() )
        
    def get_version(self):
        bRequestType = USB_DIR_IN | USB_RECIP_DEVICE | USB_TYPE_STANDARD
        bRequest      = 0x06;
        wValue        = 0x0304;
        wIndex        = 0x0409;
        wLength       = 0x0006;
        data=self.udev.controlMsg( requestType=bRequestType, 
                                   request=bRequest,
                                   buffer=wLength,
                                   value=wValue, 
                                   index=wIndex,
                                   timeout= 1000)
        s="0x"
        for b in data[2:]: s=s+chr(b)
        
        return s
 
    def get_state(self):
        bRequestType = USB_DIR_IN | USB_RECIP_DEVICE | USB_TYPE_VENDOR;
        bRequest=0x82
        wValue=  0x0000
        wIndex=  0x0000
        wLength= 0x000B
        data=self.udev.controlMsg( requestType=bRequestType, 
                                   request=bRequest,
                                   buffer=wLength,
                                   value=wValue, 
                                   index=wIndex,
                                   timeout= 1000)
        return State(data, dev_version=self.version) 
        
    def stop(self):
        '''
        Stop the displacement
        '''
        
        bRequestType = USB_DIR_OUT | USB_RECIP_DEVICE | USB_TYPE_VENDOR
        bRequest      = 0x07;
        wLength       = 0x0000;
        wValue        = 0x0000;
        wIndex        = 0x0000;
        Data=()
        self.udev.controlMsg(requestType=bRequestType,request=bRequest,buffer=Data,value=wValue,index=wIndex,timeout=1000)
    
    def move(self,pos, speed=500,div=1, sl_start=True):#L=128,I=0,div=8):#Velocidad 625 , divisor: 8,4,2,1, carro:serial
        '''
        Move to a given position
        '''
        bRequestType = USB_DIR_OUT | USB_RECIP_DEVICE | USB_TYPE_VENDOR;
        bRequest = 0x80;
        wLength  = 0x0003 
        
        buf=goto_data(pos,div=div,speed=speed, sl_strt=sl_start)
        
        wIndex   = first_word(buf)  #pos & 0xFFFF            #FIRST_WORD  ( kern_buf );
        wValue   = second_word(buf) #(pos/0x10000) & 0xFFFF #SECOND_WORD ( kern_buf );
        
        #
        self.udev.controlMsg(requestType=bRequestType, request=bRequest,buffer=buf[4:],value=wValue, index=wIndex,timeout= 1000)

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
   
        self.move(0,div=8,speed=128)

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
        data=self.udev.controlMsg( requestType=bRequestType, 
                                   request=bRequest,
                                   buffer=(),
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

    def get_status(self,st_type):
        bRequest = 0x00
        wValue   = 0x0000
        wIndex   = 0x0000
        wLength  = 0x0002

        if st_type == GET_STATUS_DEVICE:
            bRequestType = USB_DIR_IN | USB_RECIP_DEVICE | USB_TYPE_STANDARD
        elif st_type == GET_STATUS_ENDPOINT:
            bRequestType = USB_DIR_IN | USB_RECIP_ENDPOINT | USB_TYPE_STANDARD
        elif st_type ==  GET_STATUS_INTERFACE:
            bRequestType = USB_DIR_IN | USB_RECIP_INTERFACE | USB_TYPE_STANDARD

        data=self.udev.controlMsg( requestType=bRequestType, 
                                   request=bRequest,
                                   buffer=wLength,
                                   value=wValue, 
                                   index=wIndex,
                                   timeout= 1000)
        return data

    def get_serial(self):
        bRequestType = USB_DIR_IN | USB_RECIP_DEVICE | USB_TYPE_VENDOR
        bRequest      = 0xC9
        wValue        = 0x0000
        wIndex        = 0x0000
        wLength       = 0x0010
        data=self.udev.controlMsg( requestType=bRequestType, 
                                   request=bRequest,
                                   buffer=wLength,
                                   value=wValue, 
                                   index=wIndex,
                                   timeout= 1000)
                                   
        ser=""
        for i in data: ser=ser+chr(i) 
        return ser
        
    def get_encoder_state(self): 
        bRequestType = USB_DIR_IN | USB_RECIP_DEVICE | USB_TYPE_VENDOR
        bRequest      = 0x85
        wValue        = 0x0000
        wIndex        = 0x0000
        wLength       = 0x0008
        data=self.udev.controlMsg( requestType=bRequestType, 
                                   request=bRequest,
                                   buffer=wLength,
                                   value=wValue, 
                                   index=wIndex,
                                   timeout= 1000)
        return EncoderState(data)        


    def set_mode(self, mode):
        """
        mode - instance of the class mode
        """
        
        assert isinstance(mode,Mode),"mode must be an instance of the Mode class"
        
        bRequestType = USB_DIR_OUT | USB_RECIP_DEVICE | USB_TYPE_VENDOR
        bRequest      = 0x81
        wLength       = 0x0003
        buf = mode.tobuffer()
        
        wValue        = first_word_swapped(buf)
        wIndex        = second_word_swapped(buf)
        
        data=self.udev.controlMsg( requestType=bRequestType, 
                                   request=bRequest,
                                   buffer= buf[4:],
                                   value=wValue, 
                                   index=wIndex,
                                   timeout= 1000)
        self.__mode__=mode
        return data
             
########## Methods abobe are ready
   
    


    
    

    

        
    def set_parameters(self):
        bRequestType = USB_DIR_OUT | USB_RECIP_DEVICE | USB_TYPE_VENDOR
        bRequest      = 0x83
        wLength       = 0x0035
        #~ kern_buf = user_to_kernel ( user_buf, *wLength + 4 );
        wValue        = FIRST_WORD_SWAPPED ( kern_buf )
        wIndex        = SECOND_WORD        ( kern_buf )
        data=self.udev.controlMsg( requestType=bRequestType, 
                                   request=bRequest,
                                   buffer= (),
                                   value=wValue, 
                                   index=wIndex,
                                   timeout= 1000)
        print "Structures not implemented yet"
        
    def download(self):
        bRequestType = USB_DIR_OUT | USB_RECIP_DEVICE | USB_TYPE_VENDOR
        bRequest      = 0xC8
        wLength       = 0x003D
        #~ kern_buf = user_to_kernel ( user_buf, *wLength + 4 );
        wValue        = FIRST_WORD_SWAPPED  ( kern_buf )
        wIndex        = SECOND_WORD_SWAPPED ( kern_buf )
        print "Structures not implemented yet"
        
    def set_serial(self):
        bRequestType = USB_DIR_OUT | USB_RECIP_DEVICE | USB_TYPE_VENDOR
        bRequest      = 0xCA
        wLength       = 0x001C
        #~ kern_buf = user_to_kernel ( user_buf, *wLength + 4 );
        wValue        = FIRST_WORD_SWAPPED  ( kern_buf )
        wIndex        = SECOND_WORD_SWAPPED ( kern_buf )
        print "Structures not implemented yet"

    def emulate_buttons(self):
        bRequestType = USB_DIR_OUT | USB_RECIP_DEVICE | USB_TYPE_VENDOR
        bRequest      = 0x0D
        wLength       = 0x0000
        #~ kern_buf = user_to_kernel ( user_buf, *wLength + 1 );
        wValue        = FIRST_BYTE ( kern_buf );
        wIndex        = 0x0000
        print "Structures not implemented yet"

    def save_parameters(self):
        bRequestType = USB_DIR_OUT | USB_RECIP_DEVICE | USB_TYPE_VENDOR
        bRequest      = 0x84
        wLength       = 0x0000
        wValue        = 0x0000
        wIndex        = 0x0000
        print "Structures not implemented yet"
