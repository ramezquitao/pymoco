import struct
from array import array
from easystruct import Easystruct

def getbit(num,bit=0):
    b=0x01<<bit
    return (num & b) ==b
    
def tobyte(lb):
    res=0
    for n,b in enumerate(lb):
        res=res+b*(2**n)
    return res
    
def byte2bits(byte):
    res=[]
    for n in range(8):
        res.append(getbit(byte,n))
    return res


def clamp(val,minv,maxv):
    return sorted(( val, minv, maxv ))[1]
    
#define		BYTE_I(i)				(*(((__u8 * )pPacketData)+i))

def first_byte(buf):
    return struct.unpack("B",buf[0])[0]
def second_byte(buf):
    return struct.unpack("B",buf[1])[0]
def third_byte(buf):
    return struct.unpack("B",buf[2])[0]
def fourth_byte(buf):
    return struct.unpack("B",buf[3])[0]

def first_word(buf):
    return struct.unpack("H",buf[0:2])[0]
    
def second_word(buf):
    return struct.unpack("H",buf[2:4])[0]


def first_word_swapped(buf):
    return ((first_byte(buf)<<8)|second_byte(buf))
        
def second_word_swapped(buf):
    return ((third_byte(buf)<<8)|fourth_byte(buf))
    
#define		REST_DATA(pPacketData)			((void *)(((__u16 * )pPacketData)+2))

def byte(b):
    return int(b) & 0xff
    
def word(w):
    return int(w) & 0xffff

def hibyte(w):
    return ((w&0xff00)>>8)
def lobyte(w):
        return (w&0x00ff)

def hiword(dw):
    return ((dw&0xffff0000)>>16)
    
def loword(dw):
    return (dw&0x0000ffff)



def pack_word(w):
    return (hibyte(w)|(lobyte(w)<<8))

def pack_dword(w):
    return  (hibyte(hiword(w))| (lobyte(hiword(w))<<8)| (hibyte(loword(w))<<16)| (lobyte(loword(w))<<24))
     
class State:
    def __init__(self,state=None,dev_version=0x2400):
        
        
        fmt="=iHBBBH"
        st=array("B",state[0:11])
        pos,temp,S0,S1,S2,volt= struct.unpack(fmt,st)
        
        M1=getbit(S0,0)         # | Step size is 2^(-M1-2*M2), where M1,M2 = 0,1. May be otherwise 1<->2.
        M2=getbit(S0,1)         # |
        LOFT=getbit(S0,2)       # Indicates "Loft State".
        REFIN=getbit(S0,3)      # If TRUE then full power.
        CW_CCW=getbit(S0,4)     # Current direction. Relatively!
        RESET=getbit(S0,5)      # If TRUE then Step Motor is ON.
        FULLSPEED=getbit(S0,6)  # If TRUE then full speed. Valid in "Slow Start" mode.
        AFTRESET=getbit(S0,7)   # TRUE After Device reset, FALSE after "Set Position".
        
        
        RUN=getbit(S1,0)        # TRUE if step motor is rotating.
        SYNCIN=getbit(S1,1)     # Logical state directly from input synchronization PIN (pulses treated as positive).
        SYNCOUT=getbit(S1,2)    # Logical state directly from output synchronization PIN (pulses are positive).
        ROTTR=getbit(S1,3)      # Indicates current rotary transducer logical press state.
        ROTTRERR=getbit(S1,4)   # Indicates rotary transducer error flag (reset by USMC_SetMode function with ResetRT bit  TRUE).
        EMRESET=getbit(S1,5)    # Indicates state of emergency disable button (TRUE  Step motor power off).
        TRAILER1=getbit(S1,6)   # Indicates trailer 1 logical press state.
        TRAILER2=getbit(S1,7)   # Indicates trailer 2 logical press state.
        
        USBPOW=getbit(S2,0)     # USB Powered.
        #UNKNOWN   : 6;
        Working=getbit(S2,7)    # This bit must be always TRUE (to chek functionality).
        
        self.areset = AFTRESET
        
        self.cw_ccw =  CW_CCW
        self.em_reset = EMRESET
        self.full_power =  REFIN
        self.full_speed = FULLSPEED
        self.loft = LOFT
        self.power = RESET
        self.rot_tr = ROTTR
        self.rot_tr_err  = ROTTRERR
        self.run = RUN
        #/*Str -> SDivisor= See below;*/
        self.sinc_in = SYNCIN
        self.sinc_out = SYNCOUT
        
        self.trailer1  = TRAILER1
        self.trailer2  = TRAILER2
	
        self.cur_pos=pos #( ( signed int ) getStateData.CurPos ) / 8;
        self.voltage=volt/ 65536.0 * 3.3 * 20.0;
        if self.voltage<5:self.voltage=0
        
        if dev_version< 0x2400:
            temp = temp * 3.3 / 65536.0;
            temp = temp * 10.0 / ( 5.0 - temp );
            temp = ( 1.0 / 298.0 ) + ( 1.0 / 3950.0 ) * log ( temp / 10.0 );
            temp = 1.0 / t - 273.0;
	
        else:
            temp = ( ( temp * 3.3 * 100.0 / 65536.0 ) - 50.0 );
        self.temp=temp
    
class Serial:
    def __init__(self,data):
        st=array("B",data)
        print data,st
        self.password=str(st[0:16])
        self.serial=str(st[16:])

class EncoderState:
    def __init__(self, data):
        st=array("B", data)
        fmt="=II"
        self.e_cur_pos, self.enc_pos= struct.unpack(fmt,st)

class Mode:
    def __init__(self, mode=None,**kwargs):
        
        if isinstance(mode,tuple):
            assert kwargs=={}, "if mode != None no kwargs can be given"
            
            st=array("B", mode)
            fmt="=BBBI"
            b0,b1,b2,self.synccount=struct.unpack(fmt,st)
            
            [self.pmode,
            self.refinen,
            self.resetd,
            self.emreset,
            self.tr1t,
            self.tr2r,
            self.rottrt,
            self.trswap]=byte2bits(b0)
            
            [self.tr1en,
            self.tr2en,
            self.rettren,
            self.rottrop,
            self.butt1t,
            self.butt2t,
            self.butswap,
            self.resetrt]=byte2bits(b1)
            
            [self.sncouten,
            self.syncoutr,
            self.syncinop,
            self.syncopol,
            self.encoder,
            self.incvenc,
            self.resbenc,
            self.resenc]=byte2bits(b2)
        else:
            assert mode==None, "Assert can only be a tuple or none"
            self.pmode=kwargs.pop("pmode",True)
            self.refinen=kwargs.pop("refinen",True) #preg
            self.resetd=kwargs.pop("resetd",False)
            self.emreset=kwargs.pop("emreset",False)
            self.tr1t=kwargs.pop("tr1t",False) # OK for CI stages
            self.tr2r=kwargs.pop("tr2r",False) # OK for CI stages
            self.rottrt=kwargs.pop("rottrt",False)
            self.trswap=kwargs.pop("trswap",False)
                       
            ##########
            
            self.tr1en=kwargs.pop("tr1en",True) # This does not seem to matter
            self.tr2en=kwargs.pop("tr2en",True) # This does not seem to matter
            self.rettren=kwargs.pop("rettren",False)
            self.rottrop=kwargs.pop("rottrop",False)
            self.butt1t=kwargs.pop("butt1t",False)
            self.butt2t=kwargs.pop("butt2t",False)
            self.butswap=kwargs.pop("butswap",False)
            self.resetrt=kwargs.pop("resetrt",False)
            
            #############
                     
            self.sncouten=kwargs.pop("sncouten",True)
            self.syncoutr=kwargs.pop("syncoutr",False)
            self.syncinop=kwargs.pop("syncinop",True)
            self.syncopol=kwargs.pop("syncopol",False)
            self.encoder=kwargs.pop("encoder",False) # Encoderen
            self.incvenc=kwargs.pop("incvenc",False) #Encoderinv
            self.resbenc=kwargs.pop("resbenc",False)
            self.resenc=kwargs.pop("resenc",False)
            
            ##############
            
            self.synccount=kwargs.pop("synccount",4)
        
        assert kwargs=={}, "invalid kwargs given "+str(kwargs)
        
        
    def tobuffer(self):
        fmt="=BBBI"
        
        b0=tobyte([self.pmode,
                       self.refinen,
                       self.resetd,
                       self.emreset,
                       self.tr1t,
                       self.tr2r,
                       self.rottrt,
                       self.trswap])
                       
        b1=tobyte([self.tr1en,
                       self.tr2en,
                       self.rettren,
                       self.rottrop,
                       self.butt1t,
                       self.butt2t,
                       self.butswap,
                       self.resetrt])
        
        b2=tobyte([self.sncouten,
                       self.syncoutr,
                       self.syncinop,
                       self.syncopol,
                       self.encoder,
                       self.incvenc,
                       self.resbenc,
                       self.resenc])
        
        buf=struct.pack(fmt, b0, b1, b2, pack_dword(self.synccount))
        
        return buf



#~ typedef	struct	_MODE_PACKET	// 7 bytes;
#~ {
	#~ // Byte 0:
	#~ __u8  PMODE    : 1;	// Turn off buttons (TRUE - buttons disabled).
	#~ __u8  REFINEN  : 1;	// Current reduction regime (TRUE - regime is on).
	#~ __u8  RESETD   : 1;	// Turn power off and make a whole step (TRUE - apply).
	#~ __u8  EMRESET  : 1;	// Quick power off.
	#~ __u8  TR1T     : 1;	// Trailer 1 TRUE state.
	#~ __u8  TR2T     : 1;	// Trailer 2 TRUE state.
	#~ __u8  ROTTRT   : 1;	// Rotary Transducer TRUE state.
	#~ __u8  TRSWAP   : 1;	// If TRUE, Trailers are Swapped (Swapping After Reading Logical State).
	#~ // Byte 1:
	#~ __u8  TR1EN    : 1;	// Trailer 1 Operation Enabled.
	#~ __u8  TR2EN    : 1;	// Trailer 2 Operation Enabled.
	#~ __u8  ROTTREN  : 1;	// Rotary Transducer Operation Enabled.
	#~ __u8  ROTTROP  : 1;	// Rotary Transducer Operation Select (stop on error for TRUE).
	#~ __u8  BUTT1T   : 1;	// Button 1 TRUE state.
	#~ __u8  BUTT2T   : 1;	// Button 2 TRUE state.
	#~ __u8  BUTSWAP  : 1;	// If TRUE, Buttons are Swapped (Swapping After Reading Logical State).
	#~ __u8  RESETRT  : 1;	// Reset Rotary Transducer Check Positions (need one full revolution before it can detect error).
	#~ // Byte 2:
	#~ __u8  SNCOUTEN : 1;	// Output Syncronization Enabled.
	#~ __u8  SYNCOUTR : 1;	// Reset output synchronization counter.
	#~ __u8  SYNCINOP : 1;	// Synchronization input mode: TRUE - Step motor will move one time to the DestPos FALSE - Step motor will move multiple times by DestPos microsteps as distance.
	#~ __u8  SYNCOPOL : 1;	// Output Syncronization Pin Polarity.
	#~ __u8  ENCODER  : 1;	// Encoder is used on pins {SYNCIN,ROTTR} - disables Syncronization input and Rotary Tranducer.
	#~ __u8  INVENC   : 1;	// Invert Encoder Counter Direction.
	#~ __u8  RESBENC  : 1;	// Reset <Encoder Position> and <SM Position in Encoder units> to 0.
	#~ __u8  RESENC   : 1;	// Reset <SM Position in Encoder units> to <Encoder Position>.
	#~ __u16 SYNCCOUNT;	// Number of steps after which synchronization output signal occurs. Parece que esto esta mal y es un DWORD
#~ } MODE_PACKET, * PMODE_PACKET, * LPMODE_PACKET;
        

def goto_data(dest_pos ,speed=500 ,
                 div=1, 
                 def_dir=False,
                 loft_en=False,
                 sl_strt=False,
                 w_sync =False,
                 sync_out=False,
                 force_loft=False):
        
        #The sorted is used to clip the speed in the 16,5000 range
        
        a=sorted(( float(speed), 16.0, 5000.0 ))[1]
        timer_period= pack_word(int( 65536.0 - ( 1000000.0 / a + 0.5 )))
        
        #If key is not 1,2,4,8 then use as default 8, and silently ignore 
        #the error
        
        m1,m2= {1:(0,0),2:(1,0),4:(0,1),8:(1,1)}.get(div,(1,1))

        fmt="iHB"
        buf=struct.pack(fmt,
                          dest_pos,
                          timer_period,
                          m1+2*m2+4*def_dir+8*loft_en+
                          16*sl_strt+32*w_sync+64*sync_out+128*force_loft)
        return buf

#~ 
#~ typedef	struct	_GO_TO_PACKET	// 7 bytes;
#~ {
	#~ __u32 DestPos;		// Destination Position.
	#~ __u16  TimerPeriod;	// Period between steps is 12*(65536-[TimerPeriod])/[SysClk] in seconds, where SysClk = 24000000 Hz.
	#~ // Byte 7:
	#~ __u8  M1        : 1;	// | Step size is 2^(-M1-2*M2), where M1,M2 = 0,1. May be otherwise 1<->2.
	#~ __u8  M2        : 1;	// |
	#~ __u8  DEFDIR    : 1;	// Default direction. For "Anti Loft" operation.
	#~ __u8  LOFTEN    : 1;	// Enable automatic "Anti Loft" operation.
	#~ __u8  SLSTRT    : 1;	// Slow Start(and Stop) mode.
	#~ __u8  WSYNCIN   : 1;	// Wait for input synchronization signal to start.
	#~ __u8  SYNCOUTR  : 1;	// Reset output synchronization counter.
	#~ __u8  FORCELOFT : 1;	// Force driver automatic "Anti Loft" mechanism to reset "Loft State".
#~ } GO_TO_PACKET, * PGO_TO_PACKET, * LPGO_TO_PACKET;
#~ 
#~ 


class Parameters(Easystruct):

    def __init__(self,param_buf=None, dev_ver=0x2400, **kwargs):
        
        if dev_ver< 0x2407:
            startposfunc= lambda x: 0
            istartposfunc = lambda x: 0
        else:
            startposfunc= lambda x: pack_word(x*8 & 0xFFFFFF00)
            istartporfunc=lambda x: pack_word(x)/8
            
        if dev_ver <0x2400:
            def maxtempfunc(T):
                t=clamp(T,0.,100.)
                t = 10.0 * exp (3950.0*(1.0/(t+273.0)-1.0/298.0))
                t = ((5*t/(10+t))*65536.0/3.3+0.5);
                return pack_word(word(t))
            
            def maxtempfunci(T):
                t=float(pack_word(T))
                t=t*3.3/ 65536.0
                t=10.0*t/(5.0-t)
                t=(1.0/298.0)+(1.0/3950.0)*log(t/10.0)
                t=1.0/t- 273.0
                return t

        else:
            def maxtempfunc(T):
                t=(T+50.0)/330.0*65536.0
                t=(t+0.5)   
                return pack_word(word(t))
                
            def maxtempfunci(T):
                t = float(pack_word(T))
                t=(t*3.3*100.0/65536.0)-50.0
                return t

        
        def loftperiodfunc(x):
            if x==0.:
                return 0
            else:
                return pack_word (word(65536.0-(125000.0/clamp(x,16.0,5000.0))+0.5))
        
        def loftperiodfunci(x):
            X=pack_word(x)
            
            if X==0:
                return 0.
            else:
                return 125000.0/(65536.0-X)
                
        structdef=[ ("delay1","B",500., lambda x: byte(clamp(int(x/98.+.5 ),1,15 )),lambda x: 98.*x), #AccelT
                    ("delay2","B",500., lambda x: byte(clamp(int(x/98.+.5 ),1,15 )),lambda x: 98.*x), #DecelT
                    ("refintimeout","H",100., lambda x: word(clamp(x,1.,9961.)/0.152 + 0.5),lambda x: x*.152), #ptimeout
                    ("btimeout1","H",500., lambda x: pack_word(word(clamp(x,1.,9961.)/0.152 + 0.5)),lambda x: pack_word(x)*.152),
                    ("btimeout2","H",500., lambda x: pack_word(word(clamp(x,1.,9961.)/0.152 + 0.5)),lambda x: pack_word(x)*.152),
                    ("btimeout3","H",500., lambda x: pack_word(word(clamp(x,1.,9961.)/0.152 + 0.5)),lambda x: pack_word(x)*.152),
                    ("btimeout4","H",500., lambda x: pack_word(word(clamp(x,1.,9961.)/0.152 + 0.5)),lambda x: pack_word(x)*.152),
                    ("btimeoutr","H",500., lambda x: pack_word(word(clamp(x,1.,9961.)/0.152 + 0.5)),lambda x: pack_word(x)*.152),
                    ("btimeoutd","H",0, lambda x: pack_word(word(clamp(x,1.,9961.)/0.152 + 0.5)),lambda x: pack_word(x)*.152),
                    ("miniperiod","H",500., lambda x:pack_word(word(65536.-(125000.0/clamp(x,2.0,625.0))+0.5)),lambda x:125000.0/(65536.0-(pack_word(x)))),
                    ("bto1p","H",200.,lambda x:pack_word(word(65536.-(125000.0/clamp(x,2.0,625.0))+0.5)),lambda x:125000.0/(65536.0-(pack_word(x)))),
                    ("bto2p","H",300.,lambda x:pack_word(word(65536.-(125000.0/clamp(x,2.0,625.0))+0.5)),lambda x:125000.0/(65536.0-(pack_word(x)))),
                    ("bto3p","H",400.,lambda x:pack_word(word(65536.-(125000.0/clamp(x,2.0,625.0))+0.5)),lambda x:125000.0/(65536.0-(pack_word(x)))),
                    ("bto4p","H",500.,lambda x:pack_word(word(65536.-(125000.0/clamp(x,2.0,625.0))+0.5)),lambda x:125000.0/(65536.0-(pack_word(x)))),
                    ("max_loft","H",32,lambda x:pack_word(word(clamp(x, 1, 1023 )*64)),lambda x: pack_word(x)/64),
                    ("startpos","I",0,startposfunc,istartposfunc),
                    ("rtdelta","H",200,lambda x:pack_word(word(clamp(x,4,1023)*64)),lambda x:pack_word(x)/64),
                    ("rtminerror","H",15,lambda x:pack_word(word(clamp(x,4,1023)*64)),lambda x:pack_word(x)/64),
                    ("maxtemp","H",70.,maxtempfunc,maxtempfunci),
                    ("sinoutp","B",1,None,None),
                    ("loftperiod","H",500.,loftperiodfunc,loftperiodfunci),
                    ("encvscp","B",2.5,lambda x: byte(x*4. +.5),lambda x: x/4.), #Encmul
                    ("reserved","15s","",None,None),
                    ]
        Easystruct.__init__(self,structdef,param_buf,**kwargs)
    
    
            
        
        
 

#~ typedef	struct	_DOWNLOAD_PACKET	// 65 bytes;
#~ {
	#~ __u8 Page;		// Page number ( 0 - 119 ). 0 - first, 119 - last.
	#~ __u8 Data [64];		// Data.
#~ } DOWNLOAD_PACKET, * PDOWNLOAD_PACKET, * LPDOWNLOAD_PACKET;
#~ 
#~ 
#~ typedef	struct	_SERIAL_PACKET	// 32 bytes;
#~ {
	#~ __u8 Password     [16];
	#~ __u8 SerialNumber [16];
#~ } SERIAL_PACKET, * PSERIAL_PACKET, * LPSERIAL_PACKET;


