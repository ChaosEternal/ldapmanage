#!/usr/bin/python

import ldif,re

def _debug(*x):
    return
    print x

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
        self._init_desc()
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
        self.parsed_fmdef=json.read(self.fmdef)
        
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
        self.rmapping=dict([ (x[1],x[0]) for x in self.parsed_fmdef[0]]  )
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
        
    def _run_policy(self, policy, data, lv={}):
        """_key=[
                "and",
        "or"
        ]
        _logic=[
        "not"]
        _condition=[
        "match",
        "gt",
        "lt"
        ]
        _verb=[
        "set",
        "add",
        "append",
        "output",
        "del",
        "+",
        "-",
        "stop",
        "filter",
        "reduce"
        ]
        _noun=[
        "valueof",
        "localvar",
        "string"
        ]
        """
        s,c,t,f=policy
        _debug(s,c,t,f)
        cb=True
        def valueof(x):
            _tleft=""
            _debug( "inpecting ", x)
            if x[0]=="valueof":
                if data[1].has_key(x[1]):
                    _tleft=data[1][x[1]]
            elif x[0]=="localvar":
                if lv.has_key(x[1]):
                    _tleft=[lv[x[1]]]
            elif x[0]=="string":
                if type(x[1])==type(""):
                    _tleft=[x[1]]
            _debug( "getting value",_tleft)
            return _tleft
                    
            
        def check(x):
            _t=False
            _tleft=valueof(x[2])
            _tright=valueof(x[3])
            if x[1]=="match":
                _tre=re.compile(_tright[0])
                for _it in _tleft:
                    _tmatching=_tre.match(_it)
                    if _tmatching:
                        _t=True
                        break
                    else:
                        _t=False

            if x[0]=="not":
                _t=not _t
            _debug( "condition result",_t)
            return _t
                
        def ex(x):
            _debug( "execing ", x)
            for _state in x:
                if type(_state)==type([]):
                    if _state[0] == "set":
                        if data[1].has_key(_state[1]):
                            data[1][_state[1]]=valueof(_state[2])
                    elif _state[0] == "append":
                        if data[1].has_key(_state[1]):
                            data[1][_state[1]].append(valueof(_state[2])[0])
                    elif _state[0] == "setvar":
                        lv[_state[1]]=valueof(_state[2])[0]
                    elif _state[0] == "cat":
                        if data[1].has_key(_state[1]):
                            _vr=valueof(_state[2])[0]
                            for _i in data[1][_state[1]]:
                                data[1][_state[1]] += _vr
                    elif _state[0] == "output":
                        _fs = _state[1]
                        if type(_fs)!=type(""):
                            _fs=","
                        _vr=valueof(_state[2])
                        if len(_vr) > 0:
                            self._output += reduce(lambda x,y: x+_fs+y, _vr)
            pass
        _debug ("""processing """, s)
        if s=="and":
            cb=True
            for i in c:
                _debug( "condition:",i)
                cb=cb and check(i)
        elif s=="or":
            cb=False
            for i in c:
                cb=cb or check(i)
        if cb:
            ex(t)
        else:
            ex(f)
        
            
    def mapper(self,data):
        self._run_policy(self.sub["output"][0],data)
        print self._output
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

if __name__ == '__main__':
    mydesc=[
        [], #mapping
        [], #filter
        {
            "output":
                [
                ["and",
                 [
                        ["","match",["valueof","a"],["string","b"]]
                        ], #conditions 
                 [
                        ["output",",",["valueof","a"]] 
                        ], #actions if true
                 [] # actions if false
                 ]
                ]
         }, #subscribe channel
        {}#publish channel
        ]
    s=json.write(mydesc)
    print s
    data=('dn',{"a":["b","c"]})
    a=lm_driver("name",s,"hello world")
    a._output=""
    a.mapper(data)
