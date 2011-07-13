import struct
class Easystruct(object):
    
    def __init__(self, structdef, buf=None, checkargs=True, **kwargs):
        """
        structdef a list of tuples containing:
        (att_name,att_type", def_val, class2buf, buf2class)
        
        att_name    String containing the attribute name
        att_type    String containing the attribute type as defined in the strunct module
        class2buf   Function to convert the value as represented in the class to buffer representation
        buf2class   Function to convert the value as represented in the buffer to class representation
        """
        
        #Create dinamically the attribs, the format string, and fill it
        #with the default values
        
        self.structdef=structdef
        
        self.fmt="="
        
        for attr, tp, defv, mod, mod1 in structdef:
            setattr(self,attr,defv)
            self.fmt=self.fmt+tp
            
        if buf!=None:
            #if a buf is given, use its values to fill the structure
            assert kwargs=={}, "if kwargs are given, buf must be None"
            self.fillfrombuf(buf)
        else:
            #fill the values from kwargs, only the values that belong to the new class
            #do not create new arguments
            for key in kwargs.keys():
                if hasattr(self,key):
                    setattr(self,key,kwargs[key])
                    kwargs.pop[key]
        if checkargs:
            assert  len(kwargs)==0, "Unknown arguments given"+str(kwargs)
            
    
    def fillfrombuf(self,buf):
        """
        Fill the attributes using the values given in buf
        """
        
        upk=struct.unpack(self.fmt,buf)
        
        for val,attr in zip(upk,self.structdef):
            a,tp,defv, mod, mod1 = attr
            if mod1==None:
                setattr(self,a,val)
            else:
                setattr(self,a,mod1(val))
    
    def tobuffer(self):
        bl=[]
        for attr, tp, defv, mod, mod1 in self.structdef:
            if mod== None:
                bl.append(getattr(self, attr))
            else:
                bl.append(mod(getattr(self, attr)))
                
        print len(bl),
        buf=struct.pack(self.fmt, *bl)
        return buf
        
#a=Easystruct(primero=0)
        
