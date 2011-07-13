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
     

class State(Easystruct):
    def __init__(self, modebuf=None, dev_version=0x2400, **kwargs):
        if dev_version <0x2400:
            def tempfunc(T):
                t=clamp(T,0.,100.)
                t = 10.0 * exp (3950.0*(1.0/(t+273.0)-1.0/298.0))
                t = ((5*t/(10+t))*65536.0/3.3+0.5);
                return t
            
            def tempfunci(T):
                t=float(t)
                t=t*3.3/ 65536.0
                t=10.0*t/(5.0-t)
                t=(1.0/298.0)+(1.0/3950.0)*log(t/10.0)
                t=1.0/t- 273.0
                return t

        else:
            def tempfunc(T):
                t=(T+50.0)/330.0*65536.0
                t=(t+0.5)   
                return t
                
            def tempfunci(T):
                t = float(T)
                t=(t*3.3*100.0/65536.0)-50.0
                return t
                
        def volt(vi):
            v= float(vi)/ 65536.0 * 3.3 * 20.0
            if v<5.: v=0
            return v

        
        structdef=[ ("curpos"   ,"i", 0x00, None, None), 
                    ("temp"     ,"H", 0x00, tempfunc, tempfunci),
                    ("s0"       ,"B", 0x00, None, None), 
                    ("s1"       ,"B", 0x00, None, None),
                    ("s2"       ,"B", 0x00, None, None),
                    ("voltage"  ,"H", 0x04, None,volt)]
        Easystruct.__init__(self,structdef,modebuf,checkargs=False,**kwargs)
        
        
    m1g=        lambda self:getbit(self.s0,0)         # | Step size is 2^(-M1-2*M2), where M1,M2 = 0,1. May be otherwise 1<->2.
    m2g=        lambda self:getbit(self.s0,1)         # |
    loftg=      lambda self:getbit(self.s0,2)       # Indicates "Loft State".
    refing=     lambda self:getbit(self.s0,3)      # If TRUE then full power.
    cw_ccwg=    lambda self:getbit(self.s0,4)     # Current direction. Relatively!
    emresetg=   lambda self:getbit(self.s0,5)      # If TRUE then Step Motor is ON.
    fullspeedg= lambda self:getbit(self.s0,6)  # If TRUE then full speed. Valid in "Slow Start" mode.
    aresetg=    lambda self:getbit(self.s0,7)   # TRUE After Device reset, FALSE after "Set Position".
    
    
    rung=       lambda self:getbit(self.s1,0)        # TRUE if step motor is rotating.
    syncing=    lambda self:getbit(self.s1,1)     # Logical state directly from input synchronization PIN (pulses treated as positive).
    syncoutg=   lambda self:getbit(self.s1,2)    # Logical state directly from output synchronization PIN (pulses are positive).
    rottrg=     lambda self:getbit(self.s1,3)      # Indicates current rotary transducer logical press state.
    rottrerrg=  lambda self:getbit(self.s1,4)   # Indicates rotary transducer error flag (reset by USMC_SetMode function with ResetRT bit  TRUE).
    emresetg=   lambda self:getbit(self.s1,5)    # Indicates state of emergency disable button (TRUE  Step motor power off).
    trailer1g=  lambda self:getbit(self.s1,6)   # Indicates trailer 1 logical press state.
    trailer2g=  lambda self:getbit(self.s1,7)   # Indicates trailer 2 logical press state.
    
    usbpowg=    lambda self:getbit(self.s2,0)     # USB Powered.
    #UNKNOWN   : 6;
    workingg=    lambda self:getbit(self.s2,7)    # This bit must be always TRUE (to chek functionality).
    
    
    m1          = property(m1g)        
    m2          = property(m2g)       
    loft        = property(loftg)     
    refin       = property(refing)
    cw_ccw      = property(cw_ccwg)
    emreset     = property(emresetg)
    fullspeed   = property(fullspeedg)
    areset      = property(aresetg)
    
    
    run         = property(rung)
    syncin      = property(syncing)
    syncout     = property(syncoutg)
    rottr       = property(rottrg)
    rottrerr    = property(rottrerrg)
    emreset     = property(emresetg)
    trailer1    = property(trailer1g)
    trailer2    = property(trailer2g)
    
    usbpow      = property(usbpowg)

    working     = property(workingg) 
    
class Serial:
    def __init__(self,data):
        st=array("B",data)
        #print data,st
        self.password=str(st[0:16])
        self.serial=str(st[16:])

class EncoderState:
    def __init__(self, data):
        st=array("B", data)
        fmt="=II"
        self.e_cur_pos, self.enc_pos= struct.unpack(fmt,st)

class Mode(Easystruct):
    def __init__(self, modebuf=None, **kwargs):
        structdef=[ ("b0","B",       0x01, None, None), 
                    ("b1","B",       0x03, None, None), 
                    ("b2","B",       0x05, None, None),
                    ("synccount","I",0x04, pack_dword, pack_dword),
                    ]
        Easystruct.__init__(self,structdef,modebuf,checkargs=False,**kwargs)
        for key in kwargs.keys():
                if hasattr(self,key):
                    setattr(self,key,kwargs[key])
                    kwargs.pop[key]
        
    def p0bs(self,bitn,bitv):
        mask= 1<<bitn
        if bitv: self.p0 = self.p0 | mask
        else:self.p0=self.p0 & ~mask
    
    def p1bs(self,bitn,bitv):
        mask= 1<<bitn
        if bitv: self.p1 = self.p1 | mask
        else:self.p1=self.p1 & ~mask
    
    def p2bs(self,bitn,bitv):
        mask= 1<<bitn
        if bitv: self.p2 = self.p2 | mask
        else:self.p2=self.p2 & ~mask
        
    pmodeg  =   lambda self: getbit(self.b0,0) 
    refineng=   lambda self: getbit(self.b0,1)
    resetdg =   lambda self: getbit(self.b0,2)
    emresetg=   lambda self: getbit(self.b0,3)
    tr1tg   =   lambda self: getbit(self.b0,4)
    tr2tg   =   lambda self: getbit(self.b0,5)
    rottrtg =   lambda self: getbit(self.b0,6)
    trswapg =   lambda self: getbit(self.b0,7)

    tr1eng  =   lambda self: getbit(self.b1,0)
    tr2eng  =   lambda self: getbit(self.b1,1)
    rettreng=   lambda self: getbit(self.b1,2)
    rottropg=   lambda self: getbit(self.b1,3)
    butt1tg =   lambda self: getbit(self.b1,4)
    butt2tg =   lambda self: getbit(self.b1,5)
    butswapg=   lambda self: getbit(self.b1,6)
    resetrtg=   lambda self: getbit(self.b1,7)

    sncouteng=   lambda self: getbit(self.b2,0)
    syncoutrg=   lambda self: getbit(self.b2,1)
    syncinopg=   lambda self: getbit(self.b2,2)
    syncopolg=   lambda self: getbit(self.b2,3)
    encoderg =   lambda self: getbit(self.b2,4)
    incvencg =   lambda self: getbit(self.b2,5)
    resbencg =   lambda self: getbit(self.b2,6)
    resencg  =   lambda self: getbit(self.b2,7)
    
    pmodes  =   lambda self,y: p0bs(self,0,y)  
    refinens=   lambda self,y: p0bs(self,1,y)  
    resetds =   lambda self,y: p0bs(self,2,y)  
    emresets=   lambda self,y: p0bs(self,3,y)
    tr1ts   =   lambda self,y: p0bs(self,4,y)
    tr2ts   =   lambda self,y: p0bs(self,5,y)
    rottrts =   lambda self,y: p0bs(self,6,y)
    trswaps =   lambda self,y: p0bs(self,7,y)

    tr1ens  =   lambda self,y: p1bs(self,0,y)
    tr2ens  =   lambda self,y: p1bs(self,1,y)
    rettrens=   lambda self,y: p1bs(self,2,y)
    rottrops=   lambda self,y: p1bs(self,3,y)
    butt1ts =   lambda self,y: p1bs(self,4,y)
    butt2ts =   lambda self,y: p1bs(self,5,y)
    butswaps=   lambda self,y: p1bs(self,6,y)
    resetrts=   lambda self,y: p1bs(self,7,y)

    sncoutens=   lambda self,y: p2bs(self,0,y)
    syncoutrs=   lambda self,y: p2bs(self,1,y)
    syncinops=   lambda self,y: p2bs(self,2,y)
    syncopols=   lambda self,y: p2bs(self,3,y)
    encoders =   lambda self,y: p2bs(self,4,y)
    incvencs =   lambda self,y: p2bs(self,5,y)
    resbencs =   lambda self,y: p2bs(self,6,y)
    resencs  =   lambda self,y: p2bs(self,7,y)
    
    pmode       = property(pmodeg, pmodes)
    refinen     = property(refineng, refinens)
    resetd      = property(resetdg, resetds)
    emreset     = property(emresetg, emresets)
    tr1t        = property(tr1tg, tr1ts)
    tr2t        = property(tr2tg, tr2ts)
    rottrt      = property(rottrtg, rottrts)
    trswap      = property(trswapg, trswaps)

    tr1en       = property(tr1eng, tr1ens)
    tr2en       = property(tr2eng, tr2ens)
    rettren     = property(rettreng, rettrens)
    rottrop     = property(rottropg, rottrops)
    butt1t      = property(butt1tg, butt1ts)
    butt2t      = property(butt2tg, butt2ts)
    butswap     = property(butswapg, butswaps)
    resetrt     = property(resetrtg, resetrts)

    sncouten    = property(sncouteng, sncoutens)
    syncoutr    = property(syncoutrg, syncoutrs)
    syncinop    = property(syncinopg, syncinops)
    syncopol    = property(syncopolg, syncopols)
    encoder     = property(encoderg, encoders)
    incvenc     = property(incvencg, incvencs)
    resbenc     = property(resbencg, resbencs)
    resenc      = property(resencg, resencs)
        
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


