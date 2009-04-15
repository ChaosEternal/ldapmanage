class FmtError(Exception):
    pass
class fmt_helper:
    def __init__(self):
        pass
    def load(self, x):
        return json.read(x)
    def export(self, x):
        return json.write(x)

class fmt_csv(fmt_helper):
    def __init__(self, x, fs=":", vs=",", basedn=""):
            
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
        return [_dn, _rawdict]

if __name__ == "__main__":
    e=fmt_csv("cn::uid:oc")
    print e.load("chaos:asd:c,d,e:top,,inetOrgperson")
