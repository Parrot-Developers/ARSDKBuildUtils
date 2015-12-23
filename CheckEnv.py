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

import sys
import os

MYDIR=os.path.abspath(os.path.dirname(sys.argv[0]))
if '' == MYDIR:
    MYDIR=os.getcwd()
sys.path.append('%(MYDIR)s/Utils/Python' % locals())

from ARFuncs import *
import xmlreader
import tempfile

#This is a message to announce the new build system
ARPrint ('\n\nThis script is deprecated and doesn\'t work anymore.\n')
ARPrint ('Please download repo (http://source.android.com/source/downloading.html#installing-repo).')
ARPrint ('Then run \'repo init -u https://github.com/Parrot-Developers/arsdk_manifests.git\' in an empty folder.')
ARPrint ('Then run \'repo sync\' to get all sources.')
ARPrint ('After that, you\'ll be able to run \'./build.sh\' to build the SDK.')
ARPrint ('\n\nYou can find a full documentation here: http://developer.parrot.com/docs/bebop/#go-deeper\n\n')
exit(0)
# After that comment, this is the old build. Left here in memory of the old time we spent building the SDK with it. RIP


uname = ARExecuteGetStdout(["uname"], printErrorMessage=False).lower()


targets = [
    {
        'name' : 'Generic',
        'platforms' : ['darwin', 'linux'],
        'mandatoryPlatform' : False,
        'bins' : ['git', 'wget', 'jar', 'automake', 'autoconf', 'libtool'],
        'libs' : [],
        'envs' : [],
        'cmds' : [],
        'CC' : None,
        },
    {
        'name' : 'iOS',
        'platforms' : ['darwin'],
        'mandatoryPlatform' : True,
        'bins' : ['xcrun', 'xcodebuild'],
        'libs' : [],
        'envs' : [],
        'cmds' : [],
        'CC' : None,
        },
    {
        'name' : 'Unix',
        'platforms' : ['darwin', 'linux'],
        'mandatoryPlatform' : False,
        'bins' : ['gcc', 'yasm', 'nasm'],
        'libs' : ['-lz', '-pthread'],
        'envs' : [],
        'cmds' : [],
        'CC' : 'gcc',
        },
    {
        'name' : 'Android',
        'platforms' : ['darwin', 'linux'],
        'mandatoryPlatform' : False,
        'bins' : ['rpl', 'javac', 'arm-linux-androideabi-gcc', 'mipsel-linux-android-gcc', 'i686-linux-android-gcc'],
        'libs' : ['-llog'],
        'envs' : ['ANDROID_NDK_PATH', 'ANDROID_SDK_PATH'],
        'cmds' : [
            {'cmd': '$ANDROID_SDK_PATH/tools/android list targets | grep "API level:" | grep 19',
             'desc': 'Check if Android SDK 19 is installed',
             'fix': 'Missing Android SDK for API 19 (Android 4.4.2), please install it.'
             },
            ],
        'CC' : 'arm-linux-androideabi-gcc',
        },
]

doPrint = True
verbose = False
statusTarget = None
if len(sys.argv) > 1:
    if sys.argv[1] == '-v':
        verbose = True
    else:
        statusTarget = sys.argv[1]
        doPrint = False
        if not statusTarget in ['Generic', 'iOS', 'Android', 'Unix']:
            ARPrint('Unknown options, this script only support `-v`, `Generic`, `iOS`, `Android` and `Unix`')
            sys.exit(1)


hasColors = ARExecute('tput colors >/dev/null 2>&1', failOnError=False, printErrorMessage=False)

class logcolors:
    FAIL = '\033[31m' if hasColors else 'FA:'
    PASS = '\033[32m' if hasColors else 'OK:'
    NONE = '\033[33m' if hasColors else 'NT:'
    DEF  = '\033[39m' if hasColors else ''

def ARCEPrint(msg, noNewLine=False):
    if verbose:
        ARPrint(msg, noNewLine=noNewLine)

def ARVBPrint(msg, noNewLine=False):
    if doPrint:
        ARPrint(msg, noNewLine=noNewLine)

def ARPrintStatus(msg, status=False, unknown=False, padTo=20):
    if unknown:
        ARVBPrint(logcolors.NONE, noNewLine=True)
    elif status:
        ARVBPrint(logcolors.PASS, noNewLine=True)
    else:
        ARVBPrint(logcolors.FAIL, noNewLine=True)
    ARVBPrint(msg, noNewLine=True)
    if len(msg) < padTo:
        ARVBPrint(' '*(padTo-len(msg)), noNewLine=True)
    ARVBPrint(logcolors.DEF, noNewLine=True)

def ARAppendToMessage(orig, msg, leftPad=22):
    if len(orig) == 0:
        return msg
    return orig + '\n' + ' '*leftPad + msg

ARVBPrint('-- Checking if your environment will build the ARSDK for different platforms --')
ARVBPrint('')
ARVBPrint('[[ ' + logcolors.PASS + 'Should work' + logcolors.DEF + ', ' + logcolors.FAIL + 'Won\'t work' + logcolors.DEF + ', ' + logcolors.NONE + 'Not tested, may work' + logcolors.DEF + ' ]]')
ARVBPrint('')

if sys.version_info < (2, 7):
    ARVBPrint(logcolors.FAIL + ' Bad python version.' + logcolors.DEF + ' The SDK requires python 2.7 or higher (python 3 versions are supported)')
    ARVBPrint('')
    sys.exit(1)


if ' ' in MYDIR:
    ARVBPrint(logcolors.FAIL + ' Bad folder name.' + logcolors.DEF + ' The SDK needs an absolute path without spaces. There is at least one space in the current path :')
    ARVBPrint(                 '                   "' + MYDIR + '"')
    ARVBPrint('')
    sys.exit(1)

DirLastPath=os.path.basename(MYDIR)
if DirLastPath != 'ARSDKBuildUtils':
    ARVBPrint(logcolors.FAIL + ' Bad folder name.' + logcolors.DEF + ' The SDK needs to be in a folder named "ARSDKBuildUtils", but the current folder is named "'+DirLastPath+'".')
    ARVBPrint('')
    sys.exit(1)



for t in targets:
    status = True
    unknown = False
    msg = ''
    ARCEPrint ('Checking target %s ...' % t['name'])
    ARCEPrint ('--------------------------')
    ARCEPrint ('Checking platform ...', noNewLine=True)
    if uname in t['platforms'] or not t['mandatoryPlatform']:
        if not uname in t['platforms']:
            ARCEPrint(' Unknown (%s)' % uname)
            msg = ARAppendToMessage(msg, 'Unknown platform `%s`, the target `%s` has only been tested on %s ' % (uname, t['name'], t['platforms']))
            unknown = True
        else:
            ARCEPrint(' OK (%s)' % uname)
        for b in t['bins']:
            ARCEPrint('Checking if binary `%s` is available in PATH ...' % b, noNewLine=True)
            if not ARExistsInPath(b):
                ARCEPrint(' NO')
                msg = ARAppendToMessage(msg, 'Missing binary `%s`' % b)
                status = False
            else:
                ARCEPrint(' YES')
        for l in t['libs']:
            ARCEPrint('Checking if library `%s` is available for linking ...' % l, noNewLine=True)
            (sfHandle, sfPath) = tempfile.mkstemp(suffix='.c')
            (binHandle, binPath) = tempfile.mkstemp(suffix='.out')
            os.close(binHandle)
            os.remove(binPath)
            sfFile = os.fdopen(sfHandle, 'w')
            sfFile.write('int main(int argc, char *argv[]) { return 0; }\n')
            sfFile.close()
            compiler = t['CC']
            if not compiler or not ARExistsInPath(compiler):
                ARCEPrint(' NO COMPILER FOUND')
                status = False
            else:
                if not ARExecute('%(compiler)s -o %(binPath)s %(sfPath)s %(l)s >/dev/null 2>&1' % locals(), printErrorMessage=False, failOnError=False):
                    ARCEPrint(' NO')
                    status = False
                    msg = ARAppendToMessage(msg, 'Missing library `%s`' % l)
                else:
                    ARCEPrint(' YES')
            if os.path.exists(binPath):
                os.remove(binPath)
            os.remove(sfPath)
            
        for e in t['envs']:
            ARCEPrint('Checking if the environment variable `%s` is set ...' % e, noNewLine=True)
            if not e in os.environ:
                ARCEPrint(' NO')
                msg = ARAppendToMessage(msg, 'Missing environment variable `%s`' % e)
                status = False
            else:
                ARCEPrint(' YES')
        for f in t['cmds']:
            ARCEPrint('Checking if the command `%s` (%s) works ...' % (f['cmd'], f['desc']), noNewLine=True)
            if not ARExecute(f['cmd'] + ' >/dev/null 2>&1', printErrorMessage=False, failOnError=False):
                ARCEPrint(' NO')
                status = False
                msg = ARAppendToMessage(msg, f['fix'])
            else:
                ARCEPrint(' YES')
            
    else:
        status = False
        ARCEPrint(' Bad (%s)' % uname)
        msg = ARAppendToMessage(msg, 'Bad platform `%s`, you need to be on %s to build the target `%s`' % (uname, t['platforms'], t['name']))
    ARCEPrint('')
    ARPrintStatus (t['name'], status, unknown)
    t['status']  = status
    t['unknown'] = unknown
    ARVBPrint(': ', noNewLine=True)
    if not msg:
        msg = 'OK !'
    ARVBPrint(msg)
    ARCEPrint('')
    if t['name'] == 'Generic':
        globalStatus = status
        if not globalStatus:
            ARVBPrint('ERROR !')
            break

ARVBPrint('')

if not globalStatus:
    ARVBPrint(logcolors.FAIL + 'Basic configuration is not met' + logcolors.DEF + ', the SDK3Build.py script will probably fail even before trying to build a target. Fix errors for virtual target "Generic" before launching the script')
    ARVBPrint('')
    


if statusTarget:
    for t in targets:
        if t['name'] == statusTarget:
            status = 0 if not t['unknown'] and t['status'] else 1
            sys.exit(status)
    sys.exit(1)

sys.exit(0)

