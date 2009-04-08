#!/usr/bin/python
import ldap,shlex,cmd,getopt
from ldap import sasl
class debug_message:
    def __init__(self,level=1):
        self.level=level
    def __call__(self, m,nl=True):
        if self.level>0:
            if nl:
                print m
            else:
                print m ,
debug=debug_message(1)
error=debug_message(1)

class ldapmanage(object):
    def __init__(self, uri="", bindmethod="external", binduser="", cred="", authzid=""):
        if uri!="":
            self._init(uri,bindmethod,binduser,cred,authzid)
        self.cmds=["cd","ls","entry","add","modify","delete","base64","showdsa","init"]
        self.cwd="(no server)"

    def _init(self, uri="", bindmethod="external", binduser="", cred="", authzid=""):
        self.lc=ldap.initialize(uri)
        if bindmethod=="external":
            s=sasl.external()
            self.lc.sasl_interactive_bind_s("",s)
            self.me=self.lc.whoami_s()
            if self.me=="":
                self.me="(anonymous)"
            debug( "bind to ldap server at '%s' as '%s'"%(self.lc.get_option(ldap.OPT_URI), self.me) )

        self.dsa=self.lc.search_s("",ldap.SCOPE_BASE,"(objectClass=*)",["+","*"])
        self.namingContexts=self.dsa[0][1]["namingContexts"]
        debug( "We have namingcontexts at: \n   ", False)
        self.namingContexts.sort(lambda x,y:len(x)-len(y))
        for i in self.namingContexts:
            debug( "'%s'"%i, False)
            debug("")
        self.cwd=self.namingContexts[0]

    def checkexist(self,dn):
        try:
            res=self.lc.search_s(dn,ldap.SCOPE_BASE,"(objectClass=*)",["dn"])
        except:
            res=[]
        if res==[]:
            return False
        else:
            return True
    def standby(self):
        while True:
            self.prompt="'%s'=> "%self.cwd
            s=raw_input(self.prompt)
            cmd=shlex.split(s)
            if len(cmd)==0:
                continue
            if cmd[0] in self.cmds:
                self.__getattribute__(cmd[0])(cmd)
            else:
                error("no such command!")
    def cd(self,cmd):
        if len(cmd)>1:
            path=cmd[1]
            if path[-1]=="/":
                newcwd=path[0:-1]
            else:
                if self.cwd=="":
                    newcwd=path
                else:
                    newcwd=path+","+self.cwd
            if self.checkexist(newcwd):
                self.cwd=newcwd
            else:
                error("no such entry!")
        else:
            self.cwd=self.namingContexts[0]
    def entry(self,cmd):
        if len(cmd)>1:
            if self.cwd=="":
                entrydn=cmd[1]
            else:
                entrydn=cmd[1]+","+self.cwd
        else:
            entrydn=self.cwd
        res=self.lc.search_s(entrydn,ldap.SCOPE_BASE,"(objectClass=*)")
        print res
    def ls(self,cmd):
        res=self.lc.search_s(self.cwd,ldap.SCOPE_ONELEVEL,"(objectClass=*)",["dn"])
        print res
    def showdsa(self,cmd):
        print self.dsa[0]
    def init(self,cmd):
        bindmech=""
        binduser=""
        bindpw=""
        authzid=""
        optlist,args=getopt.getopt(cmd[1:],"xhy:z:d:w:")
        for o, a in optlist:
            if o=="-x":
                if bindmech!="simple" and bindmech!="":
                    error("conflict args: -x")
                    return
                bindmech="simple"
            if o=="-y":
                if bindmech=="simple":
                    error("conflict args: -y")
                    return
                bindmech=a
            if o=="-z":
                authzid=a
            if o=="-d":
                binduser=a
            if o=="-w":
                bindpw=a
            if o=="-h":
                debug("""usage: init [OPTS]...[LDAPURL]""")
                debug("""OPTS:""")
                debug("""    -x: simple bind""")
                debug("""    -y 'mech': sasl bind using mechanism 'mech'""")
                debug("""    -z 'authzid': proxied authentication to 'authzid'""")
                debug("""    -d 'binduser': bind using 'binduser', when simple bind, it is the dn""")
                debug("""    -w 'password': bind using 'password'""")
                debug("""LDAPURL: default "ldapi:///" """)
            return
        if len(args)==0:
            uri="ldapi:///"
        else:
            uri=args[0]
        if bindmech=="":
            bindmech="external"
        self._init(uri,bindmech,binduser,bindpw,authzid)
        

lm=ldapmanage()
lm.standby()
