#!/usr/bin/python
import ldap,shlex,cmd,getopt,traceback,sys,ldif
from ldap import sasl
class LdapManagerError(Exception):
    pass
class RdnError(LdapManagerError):
    pass

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
myprint=debug_message(1)


def computerdn(dn1,dn2):
    """return the rdn part of dn1 based on dn2"""
    a=ldap.explode_dn(dn1)
    b=ldap.explode_dn(dn2)
    if b=="":
        return dn1
    l_a=len(a)
    l_b=len(b)
    if l_a<l_b:
        raise RdnError, "Lenth of base dn is longer than the compared one."
    if a[l_a-l_b:]==b:
        if l_a!=l_b:
            return reduce(lambda x,y:x+", "+y, a[:l_a-l_b])
        else:
            return ""
    else:
        raise RdnError, "The dn is mismatch."

trans_scope={
    "base":ldap.SCOPE_BASE,
    "B":ldap.SCOPE_BASE,

    "one":ldap.SCOPE_ONELEVEL,
    "onelevel":ldap.SCOPE_ONELEVEL,
    "1":ldap.SCOPE_ONELEVEL,

    "subtree":ldap.SCOPE_SUBTREE,
    "sub":ldap.SCOPE_SUBTREE,
    "S":ldap.SCOPE_SUBTREE

    }

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
                except getopt.GetoptError,e:
                    debug(cmd[0]+":"+"%s"%e)
                except Exception,e:
                    raise
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
        """usage: ls [-pB1Sf] [-s base|one|sub] [-a attrlist] [filter]
        -p causes the output is raw python data
        -B, -1, -S: search scope is -s base,-s one,-s sub
        -s base|one|sub : specify the search scope to base, onelevel and subtree
        -a: the attributes need to be displayed, only valid when the output is python-mode
        -f: format the output as ldif
        """
        optlist,args=getopt.getopt(cmd[1:],"fpB1Ss:a:")
        rawoutput=False
        format=False
        scope=trans_scope["one"]
        attrs=["dn"]
        for o, a in optlist:
            if o=="-p":
                rawoutput=True
            if o=="-s":
                if not a in trans_scope.keys():
                    error("ls: invalid scope, should be one of 'base','one' and 'sub'")
                    return
                else:
                    scope=trans_scope[a]
                
            if o=="-B":
                scope=trans_scope["B"]
            if o=="-1":
                scope=trans_scope["1"]
            if o=="-S":
                scope=trans_scope["S"]
            if o=="-a":
                attrs=a.split(",")
            if o=="-f":
                format=True
        if len(args)>0:
            filter=args[0]
        else:
            filter="(objectClass=*)"

        res=self.lc.search_s(self.cwd,scope,filter,attrs)
        if rawoutput:
            print res
        elif format:
            if res[0][1]!={}:
                print ldif.CreateLDIF(res[0][0], res[0][1])
            else:
                print ldif.CreateLDIF(res[0][0],{"":[]})
        else:
            if res==[]:
                return

            if sys.stdout.isatty():
                print reduce(lambda x,y:x+"\t"+y,map(lambda x:computerdn(x[0],self.cwd),res))
            else:
                map(lambda x:myprint( computerdn(x[0],self.cwd)),res)
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
