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
from Common_HandlePrebuiltDep import *
import os
import shutil

def Java_GenLibraryDoc(target, lib, clean=False, extraSrcDirs=[], extraJavadocArgs=[], extraClasspath=[]):
    args = dict(locals())
    StartDumpArgs(**args)

    OutputDir = ARPathFromHere('Targets/%(target)s/Build/Doc' % locals())
    JavadocRootDir = ARPathFromHere('Targets/%(target)s/Build/.srcdir' % locals())
    JavadocSrcDir = '%(JavadocRootDir)s/sources' % locals()
    JavadocPrebuiltDir = '%(JavadocRootDir)s/prebuilts' % locals()

    # Clean : remove ALL docs (not just the one of the library)
    if clean:
        ARDeleteIfExists (OutputDir, JavadocSrcDir)
        return EndDumpArgs(res=True, **args)

    # Create a directory to hold all java sources to generate doc
    if not os.path.exists(JavadocSrcDir):
        os.makedirs(JavadocSrcDir)
    if not os.path.exists(JavadocPrebuiltDir):
        os.makedirs(JavadocPrebuiltDir)
        
    # Copy sources to the folder
    srcDirs = ['JNI/java']
    srcDirs.extend(extraSrcDirs)

    for _dir in srcDirs:
        SrcDir = lib.path + '/%(_dir)s' % locals()
        DstDir = '%(JavadocSrcDir)s/' % locals()
        if os.path.exists(SrcDir):
            ARCopyAndReplace(SrcDir, DstDir)

    # Copy prebuilts
    classpath = []
    for prebuilt in lib.pbdeps:
        if not Common_HandlePrebuiltDep(target, prebuilt, forcedOutputDir=JavadocPrebuiltDir):
            ARLog('Error while handling prebuilt library %(prebuilt)s' % locals())
            return EndDumpArgs(res=False, **args)

    # Run javadoc
    # -- Find list of .java / .jar (prebuilts) files
    JavaFiles = []
    for baseDir, directories, files in os.walk(JavadocSrcDir):
        for f in files:
            if f.endswith('.java'):
                JavaFiles.append(os.path.join(os.path.join(JavadocSrcDir, baseDir), f))
    for baseDir, directories, files in os.walk(JavadocPrebuiltDir):
        for f in files:
            if f.endswith('.jar'):
                classpath.append(os.path.join(os.path.join(JavadocPrebuiltDir, baseDir), f))
    classpath.extend(extraClasspath)

    # -- Do nothing if no input files are found
    if not JavaFiles:
        return EndDumpArgs(res=True, **args)

    # -- Convert list as strings
    ExtraArgsString = ARListAsBashArg(extraJavadocArgs)
    JavaFilesString = ARListAsBashArg(JavaFiles)
    classPathString = ''
    if classpath:
        classPathString = '-classpath "'
        for c in classpath:
            classPathString = classPathString + c + ':'
        classPathString = classPathString[:-1] + '"'
    
    # -- Actual run
    res = ARExecute('javadoc -d %(OutputDir)s %(JavaFilesString)s %(ExtraArgsString)s %(classPathString)s' % locals())

    return EndDumpArgs(res, **args)
