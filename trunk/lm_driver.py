#!/usr/bin/python

import ldif


try:
    import json
except:
    print 'json module is unavailable'
    json=""

class lm_driver_error(Exception):
    pass

class lm_driver:
    """default driver is python __repr__"""
    def __init__(self, fm="",fmdef="",desc=""):
        self.fm=fm
        self.fmdef=fmdef
        self.desc=desc
        self.mapping=("","")
        self.filter=("",("",""))
        self.sub={"event":"","matching":"","cmd":"","output":""}
        self.pub={"event":"","matching":"","cmd":"","input":""}
    def _init_desc(self):
        """
        definition is [mapping, filter, sub, pub ]
        mapping is list of  tuples or dictionaries, [("src-attr","dest-attr")|("src-class.attr","dst-class.attr")]
        filter is list of tuple of tuples, or tuple of dictionaries [("P|S|D|N", "src","dst"]
        sub/pub lists of  policy sets: event, matching, cmd, output/input
        policy sets are lists of polices
        policy is list of actions
        action is tuple of "condition", "action", "action if condition failed"
        condition is one of (("if", "op","arg1","arg2"), (filter, op, arg1), (reduce, )
        action is list of verbs
        verb is one of ("stop","append(noun)","set (noun, noun)")
        
        """
        self.parsed_fmdef=json.load(self.fmdef)
        
        self._validate_map()
        
        self._validate_filter()

        for l in self.sub.keys():
            if self.parsed_fmdef[2].has_key(l):
                self.sub[l]=self.parsed_fmdef[2][l]
        for l in self.pub.keys():
            if self.parsed_fmdef[3].has_key(l):
                self.pub[l]=self.parsed_fmdef[3][l]
        pass

    def _validate_map(self):
        self.mapping=dict(self.parsed_fmdef[0])
        self.rmapping=dict([ (x[1],x[0]) for x in self.parsed_fmdef[0]) ] )
        if len(self.mapping)!=len(self.rmapping):
            raise lm_driver_error, "invalid mapping"

    def _validate_filter(self):
        _psdn={
        "P":1,
        "S":0,
        "N":0,
        "D":1
        }
        _rpsdn={
        "P":0,
        "S":1,
        "N":0,
        "D":1
        }

        self.filter=dict([( x[ 1 ][ 0 ], (x[ 1 ][ 1 ], _psdn[ x[ 0 ] ] )) for x in self.parsed_fmdef[ 1 ] ])
        self.rfilter=dict([(x[ 1 ][ 1 ], (x[ 1 ][ 0 ], _rpsdn[ x [ 0 ] ] )) for x in self.parsed_fmdef[ 1 ]])
        if len(self.filter)!=len(self.rfilter):
            raise lm_driver_error, "invalid filter"
    def _run_policy(self, policy, *data, lv={}):
        
            
    def mapping(self,data):
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
