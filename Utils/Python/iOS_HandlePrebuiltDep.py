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
import os
import shutil
import re
from Common_HandlePrebuiltDep import *
from ARFuncs import *


def iOS_HandlePrebuiltDep(target, pb, forcedOutputDir=None, outputSuffixes=None, clean=False, debug=False):
    args = dict(locals())
    StartDumpArgs(**args)

    Common_HandlePrebuiltDep(target, pb, forcedOutputDir=forcedOutputDir, outputSuffixes=outputSuffixes)

    res = True

    if not pb.isAvailableForTarget(target):
        ARLog('Prebuilt library %(pb)s does not exists for target %(target)s' % locals())
    else:
        Type = pb.type
        if Type == 'header_only':
            if not clean:
                # Make fat library
                lib = pb
                InstallDir    = ARPathFromHere('Targets/%(target)s/Install/' % locals())
                FrameworksDir = '%(InstallDir)s/Frameworks/' % locals()
                Framework     = '%(FrameworksDir)s/%(lib)s.framework' % locals()
                FrameworkDbg  = '%(FrameworksDir)s/%(lib)s_dbg.framework' % locals()
                OutputDir     = '%(InstallDir)s/lib/' % locals()

                if not os.path.exists(OutputDir):
                    os.makedirs(OutputDir)
                # Create framework
                FinalFramework = Framework
                if debug:
                    FinalFramework = FrameworkDbg
                suffix = '_dbg' if debug else ''
                FrameworkLib     = '%(FinalFramework)s/%(lib)s%(suffix)s' % locals()
                FrameworkHeaders = '%(FinalFramework)s/Headers/' % locals()
                ARDeleteIfExists(FinalFramework)
                os.makedirs(FinalFramework)
                shutil.copytree('%(InstallDir)s/include/%(lib)s' % locals(), FrameworkHeaders)
        elif Type == 'framework':
            lib = pb
            InstallDir    = ARPathFromHere('Targets/%(target)s/Install/' % locals())
            FrameworksDir = '%(InstallDir)s/Frameworks/' % locals()
            Framework     = '%(FrameworksDir)s/%(lib)s.framework' % locals()
            FrameworkDbg  = '%(FrameworksDir)s/%(lib)s_dbg.framework' % locals()
            if not os.path.exists(FrameworksDir):
                os.makedirs(FrameworksDir)
            # Copy framework
            FinalFramework = Framework if not debug else FrameworkDbg
            suffix = '_dbg' if debug else ''
            prefix = 'lib' if not lib.name.startswith('lib') else ''
            ARLog(str(locals()))
            ARCopyAndReplace(pb.path,FinalFramework, deletePrevious=True)
        else:
            ARLog('Do not know how to handle prebuilts of type %(Type)s in iOS' % locals())
            res = False

    return EndDumpArgs(res, **args)
