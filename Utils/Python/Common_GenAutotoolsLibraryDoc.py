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
import re
import tempfile
import os

def Common_WriteValuesToDoxyCfgFile(DFile, **kwargs):
    for key, value in kwargs.items():
        os.write(DFile, '%(key)s = %(value)s\n' % locals())

def Common_GenAutotoolsLibraryDoc(target, lib, clean=False, subdirsToInclude=[], onlyC=True):
    args = dict(locals())
    StartDumpArgs(**args)

    res = False

    # Do not generate doc for external lib
    if lib.ext:
        ARLog('Documentation will not be generated for external libraries')
        return EndDumpArgs(res=True, **args)
    OutputDir = ARPathFromHere('Targets/%(target)s/Build/Doc/lib%(lib)s' % locals())

    # Clean handle
    if clean:
        ARDeleteIfExists(OutputDir)
        return EndDumpArgs(res=True, **args)

    # Create output directory
    if not os.path.exists(OutputDir):
        os.makedirs(OutputDir)

    # If the directory (release) is configured, just call "make doxygen-doc"
    BuildDir = ARPathFromHere('Targets/%(target)s/Build/lib%(lib)s' % locals())
    Makefile = '%(BuildDir)s/Makefile' % locals()
    if os.path.exists(Makefile):
        bdir = Chdir(BuildDir)
        res = ARExecute(os.environ.get('ARMAKE') + ' doxygen-doc')
        bdir.exit()
    # If make doxygen-doc failed, or if the Makefile does not exists, run doxygen manually
    if not res:
        DummyDirForRelativePath = ARPathFromHere('Targets/%(target)s/Build/Dummy' % locals())
        if not os.path.exists(DummyDirForRelativePath):
            os.makedirs(DummyDirForRelativePath)
        ConfigureAc = lib.path + '/Build/configure.ac'
        DoxyCfg = lib.path + '/Build/doxygen.cfg'
        if not os.path.exists(ConfigureAc):
            ARLog('Unable to generate lib%(lib)s documentation')
            ARLog('lib%(lib)s does not contains a configure.ac file, and was not previously built')
            return EndDumpArgs(res=False, **args)
        # Create Doxygen Extra Args
        SRCDIR = lib.path + '/Build'
        PROJECT = 'lib%(lib)s' % locals()
        # -- Search version in configure.ac file
        confacfile = open(ConfigureAc)
        VERSION = ''
        for line in confacfile.readlines():
            match = re.search(r'AC_INIT', line)
            if match:
                Version = re.sub(r'[A-Z_]*\(\[[^]]*\], \[([^]]*)\].*', r'\1', line).strip()
                break
        confacfile.close()
        if not Version:
            ARLog('Unable to read version from configure.ac file')
            return EndDumpArgs(res=False, **args)
        PERL_PATH = os.popen('which perl').read().strip()
        HAVE_DOT = 'NO'
        if ARExistsInPath('dot'):
            HAVE_DOT = 'YES'

        # Create temporary configuration file
        DoxyCfgFinalFile, DoxyCfgFinalName = tempfile.mkstemp()
        # -- Copy original file in the temporary one
        DoxyCfgFile = open(DoxyCfg)
        for line in DoxyCfgFile.readlines():
            os.write(DoxyCfgFinalFile, line)
        DoxyCfgFile.close()

        # -- Export needed values
        ARSetEnv ('PROJECT', PROJECT)
        ARSetEnv ('VERSION', VERSION)
        ARSetEnv ('SRCDIR', SRCDIR)
        # -- Append needed values
        Common_WriteValuesToDoxyCfgFile(DoxyCfgFinalFile,
                                        PERL_PATH=PERL_PATH,
                                        HAVE_DOT=HAVE_DOT,
                                        GENERATE_MAN='NO',
                                        GENERATE_RTF='NO',
                                        GENERATE_XML='NO',
                                        GENERATE_HTMLHELP='NO',
                                        GENERATE_CHI='NO',
                                        GENERATE_HTML='YES',
                                        GENERATE_LATEX='NO',)

        # -- Append subdirs
        for extraDir in subdirsToInclude:
            if os.path.exists(lib.path + '/../' + extraDir):
                os.write(DoxyCfgFinalFile, 'INPUT += $(SRCDIR)/../%(extraDir)s\n' % locals())

        # -- Append Non-C mode
        if not onlyC:
            Common_WriteValuesToDoxyCfgFile(DoxyCfgFinalFile, OPTIMIZE_OUTPUT_FOR_C='NO')

        # -- Close temporary file
        os.close(DoxyCfgFinalFile)

        # Call doxygen
        bdir = Chdir (DummyDirForRelativePath)
        res = ARExecute ('doxygen %(DoxyCfgFinalName)s' % locals())
        bdir.exit()

        ARDeleteIfExists(DummyDirForRelativePath)

        os.remove (DoxyCfgFinalName)

    return EndDumpArgs(res, **args)
