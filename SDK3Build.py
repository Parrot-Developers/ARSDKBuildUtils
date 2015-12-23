#!/usr/bin/env python
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
# PYTHON_ARGCOMPLETE_OK

#Generic imports
import os
import sys
import subprocess
import shutil
try:
    import argcomplete
    hasArgComplete = True
except ImportError:
    hasArgComplete = False

MYDIR=os.path.abspath(os.path.dirname(sys.argv[0]))
if '' == MYDIR:
    MYDIR=os.getcwd()

sys.path.append('%(MYDIR)s/Utils/Python' % locals())

#Custom imports
from xml.dom.minidom import parseString

from ARFuncs import *
from time import localtime, strftime
from Common_GitUtils import *
import commandLine
import xmlreader
import time


#This is a message to announce the new build system
ARPrint ('\n\nThis script is deprecated and doesn\'t work anymore.\n')
ARPrint ('Please download repo (http://source.android.com/source/downloading.html#installing-repo).')
ARPrint ('Then run \'repo init -u https://github.com/Parrot-Developers/arsdk_manifests.git\' in an empty folder.')
ARPrint ('Then run \'repo sync\' to get all sources.')
ARPrint ('After that, you\'ll be able to run \'./build.sh\' to build the SDK.')
ARPrint ('\n\nYou can find a full documentation here: http://developer.parrot.com/docs/bebop/#go-deeper\n\n')
exit(0)
# After that comment, this is the old build. Left here in memory of the old time we spent building the SDK with it. RIP

start = time.time()

DEBUG_MODE = False

#
# Init the log file
#
ARInitLogFile()

#
# Get extra xml dirs
#
xmlDirs = [ MYDIR ]
try:
    extraXmlDirs = os.environ['ARSDK_EXTRA_XML_DIRS'].split(':')
    xmlDirs.extend(extraXmlDirs)
    xmlDirs.remove('')
except:
    pass

#
# Parse XML
#
(repos, targets, prebuilts, libraries, binaries) = xmlreader.parseAll(xmlDirs)

if DEBUG_MODE:
    ARPrint ('Debug mode enabled : dump XML contents')
    repos.dump()
    targets.dump()
    prebuilts.dump()
    libraries.dump()
    binaries.dump()
    EXIT(0)

#
# Parse command line args
#
parser = commandLine.CommandLineParser(targets, libraries, binaries)
if hasArgComplete:
    argcomplete.autocomplete(parser.parser)
parser.parse(sys.argv)

#
# Dump command line args into log file
#
parser.dump()

#
# Export useful tools if available
# (e.g. colormake)
#
ARMakeArgs = '-j ' + str(parser.threads)
ARSetEnvIfExists('ARMAKE', 'colormake', 'make', args=ARMakeArgs)

# Import targets functions for library/binary/doc
# This block will try to import the functions for all targets declared in targets.xml file
# Adding a new target requires the following modifications :
# 1> Add the target in targets.xml filr
# 2> Adapt libraries.xml / binaries.xml to support this target
# 3> Create the Target_BuildLibrary.py script in Utils/Python dir
#    -> This file must contain a Target_BuildLibrary(target, lib, clean=False, debug=False) function
# 4> (Optionnal) Create the Target_BuildBinary.py script in Utils/Python dir
#    -> This file must contain a Target_BuildBinary(target, bin, clean=False, debug=False) function
# 5> (Optionnal) Create the Target_GenLibraryDoc.py script in Utils/Python dir
#    -> This file must contain a Target_GenLibraryDoc(target, lib, clean=False) function
BUILD_LIB_FUNCS = {}
BUILD_BIN_FUNCS = {}
GEN_DOC_FUNCS = {}
for t in targets.list:
    try:
        _name = t.name + '_BuildLibrary'
        _module = __import__ (_name)
        BUILD_LIB_FUNCS[t.name] = getattr (_module, _name)
    except ImportError:
        pass
    try:
        _name = t.name + '_BuildBinary'
        _module = __import__ (_name)
        BUILD_BIN_FUNCS[t.name] = getattr (_module, _name)
    except ImportError:
        pass
    try:
        _name = t.name + '_GenLibraryDoc'
        _module = __import__ (_name)
        GEN_DOC_FUNCS[t.name] = getattr (_module, _name)
    except ImportError:
        pass

#
# Do force clean if needed
#
if parser.isForceClean:
    ARLog("Force clean !")
    TARGETDIR = '%(MYDIR)s/Targets' % locals()
    ARDeleteIfExists (TARGETDIR)
    # Do all-cleanup if needed
    if parser.isForceCleanup:
        allRepoDirs=[]
        for repo in repos.list:
            if not repo.ext:
                allRepoDirs.append(repo.getDir())
        cleanScript = '%(MYDIR)s/Utils/cleanupSDKRepo.bash' % locals()
        ARExecute(cleanScript + ' ' + ARListAsBashArg(allRepoDirs))
    exit(0)

#
# Do all repo work:
#  - Clone non existant repositories
#  - Checkout the requested branch/tag/commit
#  - If on a branch, pull it
#
if not parser.noGit:
    checkAllReposUpToDate(repos, MYDIR, parser.repoBaseUrl, parser.defaultBaseRepoUrl, extraScripts=parser.extraGitScripts)
else:
    ARLog('Skipping git checks')

if parser.doNothing:
    ARLog('Nothing to be done')
    exit(0)

# Android case --> Force minimum api level and target api level
ARSetEnv('AR_ANDROID_MIN_VERSION', '14')
ARSetEnv('AR_ANDROID_API_VERSION', '19')

#
# Actual build loop
#
allOk = True
for target in parser.activeTargets:
    libraries.clearCache()
    binaries.clearCache()
    if parser.activeLibs:
        if target.name in BUILD_LIB_FUNCS:
            for lib in parser.activeLibs:
                if not BUILD_LIB_FUNCS[target.name](target, lib, clean=parser.isClean, debug=parser.isDebug, nodeps=parser.noDeps, inhouse=parser.isInHouse, requestedArchs=parser.archs, isMp=parser.multiProcess):
                    allOk = False
        else:
            ARLog('Unable to build libraries for target %(target)s' % locals())
        if parser.genDoc and not parser.isClean:
            if target.name in GEN_DOC_FUNCS:
                for lib in parser.activeLibs:
                    GEN_DOC_FUNCS[target.name](target, lib)
                TargetDocIndexScript = ARPathFromHere('Utils/generateDocIndex.bash')
                TargetDocIndexPath   = ARPathFromHere('Targets/%(target)s/Build/Doc' % locals())
                ARExecute('%(TargetDocIndexScript)s %(TargetDocIndexPath)s %(target)s' % locals())
            else:
                ARLog('Unable to generate documentation for target %(target)s' % locals())

    if parser.activeBins:
        if target.name in BUILD_BIN_FUNCS:
            for bin in parser.activeBins:
                if not BUILD_BIN_FUNCS[target.name](target, bin, clean=parser.isClean, debug=parser.isDebug, nodeps=parser.noDeps, inhouse=parser.isInHouse, requestedArchs=parser.archs):
                    target.failed = True
                    allOk = False
        else:
            ARLog('Unable to build binaries for target %(target)s' % locals())

    for scrinfo in target.postbuildScripts:
        scr = scrinfo['path']
        if allOk:
            if not ARExecute(scr + ' >/dev/null 2>&1', failOnError=False):
                ARPrint('Error while running ' + scr + '. Run manually to see the output')
                target.failed = True
                scrinfo['done'] = False
                allOk=False
            else:
                scrinfo['done'] = True
    if not allOk:
        break

if parser.installDoc and allOk:
    DocCopyScript = ARPathFromHere('Utils/copyDoc.bash')
    for target in parser.activeTargets:
        ARExecute ('%(DocCopyScript)s %(target)s' % locals())

hasColors = ARExecute('tput colors >/dev/null 2>&1', failOnError=False, printErrorMessage=False)
if ARExistsInPath('stty'):
    termSizeStr = ARExecuteGetStdout(['stty', 'size'], failOnError=False, printErrorMessage=False)
    termSizeArr = termSizeStr.split(' ')
    try:
        termCols = int(termSizeArr[1]) - 1
    except:
        termCols = 80
else:
    termCols = 80


class logcolors:
    FAIL = '\033[31m' if hasColors else 'FA:'
    PASS = '\033[32m' if hasColors else 'OK:'
    REQ  = '\033[33m' if hasColors else 'ND:'
    NONE = '\033[34m' if hasColors else 'NR:'
    UNAI = '\033[30m' if hasColors else 'NA:'
    DEF  = '\033[39m' if hasColors else ''

def SDKPrintStatus(msg, available, requested, tried, built, padToLen=20, newline=False, currentCol=0, baseCol=0):
    colorLen = 3 if not hasColors else 0
    padLen = padToLen - len(msg)
    while padLen <= 0:
        padLen += padToLen
    printLen = len(msg) + padLen + colorLen

    futureCol = currentCol + printLen

    if futureCol > termCols:
        newline = True

    if newline:
        ARPrint('')
        ARPrint(' '*baseCol, True)
        futureCol = printLen + baseCol

    if not available:
        ARPrint(logcolors.UNAI, True)
    elif not requested and not tried:
        ARPrint(logcolors.NONE, True)
    elif not tried:
        ARPrint(logcolors.REQ, True)
    elif not built:
        ARPrint(logcolors.FAIL, True)
    else:
        ARPrint(logcolors.PASS, True)
    ARPrint(msg, True)
    if padLen > 0:
        ARPrint(' '*padLen, True)
    ARPrint(logcolors.DEF, True)

    return futureCol


ARPrint('')
ARPrint('Status :')
ARPrint(' --> Legend : ' + logcolors.FAIL + 'FAIL ' + logcolors.PASS + 'PASS ' + logcolors.REQ + 'NOT_BUILT ' + logcolors.NONE + 'NOT_REQUESTED ' + logcolors.UNAI + 'NOT_AVAILABLE ' + logcolors.DEF)
ARPrint(' --> Binaries are postfixed with `*`')
ARPrint(' --> Postbuild scripts  are postfixed with `+`')
ARPrint('')
offset = 13 if hasColors else 16
for t in targets.list:
    targetRequested = t in parser.activeTargets
    targetTried = bool(t.triedToBuildLibraries)
    targetBuilt = len(t.alreadyBuiltLibraries) == len(t.triedToBuildLibraries) and not t.failed
    SDKPrintStatus(t.name, True, targetRequested, targetTried, targetBuilt, padToLen=10)
    ARPrint(' : ', True)
    count=offset
    first=False
    for l in libraries.list:
        libAvailable = l.isAvailableForTarget(t)
        libRequested = l in parser.activeLibs and targetRequested
        libTried = t.hasTriedToBuild(l)
        libBuilt = t.hasAlreadyBuilt(l)
        count = SDKPrintStatus(l.name, libAvailable, libRequested, libTried, libBuilt, padToLen=20, newline=first, currentCol=count, baseCol=offset)
        first=False
    first=True
    for b in binaries.list:
        binAvailable = b.isAvailableForTarget(t)
        binRequested = b in parser.activeBins and targetRequested
        binTried = t.hasTriedToBuildBinary(b)
        binBuilt = t.hasAlreadyBuiltBinary(b)
        count = SDKPrintStatus(b.name + '*', binAvailable, binRequested, binTried, binBuilt, padToLen=20, newline=first, currentCol=count, baseCol=offset)
        first=False
    first=True
    for scrinfo in t.postbuildScripts:
        scrAvailable = True
        scrRequescted = targetRequested
        scrTried = scrinfo['done'] is not None
        scrBuilt = bool(scrinfo['done'])
        count = SDKPrintStatus(scrinfo['name'] + '+', scrAvailable, scrRequescted, scrTried, scrBuilt, padToLen=20, newline=first, currentCol=count, baseCol=offset)
        first=False
        
        
    ARPrint('')
    ARPrint('')

ARLog('End of build')
if not allOk:
    ARLog('-- Errors were found during build ! --')

end = time.time()

seconds = int(end - start)
hours, tmp = divmod(seconds, 3600)
minutes, seconds = divmod(tmp, 60)

strh=''
strm=''
strs = str(seconds) + 's'
if hours > 0:
    strh = str(hours) + 'h '
    strm = str(minutes) + 'm '
if minutes > 0:
    strm = str(minutes) + 'm '
ARLog('Build took %(strh)s%(strm)s%(strs)s' % locals())
        
sys.exit (0 if allOk else 1)
