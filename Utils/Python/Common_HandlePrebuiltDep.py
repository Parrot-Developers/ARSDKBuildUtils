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
from ARFuncs import *


def Common_HandlePrebuiltDep(target, pb, forcedOutputDir=None, outputSuffixes=None):
    args = dict(locals())
    StartDumpArgs(**args)

    res = True

    if not pb.isAvailableForTarget(target):
        ARLog('Prebuilt library %(pb)s does not exists for target %(target)s' % locals())
    else:
        Type = pb.type
        if Type == 'jar':
            if not forcedOutputDir:
                OutputDirs = [ARPathFromHere('Targets/%(target)s/Install/jars/release/' % locals()),
                              ARPathFromHere('Targets/%(target)s/Install/jars/debug/' % locals())]
            else:
                OutputDirs = [forcedOutputDir]
            for OutputDir in OutputDirs:
                if not os.path.exists(OutputDir):
                    os.makedirs(OutputDir)
                Path = pb.path
                Path = ARReplaceEnvVars(Path)
                if Path is None:
                    return EndDumpArgs(res=False, **args)
                OutputFile = os.path.join(OutputDir, os.path.basename(Path))
                if not os.path.exists(OutputFile):
                    shutil.copy2(Path, OutputFile)
        elif Type == 'header_only':
            Name = pb.name
            if not forcedOutputDir:
                rootOutputDir = ARPathFromHere('Targets/%(target)s/Install/' % locals())
                OutputDirs = []
                if outputSuffixes:
                    for d in outputSuffixes:
                        OutputDirs.append('%(rootOutputDir)s/%(d)s/include/%(Name)s/' % locals())
                else:
                    OutputDirs.append('%(rootOutputDir)s/include/%(Name)s/' % locals())
            else:
                OutputDirs = [forcedOutputDir]
            for OutputDir in OutputDirs:
                Path = pb.path
                Path = ARReplaceEnvVars(Path)
                if Path is None:
                    return EndDumpArgs(res=False, **args)
                ARCopyAndReplace(Path, OutputDir, deletePrevious=True)
        elif Type == 'external_project':
            if not forcedOutputDir:
                OutputDirs = [ ARPathFromHere('../' + pb.name) ]
            else:
                OutputDirs = [ forcedOutputDir ]
            for OutputDir in OutputDirs:
                Path = pb.path
                Path = ARReplaceEnvVars(Path)
                if Path is None:
                    return EndDumpArgs(res=False, **args)
                if not os.path.islink(OutputDir):
                    os.symlink(Path,OutputDir)
        else:
            ARLog('Do not know how to handle prebuilts of type %(Type)s' % locals())
            res = False

    return EndDumpArgs(res, **args)
