import struct
from array import array

def getbit(num,bit=0):
    b=0x01<<bit
    return (num & b) ==b
    
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
    def __init__(self,state,dev_version=0x2400):
        
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

        fmt="HB"
        buf=struct.pack(fmt,
                          #dest_pos,
                          timer_period,
                          m1+2*m2+4*def_dir+8*loft_en+
                          16*sl_strt+32*w_sync+64*sync_out+128*force_loft)
        return buf
        
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





#~ typedef	struct	_ENCODER_STATE_PACKET	// 8 bytes;
#~ {
	#~ __u32 ECurPos;	// Current Position in Encoder Units.
	#~ __u32 EncPos;	// Encoder Current Position.
#~ } ENCODER_STATE_PACKET, * PENCODER_STATE_PACKET, * LPENCODER_STATE_PACKET;
#~ 
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
	#~ __u16 SYNCCOUNT;	// Number of steps after which synchronization output signal occurs.
#~ } MODE_PACKET, * PMODE_PACKET, * LPMODE_PACKET;
#~ 
#~ 
#~ typedef	struct	_PARAMETERS_PACKET	// 57 bytes;
#~ {
	#~ __u8  DELAY1;		// Acceleration time multiplier.
	#~ __u8  DELAY2;		// Deceleration time multiplier.
	#~ __u16 RefINTimeout;	// Timeout for RefIN reseting.
	#~ __u16 BTIMEOUT1;	// | Buttons Timeouts (4 stages).
	#~ __u16 BTIMEOUT2;	// |
	#~ __u16 BTIMEOUT3;	// |
	#~ __u16 BTIMEOUT4;	// |
	#~ __u16 BTIMEOUTR;	// Timeout for RESET command.
	#~ __u16 BTIMEOUTD;	// Timeout for Double Click.
	#~ __u16 MINPERIOD;	// Standart Timer Period.
	#~ __u16 BTO1P;		// | Timer Periods for button rotation.
	#~ __u16 BTO2P;		// |
	#~ __u16 BTO3P;		// |
	#~ __u16 BTO4P;		// |
	#~ __u16 MAX_LOFT;		// Max Loft Value.
	#~ __u32 STARTPOS;		// Start Position.
	#~ __u16 RTDelta;		// Revolution Distance.
	#~ __u16 RTMinError;	// Minimal value of Rotatory Tranduser Error.
	#~ __u16 MaxTemp;		// Working Temperature Limit.
	#~ __u8  SynOUTP;		// Syncronizaion OUT pulse duration( T = (sopd-1/2)*StepPeriod ).
	#~ __u16 LoftPeriod;	// Loft last phase speed.
	#~ __u8  EncVSCP;		// 4x Number of Encoder steps per one full SM step.
	#~ __u8  Reserved [15];	// Reserved.
#~ } PARAMETERS_PACKET, * PPARAMETERS_PACKET, * LPPARAMETERS_PACKET;
#~ 
#~ 
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


