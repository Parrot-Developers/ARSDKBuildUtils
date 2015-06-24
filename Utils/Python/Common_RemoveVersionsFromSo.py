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
import os
import shutil
import re

if sys.version_info < (3,):
    range = xrange

def Common_RemoveVersionsFromSo(rootSo, soext, depLibs):
    # This script needs rpl to be in the path
    if not ARExistsInPath('rpl'):
        ARLog('rpl is needed to strip versioning informations from shared object files')
        return False
        
    outputName = rootSo
    inputName = rootSo
    # Can't work on a lib if it does not exists
    if not os.path.exists(inputName):
        ARLog('%(inputName)s does not exists' % locals())
        return False
    # If the lib is not a symlink to the main library, assume it was already stripped of versioning symbols
    # and remove input if different from output
    if os.path.exists(outputName) and not os.path.islink(outputName):
        if inputName is not outputName:
            ARDeleteIfExists(inputName)
        return True
    
    DirName = os.path.dirname(inputName)
    # Remove symlink and copy acutal lib
    ActualName = os.readlink(inputName)
    ARDeleteIfExists(outputName)
    ARDeleteIfExists(inputName)
    shutil.copy2(os.path.join(DirName, ActualName), outputName)
    
    for BaseName in os.path.basename(inputName) and depLibs:
        # Find other names
        OtherNames = [ f for f in os.listdir(DirName) if BaseName in f and not f.endswith('.' + soext) ]

        # Iterate over other names
        for name in OtherNames:
            # Compute new string to replace
            lenDiff = len(name) - len(BaseName)
            newString = BaseName
            for i in range(lenDiff):
                newString = newString + r'\0'
            # Call rpl
            if not ARExecute('rpl -e %(name)s "%(newString)s" %(outputName)s >/dev/null 2>&1' % locals(), printErrorMessage=False):
                ARLog('Error while running rpl')
                return False
    return True
