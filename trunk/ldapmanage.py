#!/usr/bin/python
import ldap,shlex,cmd,getopt,traceback
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
        self.cwd="(no server)"
        self.cmds=["cd","ls","entry","add","modify","delete","base64","getdsa","init","exit","w","whoami","help","bind"]
        if uri!="":
            self._init(uri,bindmethod,binduser,cred,authzid)

    def _init(self, uri="ldapi:///", bindmethod="", binduser="", cred="", authzid=""):
        self.lc=ldap.initialize(uri)
        if bindmethod!="":
            self._bind(bindmethod, binduser, cred, authzid)
        self._refresh_dsa()

    def _refresh_dsa(self):
        self.dsa=self.lc.search_s("",ldap.SCOPE_BASE,"(objectClass=*)",["+","*"])
        self.namingContexts=self.dsa[0][1]["namingContexts"]
        debug( "We have namingcontexts at: \n   ", False)
        self.namingContexts.sort(lambda x,y:len(x)-len(y))
        for i in self.namingContexts:
            debug( "'%s'"%i, False)
            debug("")
        self.cwd=self.namingContexts[0]

    def _bind(self, bindmethod="external",binduser="", cred="", authzid=""):
        if bindmethod=="external":
            s=sasl.external()
            self.lc.sasl_interactive_bind_s("",s)
            self.me=self.lc.whoami_s()
            if self.me=="":
                self.me="(anonymous)"
            debug( "bind to ldap server at '%s' as '%s'"%(self.lc.get_option(ldap.OPT_URI), self.me) )
        if bindmethod=="simple":
            self.lc.simple_bind_s(binduser,cred)
        return


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
            try:
                s=raw_input(self.prompt)
            except EOFError,e:
                self.exit(["exit","eof"])
            cmd=shlex.split(s)
            if len(cmd)==0:
                continue
            if cmd[0] in self.cmds:
                try:
                    self.__getattribute__(cmd[0])(cmd)
                except Exception,e:
                    debug(type(e).__name__,":")
                    debug( e.args)
            else:
                error("no such command!")
    def cd(self,cmd):
        """usage: cd [path]
           path: null means goto root of the tree
                 "/" at the end of 'path' mean the path is absolute 
        """
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
        """usgae: entry [rdn]"""
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
        """usage: ls"""
        res=self.lc.search_s(self.cwd,ldap.SCOPE_ONELEVEL,"(objectClass=*)",["dn"])
        print res
    def getdsa(self,cmd):
        """usage: getdsa [-r]
        -r means reload dsa data from server, and will cause the cwd change
        """
        if len(cmd)>1 and cmd[1]=="-r":
            self._refresh_dsa()
        print self.dsa[0]
    def init(self,cmd):
        """usage: init [OPTS]...[LDAPURL]
            OPTS:
                -x: simple bind
                -y 'mech': sasl bind using mechanism 'mech'
                -z 'authzid': proxied authentication to 'authzid'
                -d 'binduser': bind using 'binduser', when simple bind, it is the dn
                -w 'password': bind using 'password'
            LDAPURL: default "ldapi:///"
        """
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
                print self.init.__doc__
                return
        if len(args)==0:
            uri="ldapi:///"
        else:
            uri=args[0]
#         if bindmech=="":
#             bindmech="external"
        if cmd[0]=="init":
            self._init(uri,bindmech,binduser,bindpw,authzid)
        else:
            if bindmech=="":
                bindmech="external"
            self._bind(bindmech,binduser,bindpw,authzid)
    def bind(self,cmd):
        """usage: bind [OPTS]...
            OPTS:
                -x: simple bind
                -y 'mech': sasl bind using mechanism 'mech'
                -z 'authzid': proxied authentication to 'authzid'
                -d 'binduser': bind using 'binduser', when simple bind, it is the dn
                -w 'password': bind using 'password'
        """
        self.init(cmd)

    def exit(self,cmd):
        """usage: exit"""
        import sys
        sys.exit(0)
    def w(self,cmd):
        """usage: w"""
        self.whoami(cmd)
    def whoami(self,cmd):
        """usage: whoami"""
        r=self.lc.whoami_s()
        print r
    def help(self,cmd):
        """usage: help [command]"""
        if len(cmd)>1:
            if cmd[1] in self.cmds:
                print self.__getattribute__(cmd[1]).__doc__
            else:
                print "help: No such command!"
        else:
            for i in self.cmds:
                print i

        

lm=ldapmanage()
lm.standby()
