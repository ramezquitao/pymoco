
import struct

class Easystruct:
    __structdef__ = [("primero","B",3),("segundo","i",30000)]
    
    
    def __init__(self,buf=None,**kwargs):
        
        #Create dinamically the attribs, the format string, and fill it
        #with the default values
        self.fmt=""
        for attr, tp, defv in self.__class__.__structdef__:
            setattr(self,attr,defv)
            self.fmt=self.fmt+tp
            
        if buf!=None:
            #if a buf is given, use its values to fill the structure
            assert kwargs=={}, "if kwargs are given, buf must be None"
            self.fillfrombuf(buf)
        else:
            #fill the values from kwargs
            for key in kwargs.keys():
                assert hasattr(self,key), "Triying to asign a non existing attribute to class "+ str(self.__class__)
                setattr(self,key,kwargs[key])
            
    
    def fillfrombuf(self,buf):
        """
        Fill the attributes using the values given in buf
        """
        
        upk=struct.unpack(self.__fmt__,buf)
        
        for val,attr in zip(upk,self.__class__.__structdef__):
            setattr(self,attr[0],val)

a=Easystruct(primero=0)
        
