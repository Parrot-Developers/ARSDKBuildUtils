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

VALID_BSTRAP_SCRIPTS = [ 'bootstrap', 'buildconf' ]

def Common_ValidAutotoolsDirectory(path):
    if os.path.exists('%(path)s/configure' % locals()):
        return True
    for tst in VALID_BSTRAP_SCRIPTS:
        if os.path.exists('%(path)s/%(tst)s' % locals()):
            return True
    return False

def Common_CheckBootstrap(path):
    args = dict(locals())

    StartDumpArgs(**args)

    CONFIGURE    = '%(path)s/configure' % locals()
    MAKEFILE_AM  = '%(path)s/Makefile.am' % locals()
    CONFIGURE_AC = '%(path)s/configure.ac' % locals()
    CONFIGURE_IN = '%(path)s/configure.in' % locals()
    ARSDK_M4     = ARPathFromHere('Utils/m4/ARSDK.m4')

    BSTRAP = ''


    # Search either a configure script, or a valid bootstrap script
    found = False
    for bstrap in VALID_BSTRAP_SCRIPTS:
        if os.path.exists('%(path)s/%(bstrap)s' % locals()):
            found = True
            BSTRAP = './%(bstrap)s' % locals()
            break

    # Check for needed files for bootstrapping
    if (not os.path.exists(MAKEFILE_AM) or not os.path.exists(CONFIGURE_AC)) and not os.path.exists(CONFIGURE):
        ARLog('Given directory must contains Makefile.am and configure.ac')
        return EndDumpArgs(res=False, **args)

    # Check if we need to rerun the bootstrapping script
    # + rerun if needed
    mustRerun = False
    if not os.path.exists(CONFIGURE):
        ARLog('No configure script : must run %(BSTRAP)s' % locals())
        mustRerun = True
    elif ARFileIsNewerThan(MAKEFILE_AM, CONFIGURE):
        ARLog('%(MAKEFILE_AM)s is newer than %(CONFIGURE)s : rerun %(BSTRAP)s' % locals())
        mustRerun = True
    elif ARFileIsNewerThan(CONFIGURE_AC, CONFIGURE):
        ARLog('%(CONFIGURE_AC)s is newer than %(CONFIGURE)s : rerun %(BSTRAP)s' % locals())
        mustRerun = True
    elif ARFileIsNewerThan(CONFIGURE_IN, CONFIGURE):
        ARLog('%(CONFIGURE_IN)s is newer than %(CONFIGURE)s : rerun %(BSTRAP)s' % locals())
        mustRerun = True
    elif ARFileIsNewerThan(ARSDK_M4, CONFIGURE):
        ARLog('%(ARSDK_M4)s is newer than %(CONFIGURE)s : rerun %(BSTRAP)s' % locals())
        mustRerun = True


    res = True
    if mustRerun:
        cdir = Chdir(path)
        if found:
            res = ARExecute(BSTRAP)
        elif os.path.exists(CONFIGURE_AC) or os.path.exists(CONFIGURE_IN) or os.path.exists(MAKEFILE_AM):
            res = ARExecute('autoreconf -fiv')
        else:
            res = True
        cdir.exit()

    return EndDumpArgs(res, **args)
