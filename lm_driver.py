#!/usr/bin/python

import ldif


try:
    import json
except:
    print 'json module is unavailable'
    json=""

class lm_driver:
    """default driver is python __repr__"""
    def __init__(self, fm="",fmdef="",desc=""):
        self.fm=fm
        self.fmdef=fmdef
        self.desc=desc
        self.mapping=("","")
        self.filter=("",("",""))
        self.sub=["event","matching","cmd","output"]
        self.pub=["event","matching","cmd","input"]

    def mapping(self,i,o):
        pass
    
    def __call__(self, data, writer=""):
        if writer=="":
            writer=self.myprint
        if self.fm=="":
            writer(data.__repr__())
        if self.fm=="ldif":
            for i in data:
                if i[1]!={}:
                    writer(ldif.CreateLDIF(i[0],i[1]),0)
                else:
                    writer(ldif.CreateLDIF(i[0],{"":[]}),0)
        if self.fm=="json":
            import json
            writer(json.write(data))
