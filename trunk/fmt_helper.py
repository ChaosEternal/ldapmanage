import ldif,StringIO,json
class FmtError(Exception):
    pass
class fmt_helper:
    def __init__(self):
        pass
    def load(self, x):
        return json.read(x)
    def export(self, x):
        return json.write(x)
    def export_multi(self,x,rf="\n"):
        return reduce(lambda x,y:"%s%s%s"%(x,rf,y), map(lambda x:self.export(x),x))
class fmt_ldif(fmt_helper):
    def load(self,x):
        _f=StringIO.StringIO(x)
        return ldif.ParseLDIF(_f)[0]
    def export(self,x):
        if x[1]=={}:
            return ldif.CreateLDIF(x[0],{None:[]})
        else:
            return ldif.CreateLDIF(x[0],x[1])
class fmt_csv(fmt_helper):
    def __init__(self, x, fs=":", vs=",", basedn="", oc=["inetOrgPerson"]):
            
        _fields=map(lambda x:x.strip(),x.split(fs))
        _dnf=filter(lambda x: x.find("#") >= 0 ,_fields)
        _dnf.sort(lambda x , y: int(x.split("#")[1] + "0") - int( y.split("#")[1] + "0") )

        self.fields=_fields
        self.dnf=map(lambda x:x.split("#")[0], _dnf)
        self.fs=fs
        self.vs=vs
        if basedn=="":
            self.basedn=""
        else:
            self.basedn=", " + basedn
        self.oc=oc
    def load(self,x):
        _raw=map( lambda x:[ y.strip() for y in x.split(self.vs)],
                  map( lambda x:x.strip(), x.split(self.fs)) )
        if len(self.fields) != len(_raw):
            raise FmtError, "number of fields mismatch."
        _sraw=map(lambda x: filter( lambda y: y!="",x) ,_raw)
        _rawmap=map( lambda x,y:(x,y),self.fields, _sraw)
        _rawdict=dict( filter(lambda x: x[1]!=[] and x[0]!="" , _rawmap))

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
        for i in self.fields:
            if _rawdict.has_key(i):
                _p1.append(reduce(lambda x,y:"%s%s%s"%(x,self.vs,y), _rawdict[i]))
            else:
                _p1.append("")
        _str=reduce(lambda x,y:x+self.fs+y,_p1)
        return _str
        pass

if __name__ == "__main__":
    e=fmt_csv("cn::uid:objectClass")
    f=e.load("chaos :a sd:c d ,e :top, ,posixAccount,inetOrgPerson")
    print f
    
    print e.export(f)
    lf=fmt_ldif()
    print lf.load("dn: o=cn\no: cn")
