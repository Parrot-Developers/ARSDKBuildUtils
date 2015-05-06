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
from Common_BuildConfigureLibrary import *
from Common_HandlePrebuiltDep import *

def Unix_BuildLibrary(target, lib, clean=False, debug=False, nodeps=False, inhouse=False, requestedArchs=None, isMp=False):
    # Unix libraries are only configure libraries, with no extra args
    args = dict(locals())
    StartDumpArgs(**args)

    # Sanity check : is library valid for this target
    if not lib.isAvailableForTarget(target):
        ARLog('lib%(lib)s does not need to be built for %(target)s' % locals())
        return EndDumpArgs(res=True, **args)

    # First thing : build deps
    if not nodeps:
        for pb in lib.pbdeps:
            if not Common_HandlePrebuiltDep(target, pb):
                ARLog('Error while handling prebuilt library %(pb)s' % locals())
                return EndDumpArgs(res=False, **args)
        for dep in lib.deps:
            ARLog('Building lib%(dep)s (dependancy of lib%(lib)s)' % locals())
            if target.hasAlreadyBuilt(dep):
                ARLog('Dependancy lib%(dep)s already built for %(target)s' % locals())
            elif not dep.isAvailableForTarget(target):
                ARLog('Dependancy lib%(dep)s does not need to be built for %(target)s' % locals())
            elif Unix_BuildLibrary(target, dep, clean, debug):
                ARLog('Dependancy lib%(dep)s built' % locals())
            else:
                ARLog('Error while building dependancy lib%(dep)s' %locals())
                return EndDumpArgs(res=False, **args)
    else:
        ARLog('Skipping deps building for %(lib)s' % locals())

    target.addTriedLibrary(lib)

    # Then : build this library
    ExtraConfFlags = [ 'CFLAGS="-fPIC"']
    res = Common_BuildConfigureLibrary(target, lib, extraArgs=ExtraConfFlags, clean=clean, debug=debug, inhouse=inhouse, isMp=False)

    # If all went well, mark the library as built for current target
    if res:
        target.addBuiltLibrary(lib)

    return EndDumpArgs(res, **args)
