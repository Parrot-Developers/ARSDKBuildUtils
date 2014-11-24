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

def Common_CheckConfigure(lib, confdir, makedir, ConfigureArgs, extraConfigureFiles):
    args = dict(locals())

    StartDumpArgs(**args)

    # Files used in this part
    CONFIGURE  = '%(confdir)s/configure' % locals()
    FAILFILE   = '%(makedir)s/.configure.failed' % locals()
    CONFIG_LOG = '%(makedir)s/config.log' % locals()
    MAKEFILE   = '%(makedir)s/Makefile' % locals()

    # Sanity check
    if not os.path.exists(CONFIGURE):
        ARLog('No configure script in %(confdir)s' % locals())
        return EndDumpArgs(res=False, **args)

    mustRunConfigure = False

    # Check if a previous configure run failed
    if os.path.exists(FAILFILE):
        ARLog('Previous configure run failed, rerun it')
        mustRunConfigure = True
    # Check if config.log does exist
    elif not os.path.exists(CONFIG_LOG):
        ARLog('Config.log does not exists, run configure')
        mustRunConfigure = True
    # Check if Makefile does exist
    elif not os.path.exists(MAKEFILE):
        ARLog('Makefile does not exists, run configure')
        mustRunConfigure = True

    confCheckFiles = [ CONFIGURE, ARPathFromHere('Utils/Python/ARSDK_PrebuildActions.py') ]

    # For non external lib, add all public headers as deps for configure run
    # This allow proper update of enum tostrings and java enum files
    # -- > Library which generates code should be avoided in this list.
    #      Otherwise, the configure will be run each time the target is changed,
    #      regardless of real changes.
    #      To find these libraries, we check for deps on xml files.
    HeadersDir = lib.path + '/Includes/lib' + lib.name + '/*.h'
    if not lib.ext:
        hasXmlDeps = False
        for ecf in extraConfigureFiles:
            if ecf.endswith('xml'):
                hasXmlDeps = True
                break
        if not hasXmlDeps:
            if extraConfigureFiles is not None:
                extraConfigureFiles.append(HeadersDir)
            else:
                extraConfigureFiles = [HeadersDir]

    for extraFile in extraConfigureFiles:
        if '*' in extraFile:
            extraBasedir = os.path.dirname(extraFile)
            pattern = os.path.basename(extraFile).replace('*', '.*')
            for basedir, directories, files in os.walk(extraBasedir):
                for _file in files:
                    match = re.search(pattern, _file)
                    if match is not None:
                        confCheckFiles.append(os.path.join(basedir, _file))
        else:
            confCheckFiles.append(extraFile)

    if not mustRunConfigure:
        for _file in confCheckFiles:
            if ARFileIsNewerThan(_file, CONFIG_LOG):
                ARLog(os.path.basename(_file) + ' is newer than config.log, rerun configure')
                mustRunConfigure = True
                break


    # Check config.log args against our args
    if not mustRunConfigure:
        # Write current args as a string (same format as in config.log)
        STR_ARGS = ARListAsBashArg(ConfigureArgs).replace('\'','').replace('"','')
        # Retrieve config.log args list
        LOG_ARGS = None
        clogfile = open(CONFIG_LOG, 'r')
        for line in clogfile.readlines():
            match = re.search(r'^[\ \t]*\$.*configure.*', line)
            if match:
                LOG_ARGS = re.sub(r'.*configure\ ', '', line).strip()
                break
        clogfile.close()
        if LOG_ARGS != STR_ARGS:
            ARLog('Rerun configure because ConfigureArgs are differents :')
            ARLog(' OLD args -> %(LOG_ARGS)s' % locals())
            ARLog(' NEW args -> %(STR_ARGS)s' % locals())
            mustRunConfigure = True

    res = True
    if mustRunConfigure:
        # Remove fail info file if it exists
        ARDeleteIfExists(FAILFILE)

        # Go to makedir
        mdir = Chdir(makedir)

        # Run configure
        if not ARExecute(CONFIGURE + ' ' + ARListAsBashArg(ConfigureArgs), failOnError=False):
            # Error
            # Create FAILFILE
            open(FAILFILE, 'a').close()
            res = False

        if res:
            ARExecute(os.environ.get('ARMAKE') + ' clean')

        # Return to previous directory
        mdir.exit()

    return EndDumpArgs(res, **args)
