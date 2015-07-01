'''
    Copyright (C) 2014 Parrot SA

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions
    are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in
      the documentation and/or other materials provided with the 
      distribution.
    * Neither the name of Parrot nor the names
      of its contributors may be used to endorse or promote products
      derived from this software without specific prior written
      permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
    FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
    COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
    INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
    BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
    OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED 
    AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
    OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
    SUCH DAMAGE.
'''
from xml.dom.minidom import parseString
import sys
import re
from ARFuncs import *
if sys.version_info < (3,):
    from urlparse import urlparse
else:
    from urllib.parse import urlparse
import posixpath

#
# Repo object definition
#

class ARRepo:
    "Represent a repo of the ARSDK 3"
    def __init__(self, reponame, revision="master", isExternal=False, isExtraRepo=False):
        self.name = reponame
        self.rev = revision
        self.ext = isExternal
        self.extra = isExtraRepo
        self.forceBaseUrl = False
        self.path = None
        self.patches = []
        self.additionnalCommands = []
    def setForceBaseUrl(self):
        self.forceBaseUrl = True
    def getDir(self):
        if self.path:
            return ARPathFromHere(self.path)
        elif self.ext:
            foldername = re.sub(r'.*/(.*).git', r'\1', self.name)
            return ARPathFromHere('../%(foldername)s' % locals())
        else:
            foldername = re.sub(r'.*/(.*)', r'\1', self.name)
            return ARPathFromHere('../%(foldername)s' % locals())
    def addPatchFile(self, patchFile):
        if not patchFile in self.patches:
            self.patches.append(patchFile)
    def addCommand(self, command):
        self.additionnalCommands.append (command)
    def setPath(self, path):
        self.path = path
    def describe(self, level=0):
        prefix = ''
        for i in range(0, level):
            prefix = prefix + ' '
        if self.path:
            ARPrint(prefix + 'ARRepo > Name : ' + self.name + ' | Revision : ' + self.rev + ' | Path : ' + self.path)
        else:
            ARPrint(prefix + 'ARRepo > Name : ' + self.name + ' | Revision : ' + self.rev)
        for pf in self.patches:
            ARPrint(prefix + '         Patch : ' + pf)
        for cmd in self.additionnalCommands:
            ARPrint(prefix + '  - Post download command : ' + cmd)
    def __str__(self):
        return self.name

#
# Webfile object definition
#

class ARWebfile:
    "Represent a file that must be downloaded from the web"
    def __init__(self, url, storePath):
        self.name = posixpath.basename(urlparse(url).path)
        self.url = url
        self.storePath = ARPathFromHere(storePath)
        self.additionnalCommands = []
        self.patches = []
    def addPatchFile(self, patchFile):
        if not patchFile in self.patches:
            self.patches.append(patchFile)
    def addCommand(self, command):
        self.additionnalCommands.append (command)
    def describe(self, level=0):
        prefix = ''
        for i in range(0, level):
            prefix = prefix + ' '
        ARPrint(prefix + 'ARWebfile > Name : ' + self.name + ' | Url : ' + self.url + ' | Store path : ' + self.storePath)
        for pf in self.patches:
            ARPrint(prefix + '  - Patch : ' + pf)
        for cmd in self.additionnalCommands:
            ARPrint(prefix + '  - Post download command : ' + cmd)

#
# Repos list storage
#

class ARReposList:
    "List of repos for ARSDK 3"
    def __init__(self):
        self.list = []
        self.webfilesList = []
    def contains(self, repo):
        res = False
        for trep in self.list:
            if trep == repo:
                res = True
                break
        return res
    def addRepo(self, repo):
        if self.contains(repo):
            ARPrint('Repo %(repo)s is already in list' % locals())
            EXIT(1)
        self.list.append(repo)
    def getRepo(self, name, silent=False):
        for rep in self.list:
            if rep.name == name:
                return rep
        if not silent:
            ARPrint('Repo %(name)s does not exist in list' % locals())
            EXIT(1)
        else:
            raise Exception
    def containsWebfile(self, webfile):
        res = False
        for trep in self.webfilesList:
            if trep == webfile:
                res = True
                break
        return res
    def addWebfile(self, webfile):
        if self.containsWebfile(webfile):
            ARPrint('Webfile %(webfile)s is already in list' % locals())
            EXIT(1)
        self.webfilesList.append(webfile)
    def getWebfile(self, name, silent=False):
        for rep in self.webfilesList:
            if rep.name == name:
                return rep
        if not silent:
            ARPrint('Webfile %(name)s does not exist in list' % locals())
            EXIT(1)
        else:
            raise Exception
    def dump(self):
        ARPrint('REPOS : {')
        for repo in self.list:
            repo.describe()
        ARPrint('}')
        ARPrint('WEB FILES : {')
        for _file in self.webfilesList:
            _file.describe()
        ARPrint('}')

#
# Target object definition
#

class ARTarget:
    "Represent a target of the ARSDK 3"
    def __init__(self, targetname, soext):
        self.name = targetname
        self.alreadyBuiltLibraries = []
        self.triedToBuildLibraries = []
        self.alreadyBuiltBinaries = []
        self.triedToBuildBinaries = []
        self.postbuildScripts = []
        self.failed = False
        if soext == '__HOST__':
            platform = sys.platform
            plow = platform.lower()
            if plow.startswith('linux'):
                self.soext = 'so'
            elif plow == 'darwin':
                self.soext = 'dylib'
            elif plow == 'windows':
                self.soext = 'dll'
            else:
                self.soext = None
        else:
            self.soext = soext
    def addTriedLibrary(self, lib):
        if not lib.name in self.triedToBuildLibraries:
            self.triedToBuildLibraries.append(lib.name)
    def hasTriedToBuild(self, lib):
        return lib.name in self.triedToBuildLibraries
    def addBuiltLibrary(self, lib):
        if not lib.name in self.alreadyBuiltLibraries:
            self.alreadyBuiltLibraries.append(lib.name)
    def needsToBuild(self, lib):
        return not self.hasAlreadyBuilt(lib)
    def hasAlreadyBuilt(self, lib):
        return lib.name in self.alreadyBuiltLibraries
    def addTriedBinary(self, lib):
        if not lib.name in self.triedToBuildBinaries:
            self.triedToBuildBinaries.append(lib.name)
    def hasTriedToBuildBinary(self, lib):
        return lib.name in self.triedToBuildBinaries
    def addBuiltBinary(self, lib):
        if not lib.name in self.alreadyBuiltBinaries:
            self.alreadyBuiltBinaries.append(lib.name)
    def hasAlreadyBuiltBinary(self, lib):
        return lib.name in self.alreadyBuiltBinaries
    def addPostbuildScript(self, script, name):
        self.postbuildScripts.append({'path':script, 'name':name,  'done':None})
    def describe(self, level=0):
        prefix = ''
        for i in range(0, level):
            prefix = prefix + ' '
        ARPrint(prefix + 'ARTarget > Name : ' + self.name)
        ARPrint(prefix + '           Shared Object ext : ' + self.soext)
        for scrinfo in self.postbuildScripts:
            scr = scrinfo['path']
            ARPrint(prefix + '           Postbuild script  : ' + scr) 
    def __str__(self):
        return self.name

#
# Targets list storage
#

class ARTargetsList:
    "List of targets for ARSDK 3"
    def __init__(self):
        self.list = []
    def contains(self, target):
        res = False
        for ttar in self.list:
            if ttar == target:
                res = True
                break
        return res
    def addTarget(self, target):
        if self.contains(target):
            ARPrint('Target %(target)s is already in list' % locals())
            raise Exception
        self.list.append(target)
    def getTarget(self, name, silent=False):
        for tar in self.list:
            if tar.name == name:
                return tar
        if not silent:
            ARPrint('Target %(name)s does not exist in list' % locals())
            EXIT(1)
        else:
            raise Exception
    def dump(self):
        ARPrint('TARGETS : {')
        for target in self.list:
            target.describe()
        ARPrint('}')

#
# Prebuilt object definition
#

class ARPrebuilt:
    "Represent a prebuilt library for the ARSDK 3"
    def __init__(self, name, fileType, path):
        self.name = name
        if path.startswith('/'):
            self.path = path
        else:
            self.path = ARPathFromHere(path)
        self.type = fileType
        self.targets = []
    def addTarget(self, target):
        if not target in self.targets:
            self.targets.append(target)
    def isAvailableForTarget(self, target):
        ret = False
        if not self.targets:
            ret = True # No target set means all targets are OK
        else:
            for tar in self.targets:
                if tar.name == target.name:
                    ret = True
                    break
        return ret
    def ARCopy(self, newTargets):
        ret = ARPrebuilt(self.name, self.type, self.path)
        if not newTargets:
            for t in self.targets:
                ret.addTarget(t)
        else:
            for t in newTargets:
                if self.isAvailableForTarget(t):
                    ret.addTarget(t)
                else:
                    ARPrint('Target %(t)s is not a valid target for %(ret)s' % locals())
                    EXIT(1)
        return ret
    def describe(self, level=0):
        offset = len('ARPrebuilt > ')
        prefix = ''
        for i in range(0, level):
            prefix = prefix + ' '
        ARPrint(prefix + 'ARPrebuilt > Name : ' + self.name)
        ARPrint(prefix + '             Path : ' + self.path)
        ARPrint(prefix + '             Type : ' + self.type)
        ARPrint(prefix + '             Targets {')
        for t in self.targets:
            t.describe(level+offset+4)
        ARPrint(prefix + '             }')
    def __str__(self):
        return self.name

#
# Prebuilt list storage
#

class ARPrebuiltList:
    "List of prebuilt libraries for ARSDK 3"
    def __init__(self):
        self.list = []
    def contains(self, pb):
        return self.containsName(pb.name)
    def containsName(self, name):
        res = False
        for tpb in self.list:
            if tpb.name == name:
                res = True
                break
        return res
    def addPrebuilt(self, pb):
        if self.contains(pb):
            ARPrint('Prebuilt library %(pb)s is already in list' % locals())
            EXIT(1)
        self.list.append(pb)
    def getPrebuilt(self, name, silent=False):
        for pb in self.list:
            if pb.name == name:
                return pb
        if not silent:
            ARPrint('Prebuilt library %(pb)s does not exists in list' % locals())
            EXIT(1)
        else:
            raise Exception
    def dump(self):
        ARPrint('PREBUILT LIBS : {')
        for pb in self.list:
            pb.describe()
        ARPrint('}')

#
# Library object definition
#

class ARLibrary:
    "Represent a library of the ARSDK 3"
    def __init__(self, libname, isExternal=False, extPath="", customBuild=None):
        self.name = libname
        self.deps = []
        self.pbdeps = []
        self.ext = isExternal
        self.extraConfFlags = []
        self.confdeps = []
        self.targets = []
        self.soLibs = []
        self.hasBaseSoLibs = False
        self.customBuild = customBuild
        if extPath:
            self.relativePath = extPath
        else:
            self.relativePath = '../lib' + self.name
        self.path = ARPathFromHere(self.relativePath)
    def addConfDep(self, confdep):
        if not confdep in self.confdeps:
            self.confdeps.append(os.path.join(self.path,confdep))
    def addDep(self, dep):
        if dep.name == self.name:
            ARPrint('Cyclical dependancy in lib' + self.name)
            EXIT(1)
        if not dep in self.deps:
            self.deps.append(dep)
    def addPrebuiltDep(self, dep):
        if not dep in self.pbdeps:
            self.pbdeps.append(dep)
    def addExtraConfFlag(self, flag):
        self.extraConfFlags.append(flag)
    def addTarget(self, target):
        if not target in self.targets:
            self.targets.append(target)
    def isAvailableForTarget(self, target):
        ret = False
        if not self.targets:
            ret = True # No target set means all targets are OK
        else:
            for tar in self.targets:
                if tar.name == target.name:
                    ret = True
                    break
        return ret
    def runOnAllDeps(self, target, func, firstLevel=True, **kwargs):
        for dep in self.deps:
            if dep.isAvailableForTarget(target):
                dep.runOnAllDeps(target, func, False, **kwargs)
        if not firstLevel:
            func(target, self, **kwargs)
    def ARCopy(self, newTargets):
        ret = ARLibrary(self.name, self.ext, self.relativePath, self.customBuild)
        for cd in self.confdeps:
            ret.addConfDep(cd)
        for d in self.deps:
            ret.addDep(d.ARCopy(newTargets))
        for pb in self.pbdeps:
            ret.addPrebuiltDep(pb.ARCopy(newTargets))
        for ecf in self.extraConfFlags:
            ret.addExtraConfFlag(ecf)
        ret.soLibs = self.soLibs
        if not newTargets:
            for t in self.targets:
                ret.addTarget(t)
        else:
            for t in newTargets:
                if self.isAvailableForTarget(t):
                    ret.addTarget(t)
                else:
                    ARPrint('Target %(t)s is not a valid target for %(ret)s' % locals())
                    EXIT(1)
        return ret
    def describe(self, level=0):
        offset = len('ARLibrary > ')
        prefix = ''
        for i in range(0, level):
            prefix = prefix + ' '
        ARPrint(prefix + 'ARLibrary > Name : ' + self.name)
        ARPrint(prefix + '            Ext  : ' + str(self.ext))
        ARPrint(prefix + '            Path : ' + self.path)
        ARPrint(prefix + '            Deps {')
        for d in self.deps:
            d.describe(level+offset+4)
        ARPrint(prefix + '            }')
        ARPrint(prefix + '            Prebuilts {')
        for pb in self.pbdeps:
            pb.describe(level+offset+4)
        ARPrint(prefix + '            }')
        ARPrint(prefix + '            ExtraConfFlags {')
        for cf in self.extraConfFlags:
            ARPrint(prefix + '                ' + cf)
        ARPrint(prefix + '            }')
        ARPrint(prefix + '            Conf Deps {')
        for cd in self.confdeps:
            ARPrint(prefix + '                ' + cd)
        ARPrint(prefix + '            }')
        ARPrint(prefix + '            Targets {')
        for t in self.targets:
            t.describe(level+offset+4)
        ARPrint(prefix + '            }')
    def __str__(self):
        return self.name
    def clearCache(self):
        if not self.hasBaseSoLibs:
            del self.soLibs[:]

#
# Libraries list storage
#

class ARLibrariesList:
    "List of libraries for ARSDK 3"
    def __init__(self):
        self.list = []
    def contains(self, lib):
        return self.containsName(lib.name)
    def containsName(self, name):
        res = False
        for tlib in self.list:
            if tlib.name == name:
                res = True
                break
        return res
    def addLib(self, lib):
        if self.contains(lib):
            ARPrint('Library lib%(lib)s is already in list' % locals())
            EXIT(1)
        self.list.append(lib)
    def getLib(self, name, silent=False):
        for lib in self.list:
            if lib.name == name:
                return lib
        if not silent:
            ARPrint('Library lib%(name)s does not exist in list' % locals())
            EXIT(1)
        else:
            raise Exception
    def dump(self):
        ARPrint('LIBS : {')
        for lib in self.list:
            lib.describe()
        ARPrint('}')
    def clearCache(self):
        for lib in self.list:
            lib.clearCache()

#
# Binary object definition
#

class ARBinary:
    "Represent a binary of the ARSDK 3"
    def __init__(self, binname, builddir):
        self.name = binname
        self.deps = []
        self.targets = []
        self.extraConfFlags = []
        self.confdeps = []
        self.relativePath = builddir
        self.path = ARPathFromHere(builddir)
        self.ext = False
        self.soLibs = []
        self.customBuild = None
        
    def addDep(self, dep):
        if not dep in self.deps:
            self.deps.append(dep)
    def addExtraConfFlag(self, flag):
        self.extraConfFlags.append(flag)
    def addTarget(self, target):
        if not target in self.targets:
            self.targets.append(target)
    def isAvailableForTarget(self, target):
        ret = False
        if not self.targets:
            ret = True # No target set means all targets are OK
        else:
            for tar in self.targets:
                if tar.name == target.name:
                    ret = True
                    break
        return ret
    def runOnAllDeps(self, target, func, firstLevel=True, **kwargs):
        for dep in self.deps:
            if dep.isAvailableForTarget(target):
                dep.runOnAllDeps(target, func, False, **kwargs)
        if not firstLevel:
            func(target, self, **kwargs)
    def ARCopy(self, newTargets):
        ret = ARBinary(self.name, self.relativePath)
        for d in self.deps:
            ret.addDep(d.ARCopy())
        for ecf in self.extraConfFlags:
            ret.addExtraConfFlag(ecf)
        ret.soLibs = self.soLibs
        if not newTargets:
            for t in self.targets:
                ret.addTarget(t)
        else:
            for t in newTargets:
                if self.isAvailableForTarget(t):
                    ret.addTarget(t)
                else:
                    ARPrint('Target %(t)s is not a valid target for %(ret)s' % locals())
                    EXIT(1)
        return ret
    def describe(self, level=0):
        offset = len('ARBinary > ')
        prefix = ''
        for i in range(0, level):
            prefix = prefix + ' '
        ARPrint(prefix + 'ARBinary > Name : ' + self.name)
        ARPrint(prefix + '           Path : ' + self.path)
        ARPrint(prefix + '           Deps {')
        for d in self.deps:
            d.describe(level+offset+4)
        ARPrint(prefix + '           }')
        ARPrint(prefix + '           ExtraConfFlags {')
        for cf in self.extraConfFlags:
            ARPrint(prefix + '               ' + cf)
        ARPrint(prefix + '           }')
        ARPrint(prefix + '           Conf Deps {')
        for cd in self.confdeps:
            ARPrint(prefix + '               ' + cd)
        ARPrint(prefix + '           }')
        ARPrint(prefix + '           Targets {')
        for t in self.targets:
            t.describe(level+offset+4)
        ARPrint(prefix + '           }')
    def __str__(self):
        return self.name
    def clearCache(self):
        del self.soLibs[:]


#
# Binaries list storage
#

class ARBinariesList:
    "List of binaries for ARSDK 3"
    def __init__(self):
        self.list = []
    def contains(self, bin):
        return self.containsName(bin.name)
    def containsName(self, name):
        res = False
        for tbin in self.list:
            if tbin.name == name:
                res = True
                break
        return res
    def addBin(self, bin):
        if self.contains(bin):
            ARPrint('Binary %(bin)s is already in list' % locals())
            EXIT(1)
        self.list.append(bin)
    def getBin(self, name, silent=False):
        for bin in self.list:
            if bin.name == name:
                return bin
        if not silent:
            ARPrint('Binary %(name)s does not exist in list' % locals())
            EXIT(1)
        else:
            raise Exception
    def dump(self):
        ARPrint('BIN : {')
        for bin in self.list:
            bin.describe()
        ARPrint('}')
    def clearCache(self):
        for bin in self.list:
            bin.clearCache()

#
# Parsers
#

def parseRepoXmlFile(paths):

    repos = ARReposList()

    for root_path in paths:
        path = '%(root_path)s/repos.xml' % locals()

        xfile=open(path, 'r')
        xdata=xfile.read()
        xfile.close()

        xmldata = parseString(xdata)

        xrepos = xmldata.getElementsByTagName('repo')
        for xrepo in xrepos:
            repo = ARRepo(xrepo.attributes['name'].nodeValue, xrepo.attributes['rev'].nodeValue)
            try:
                repo.setPath(xrepo.attributes['path'].nodeValue)
            except:
                pass
            try:
                if xrepo.attributes['forceBaseUrl'].nodeValue == 'TRUE':
                    repo.setForceBaseUrl()
            except:
                pass
            xpatches = xrepo.getElementsByTagName('patchFile')
            for xpatch in xpatches:
                repo.addPatchFile(xpatch.attributes['path'].nodeValue)
            xcmds = xrepo.getElementsByTagName('postDownloadAction')
            for xcmd in xcmds:
                repo.addCommand(xcmd.attributes['command'].nodeValue)
            repos.addRepo(repo)

        xrepos = xmldata.getElementsByTagName('extrarepo')
        for xrepo in xrepos:
            repo = ARRepo(xrepo.attributes['url'].nodeValue, xrepo.attributes['rev'].nodeValue, isExternal=True, isExtraRepo=True)
            try:
                repo.setPath(xrepo.attributes['path'].nodeValue)
            except:
                pass
            xpatches = xrepo.getElementsByTagName('patchFile')
            for xpatch in xpatches:
                repo.addPatchFile(xpatch.attributes['path'].nodeValue)
            xcmds = xrepo.getElementsByTagName('postDownloadAction')
            for xcmd in xcmds:
                repo.addCommand(xcmd.attributes['command'].nodeValue)
            repos.addRepo(repo)

        xrepos = xmldata.getElementsByTagName('extrepo')
        for xrepo in xrepos:
            repo = ARRepo(xrepo.attributes['url'].nodeValue, xrepo.attributes['rev'].nodeValue, isExternal=True)
            xpatches = xrepo.getElementsByTagName('patchFile')
            for xpatch in xpatches:
                repo.addPatchFile(xpatch.attributes['path'].nodeValue)
            xcmds = xrepo.getElementsByTagName('postDownloadAction')
            for xcmd in xcmds:
                repo.addCommand(xcmd.attributes['command'].nodeValue)
            repos.addRepo(repo)

        xrepos = xmldata.getElementsByTagName('webfile')
        for xrepo in xrepos:
            webfile = ARWebfile(xrepo.attributes['url'].nodeValue, xrepo.attributes['storePath'].nodeValue)
            xpatches = xrepo.getElementsByTagName('patchFile')
            for xpatch in xpatches:
                webfile.addPatchFile(xpatch.attributes['path'].nodeValue)
            xcmds = xrepo.getElementsByTagName('postDownloadAction')
            for xcmd in xcmds:
                webfile.addCommand(xcmd.attributes['command'].nodeValue)
            repos.addWebfile(webfile)

    return repos

def parseTargetsXmlFile(paths):

    targets = ARTargetsList()

    for root_path in paths:
        path = '%(root_path)s/targets.xml' % locals()

        xfile=open(path, 'r')
        xdata=xfile.read()
        xfile.close()

        xmldata = parseString(xdata)

        xtargets = xmldata.getElementsByTagName('target')
        for xtarget in xtargets:
            needToAdd = True
            try:
                target = targets.getTarget(xtarget.attributes['name'].nodeValue, silent=True)
                needToAdd = False
            except:
                target = ARTarget(xtarget.attributes['name'].nodeValue, xtarget.attributes['soext'].nodeValue)
            xscrs = xtarget.getElementsByTagName('postbuildscript')
            for xscr in xscrs:
                target.addPostbuildScript(os.path.join(root_path, xscr.attributes['name'].nodeValue), xscr.attributes['name'].nodeValue)

            if needToAdd:
                targets.addTarget(target)

    return targets

def parsePrebuiltXmlFile(paths, targets):

    prebuilts = ARPrebuiltList()
    
    for root_path in paths:
        path = '%(root_path)s/prebuilt.xml' % locals()

        xfile=open(path, 'r')
        xdata=xfile.read()
        xfile.close()

        xmldata = parseString(xdata)

    
        xprebuilts = xmldata.getElementsByTagName('prebuilt')
        for xpb in xprebuilts:
            needToAdd = True
            try:
                pb = prebuilts.getPrebuilt(xpb.attributes['name'].nodeValue, silent=True)
                needToAdd = False
            except:
                pb = ARPrebuilt(xpb.attributes['name'].nodeValue, xpb.attributes['type'].nodeValue, xpb.attributes['path'].nodeValue)
            xtars = xpb.getElementsByTagName('validtar')
            for xtar in xtars:
                pb.addTarget(targets.getTarget(xtar.attributes['name'].nodeValue))
            if needToAdd:
                prebuilts.addPrebuilt(pb)

    return prebuilts

def parseLibraryXmlFile(paths, targets, prebuilts):

    libraries = ARLibrariesList()

    for root_path in paths:
        path = '%(root_path)s/libraries.xml' % locals()

        xfile=open(path, 'r')
        xdata=xfile.read()
        xfile.close()

        xmldata = parseString(xdata)

        xlibraries = xmldata.getElementsByTagName('extlib')
        for xlib in xlibraries:
            needToAdd = True
            try:
                lib = libraries.getLib(xlib.attributes['name'].nodeValue, silent=True)
                needToAdd = False
            except:
                lib = ARLibrary(xlib.attributes['name'].nodeValue, isExternal=True, extPath=xlib.attributes['path'].nodeValue)
            xdeps = xlib.getElementsByTagName('dep')
            for xdep in xdeps:
                ltargets = []
                xtars = xdep.getElementsByTagName('validdeptar')
                for xtar in xtars:
                    ltargets.append(targets.getTarget(xtar.attributes['name'].nodeValue))
                lib.addDep(libraries.getLib(xdep.attributes['name'].nodeValue).ARCopy(ltargets))
            hasCustomBuild = False
            if xlib.hasAttribute('customBuild') and xlib.attributes['customBuild'].nodeValue is not None:
                lib.customBuild = xlib.attributes['customBuild'].nodeValue
                hasCustomBuild = True
            xsofiles = xlib.getElementsByTagName('sofile')
            if xsofiles and not hasCustomBuild:
                ARPrint('You can not use sofile in a library without a customBuild script !')
                raise OSError
            for xsofile in xsofiles:
                lib.soLibs.append(xsofile.attributes['name'].nodeValue)
                lib.hasBaseSoLibs = True
            xtargets = xlib.getElementsByTagName('validtar')
            for xtarget in xtargets:
                lib.addTarget(targets.getTarget(xtarget.attributes['name'].nodeValue))
            xdeps = xlib.getElementsByTagName('dep')
            for xdep in xdeps:
                ltargets = []
                xtars = xdep.getElementsByTagName('validdeptar')
                for xtar in xtars:
                    ltargets.append(targets.getTarget(xtar.attributes['name'].nodeValue))
                lib.addDep(libraries.getLib(xdep.attributes['name'].nodeValue).ARCopy(ltargets))
            xpbdeps = xlib.getElementsByTagName('prebuiltdep')
            for xpbdep in xpbdeps:
                ltargets = []
                xtars = xpbdep.getElementsByTagName('validdeptar')
                for xtar in xtars:
                    ltargets.append(targets.getTarget(xtar.attributes['name'].nodeValue))
                lib.addPrebuiltDep(prebuilts.getPrebuilt(xpbdep.attributes['name'].nodeValue).ARCopy(ltargets))
            xflags = xlib.getElementsByTagName('extraConfigureFlag')
            for xflag in xflags:
                lib.addExtraConfFlag(xflag.attributes['value'].nodeValue)
            if needToAdd:
                libraries.addLib(lib)

        xlibraries = xmldata.getElementsByTagName('lib')
        for xlib in xlibraries:
            needToAdd = True
            try:
                lib = libraries.getLib(xlib.attributes['name'].nodeValue, silent=True)
                needToAdd = False
            except:
                lib = ARLibrary(xlib.attributes['name'].nodeValue)
            xtargets = xlib.getElementsByTagName('validtar')
            for xtarget in xtargets:
                lib.addTarget(targets.getTarget(xtarget.attributes['name'].nodeValue))
            xdeps = xlib.getElementsByTagName('dep')
            for xdep in xdeps:
                ltargets = []
                xtars = xdep.getElementsByTagName('validdeptar')
                for xtar in xtars:
                    ltargets.append(targets.getTarget(xtar.attributes['name'].nodeValue))
                lib.addDep(libraries.getLib(xdep.attributes['name'].nodeValue).ARCopy(ltargets))
            xpbdeps = xlib.getElementsByTagName('prebuiltdep')
            for xpbdep in xpbdeps:
                ltargets = []
                xtars = xpbdep.getElementsByTagName('validdeptar')
                for xtar in xtars:
                    ltargets.append(targets.getTarget(xtar.attributes['name'].nodeValue))
                lib.addPrebuiltDep(prebuilts.getPrebuilt(xpbdep.attributes['name'].nodeValue).ARCopy(ltargets))
            xflags = xlib.getElementsByTagName('extraConfigureFlag')
            for xflag in xflags:
                lib.addExtraConfFlag(xflag.attributes['value'].nodeValue)
            xcdeps = xlib.getElementsByTagName('configureDepFile')
            for xcdep in xcdeps:
                lib.addConfDep(xcdep.attributes['name'].nodeValue)
            if needToAdd:
                libraries.addLib(lib)

    return libraries

def parseBinariesXmlFile(paths, targets, libraries):

    binaries = ARBinariesList()

    for root_path in paths:
        path = '%(root_path)s/binaries.xml' % locals()

        xfile=open(path, 'r')
        xdata=xfile.read()
        xfile.close()

        xmldata = parseString(xdata)

        xbinaries = xmldata.getElementsByTagName('binary')
        for xbin in xbinaries:
            needToAdd = True
            try:
                bin = binaries.getBin(xbin.attributes['name'].nodeValue, silent=True)
                needToAdd = False
            except:
                bin = ARBinary(xbin.attributes['name'].nodeValue, xbin.attributes['pathToBuildDir'].nodeValue)
            xtars = xbin.getElementsByTagName('validtar')
            for xtar in xtars:
                bin.addTarget(targets.getTarget(xtar.attributes['name'].nodeValue))
            xdeps = xbin.getElementsByTagName('deplib')
            for xdep in xdeps:
                ltargets = []
                xtars = xdep.getElementsByTagName('validdeptar')
                for xtar in xtars:
                    ltargets.append(targets.getTarget(xtar.attributes['name'].nodeValue))
                bin.addDep(libraries.getLib(xdep.attributes['name'].nodeValue).ARCopy(ltargets))
            xflags = xbin.getElementsByTagName('extraConfigureFlag')
            for xflag in xflags:
                bin.addExtraConfFlag(xflag.attributes['value'].nodeValue)
            if needToAdd:
                binaries.addBin(bin)

    return binaries

def parseAll(paths):
    repos = parseRepoXmlFile(paths)
    targets = parseTargetsXmlFile(paths)
    prebuilts = parsePrebuiltXmlFile(paths, targets)
    libraries = parseLibraryXmlFile(paths, targets, prebuilts)
    binaries = parseBinariesXmlFile(paths, targets, libraries)
    return (repos, targets, prebuilts, libraries, binaries)
