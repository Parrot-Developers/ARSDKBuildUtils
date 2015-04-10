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
from ARFuncs import *
import shutil

def Darwin_RunXcodeBuild(target, lib, xcprojPath, archs, debug=False, clean=False):
    args = dict(locals())
    StartDumpArgs(**args)

    res = True

    if not os.path.exists(xcprojPath):
        ARLog('%(xcprojPath)s does not exists' % locals())
        return EndDumpArgs(res=False, **args)

    FrameworksDir = ARPathFromHere('Targets/%(target)s/Install/Frameworks' % locals())

    libLower = lib.name.lower()
    libPrefix = 'lib' if ((not libLower.startswith('lib')) and (not lib.ext)) else ''

    Framework     = '%(FrameworksDir)s/%(libPrefix)s%(lib)s.framework' % locals()
    FrameworkDbg  = '%(FrameworksDir)s/%(libPrefix)s%(lib)s_dbg.framework' % locals()

    BuiltLibs = []
    xcprojDir = os.path.realpath('%(xcprojPath)s/..' % locals())

    if debug:
        ARDeleteIfExists(FrameworkDbg)
    else:
        ARDeleteIfExists(Framework)

    for dictionnary in archs:
        arch = dictionnary['arch']
        platform = dictionnary['platform']
        minos = dictionnary['minos']
        #for arch, platform in archs.items():
        SDK = platform.lower()
        if clean:
            if not ARExecute('xcodebuild -project %(xcprojPath)s -configuration Release -sdk %(SDK)s -arch %(arch)s clean' % locals()):
                ARLog('Unable to clean Release project')
                return EndDumpArgs(res=False, **args)
            if not ARExecute('xcodebuild -project %(xcprojPath)s -configuration Debug -sdk %(SDK)s -arch %(arch)s clean' % locals()):
                ARLog('Unable to clean Debug project')
                return EndDumpArgs(res=False, **args)
        else:
            CONFIGURATION = 'Release'
            if debug:
                CONFIGURATION = 'Debug'
            if not ARExecute('xcodebuild -project %(xcprojPath)s -configuration %(CONFIGURATION)s -sdk %(SDK)s -arch %(arch)s' % locals()):
                ARLog('Unable to build %(CONFIGURATION)s project' % locals())
                return EndDumpArgs(res=False, **args)

            BuildFramework = '%(xcprojDir)s/Products/%(arch)s/%(libPrefix)s%(lib)s.framework' % locals()
            BuildFrameworkDbg = '%(xcprojDir)s/Products/%(arch)s/%(libPrefix)s%(lib)s_dbg.framework' % locals()

            if debug:
                if not os.path.exists(FrameworkDbg):
                    shutil.copytree(BuildFrameworkDbg, FrameworkDbg)
                BuiltLibs.extend([ os.path.join(BuildFrameworkDbg, l) for l in os.listdir(BuildFrameworkDbg) if 'lib' in l])
            else:
                if not os.path.exists(Framework):
                    shutil.copytree(BuildFramework, Framework)
                BuiltLibs.extend([ os.path.join(BuildFramework, l) for l in os.listdir(BuildFramework) if 'lib' in l])

    # Create(or delete) universal framework
    if clean:
        ARDeleteIfExists(Framework)
        ARDeleteIfExists(FrameworkDbg)
    else:
        FrameworkLib = '%(Framework)s/%(libPrefix)s%(lib)s' % locals()
        if debug:
            FrameworkLib = '%(FrameworkDbg)s/%(libPrefix)s%(lib)s_dbg' % locals()

        if not ARExecute('lipo ' + ARListAsBashArg(BuiltLibs) + ' -create -output ' + FrameworkLib):
            ARLog('Error while creating universal library')
            return EndDumpArgs(res=False, **args)

    return EndDumpArgs(res=True, **args)
