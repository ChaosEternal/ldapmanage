import ldif,StringIO
class FmtError(Exception):
    pass
class fmt_helper:
    def __init__(self,desc="python"):
        self.desc="Format type:" + desc
        pass
    def load(self, x):
        pass
    def export(self, x):
        return repr(x)
    def export_multi(self,x,rf="\n"):
        return reduce(lambda x,y:"%s%s%s"%(x,rf,y), map(lambda x:self.export(x),x))
class fmt_ldif(fmt_helper):
    def __init__(self,desc="ldif"):
        fmt_helper.__init__(self, desc)
    def load(self,x):
        _f=StringIO.StringIO(x)
        return ldif.ParseLDIF(_f)[0]
    def export(self,x):
        if x[1]=={}:
            return ldif.CreateLDIF(x[0],{None:[]})
        else:
            return ldif.CreateLDIF(x[0],x[1])
class fmt_csv(fmt_helper):
    def __init__(self, x, fdflt="", fs=":", vs=",", basedn="", oc=["inetOrgPerson"],desc="csv"):
        fmt_helper.__init__(self,desc)
        self.desc+=", field seprator is '%s', value seprator is '%s'"%(fs,vs)+"\n   Fields definition:\""+ x + "\","
        if fdflt!="":
            self.desc+="\n Default input value definition:\"" + fdflt +"\","
        self.desc+="\n   BaseDn is \"" + basedn +"\","
        self.desc+="\n   Create objectClass is \""+reduce(lambda x,y:x+","+y,oc)+"\"."
            
        _fields=map(lambda x:x.strip(),x.split(fs))
        _dnf=filter(lambda x: x.find("#") >= 0 ,_fields)
        _dnf.sort(lambda x , y: int(x.split("#")[1] + "0") - int( y.split("#")[1] + "0") )

        _fields_p1=map(lambda x:x.split("#")[0], _fields)
        _outdflt=map(lambda x:(x+"%").split("%")[1], _fields_p1)
        _fields_p2=map(lambda x:x.split("%")[0], _fields_p1)

        self.fields=_fields_p2
        self.dnf=map(lambda x:x.split("#")[0], _dnf)
        self.fs=fs
        self.vs=vs
        self.outdflt=_outdflt
        if basedn=="":
            self.basedn=""
        else:
            self.basedn=", " + basedn
        self.oc=oc
        
        if fdflt!="":
            _indfltdict=self._load(fdflt)
            self.indfltdict=_indfltdict
        else:
            self.indfltdict=None

    def _load(self,x):
        _raw=map( lambda x:[ y.strip() for y in x.split(self.vs)],
                  map( lambda x:x.strip(), x.split(self.fs)) )
        if len(self.fields) != len(_raw):
            raise FmtError, "number of fields mismatch."
        _sraw=map(lambda x: filter( lambda y: y!="",x) ,_raw)
        _rawmap=map( lambda x,y:(x,y),self.fields, _sraw)
        _rawdict=dict( filter(lambda x: x[1]!=[] and x[0]!="" , _rawmap))
        return _rawdict
    
    def load(self,x):
        _rawdict = self._load(x)
        if self.indfltdict!=None:
            for i in self.indfltdict.keys():
                if not _rawdict.has_key(i):
                    _rawdict[i]=[]
                    for j in self.indfltdict[i]:
                        if j[0]!="$":
                            _rawdict[i].append(j)
                        else:
                            if _rawdict.has_key(j[1:]):
                                for k in _rawdict[j[1:]]:
                                    if not k in _rawdict[i]:
                                        _rawdict[i].append(k)
        for i in self.dnf:
            if _rawdict.has_key(i):
                _dn=i+"="+_rawdict[i][0]+self.basedn
                break
        else:
            for i in self.fields:
                if _rawdict.has_key(i):
                    _dn=i+"="+_rawdict[i][0]+self.basedn
                    break
            else:
                raise FmtError, "can't generate DN."
        if _rawdict.has_key("objectClass"):
            _ocdiff=filter(lambda x: not x in _rawdict["objectClass"],self.oc)
            _rawdict["objectClass"].extend(_ocdiff)
        else:
            _rawdict["objectClass"]=self.oc
        if _rawdict.has_key("dn"):
            _dn=_rawdict.pop("dn")[0]
        return (_dn, _rawdict)
            

    def export(self,x):
        _rawdict=x[1]
        _rawdict['dn']=x[0]
        _str=""
        _p1=[]
        for i in range(len(self.fields)):
            if _rawdict.has_key(self.fields[i]):
                _p1.append(reduce(lambda x,y:"%s%s%s"%(x,self.vs,y), _rawdict[self.fields[i]]))
            else:
                _p1.append(self.outdflt[i])
        _str=reduce(lambda x,y:x+self.fs+y,_p1)
        return _str
        pass

if __name__ == "__main__":
    e=fmt_csv("cn:%x:uid#:objectClass",fdflt="eternal::$cn:")
    f=e.load("chaos,eterna;:a sd::top, ,posixAccount,inetOrgPerson")
    print f
    
    print e.export(f)
    lf=fmt_ldif()
    print lf.load("dn: o=cn\no: cn")
