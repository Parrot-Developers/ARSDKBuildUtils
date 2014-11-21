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
from Java_GenLibraryDoc import *

def Android_GenLibraryDoc(target, lib, clean=False):
    args = dict(locals())
    StartDumpArgs(**args)

    ANDROID_SDK_VERSION = os.environ.get('AR_ANDROID_API_VERSION')

    if not os.environ.get('ANDROID_SDK_PATH'):
        ARLog ('You need to export ANDROID_SDK_PATH to generate android documentation')
        return EndDumpArgs(res=True, **args)

    extraJavadocArgs = ['-linkoffline http://developer.android.com/reference ' + os.environ.get('ANDROID_SDK_PATH') + '/docs/reference']
    extraClasspath   = [os.environ.get('ANDROID_SDK_PATH')+'/platforms/android-' + ANDROID_SDK_VERSION + '/android.jar']

    res = Java_GenLibraryDoc(target, lib, clean, extraSrcDirs=['Android/src'], extraJavadocArgs=extraJavadocArgs, extraClasspath=extraClasspath)

    return EndDumpArgs(res, **args)
