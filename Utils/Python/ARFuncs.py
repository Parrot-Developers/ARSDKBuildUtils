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
import subprocess
import os
import inspect
import shutil
import re
import filecmp
import errno

# Print a message
def ARPrint(msg, noNewLine=False):
    sys.stdout.write(msg)
    if not noNewLine:
        sys.stdout.write('\n')

# Exit the script with an optional error code
def EXIT(code):
    if code != 0:
        ARPrint('-- ABORTING --')
    sys.exit(code)

# Class to handle 'cd' and 'cd -'
class Chdir:
    def __init__(self, newPath, create=True, verbose=True):
        self.savedPath = os.getcwd()
        if not os.path.exists(newPath) and create:
            os.makedirs(newPath)
        os.chdir(newPath)
        self.verbose = verbose
        if verbose:
            try:
                ARLog('Entering <%(newPath)s>' % locals())
            except:
                pass
    def exit(self):
        os.chdir(self.savedPath)
        if self.verbose:
            try:
                ARLog('Returning to <'+self.savedPath+'>')
            except:
                pass

# Execute a bash command
def ARExecute(cmdline, isShell=True, failOnError=False, printErrorMessage=True):
    try:
        if printErrorMessage:
            ARLog('Running <%(cmdline)s>' % locals())
        subprocess.check_call(cmdline, shell=isShell)
        return True
    except subprocess.CalledProcessError as e:
        if printErrorMessage:
            ARPrint('Error while running <%(cmdline)s>' % locals())
        if failOnError:
            EXIT(e.returncode)
        else:
            return False

# Execute a bash command, and return the stdout output
def ARExecuteGetStdout(args, isShell=False, failOnError=True, printErrorMessage=True):
    if printErrorMessage:
        ARLog('Running <' + ARListAsBashArg(args) + '>')
    p = subprocess.Popen(args, shell=isShell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    out, err = p.communicate()
    ret = p.wait()
    if ret:
        if printErrorMessage:
            ARLog('Error while running <' + ARListAsBashArg(args) + '>')
        if failOnError:
            EXIT(ret)
        return ''
    return out.strip()

# Checks if a given commands exists in path
def ARExistsInPath(program, isShell=True):
    try:
        subprocess.check_call('which %(program)s 2>/dev/null 1>/dev/null' % locals(), shell=isShell)
        return True
    except subprocess.CalledProcessError as e:
        return False

# Set an environment variable
def ARSetEnv(var, val):
    os.environ[var] = val

# Set an environment variable if not currenly defined
# return True if the variable was added
def ARSetEnvIfEmpty(var, val):
    if os.environ.get(var) is None:
        os.environ[var] = val
        return True
    return False

# Unset an environment variable
def ARUnsetEnv(var):
    if var in os.environ:
        os.environ.pop(var)

# Set an environment variable to 'ideal' if it exists in path, else to 'fallback'
def ARSetEnvIfExists(var, ideal, fallback, args=''):
    if ARExistsInPath(ideal):
        ARSetEnv(var, ideal + ' ' + args)
    else:
        ARSetEnv(var, fallback + ' ' + args)

# Append a message to a file
def ARAppendToFile(filename, message, doPrint=True):
    arfile = open(filename, 'a')
    arfile.write(message + '\n')
    arfile.close()
    if doPrint:
        ARPrint(message)

# Log a message(append to the default logfile + output to console)
def ARLog(message):
    LOGFILE = os.environ.get('ARLOGF')
    if not LOGFILE:
        LOGFILE = ARPathFromHere('build.log')
    ARAppendToFile(LOGFILE, message)

# Init the default log file
def ARInitLogFile():
    LOGFILE = ARPathFromHere('build.log')
    ARSetEnv('ARLOGF', LOGFILE)
    ARDeleteIfExists(LOGFILE)
    
# Get the absolute path from a relative path
def ARPathFromHere(path):
    MYDIR=os.path.abspath(os.path.dirname(sys.argv[0]))
    if '' == MYDIR:
        MYDIR=os.getcwd()
    return '%(MYDIR)s/%(path)s' % locals()
    
# Get the absolute path from a relative path
def ARPathFromPwd(path):
    MYDIR=os.getcwd()
    return '%(MYDIR)s/%(path)s' % locals()

# Transform a python list to a bash args list
def ARListAsBashArg(lst):
    return ' '.join(lst)

# Checks if file A is newer than file B
def ARFileIsNewerThan(fileA, fileB):
    if not os.path.exists(fileA):
        return False
    if not os.path.exists(fileB):
        return True
    return os.stat(fileA).st_mtime > os.stat(fileB).st_mtime

# Called at the beginning of a function to log its start with all its arguments
def StartDumpArgs(**kwargs):
    CallerName = inspect.stack()[1][3]
    if len(kwargs) > 0:
        ARLog('Start running %(CallerName)s with args:' % locals())
    else:
        ARLog('Start running %(CallerName)s' % locals())

    for key, value in kwargs.items():
        ARLog(' -- %(key)s -> %(value)s' % locals())
    
# Called at the end of a function to log its return status and all its arguments
# (use 'return EndDumpArgs(res=True/False, args)')
def EndDumpArgs(res, **kwargs):
    CallerName = inspect.stack()[1][3]
    START_MSG = 'Finished'
    if not res:
        START_MSG = 'Error while'

    if len(kwargs) > 0:
        ARLog('%(START_MSG)s running %(CallerName)s with args:' % locals())
    else:
        ARLog('%(START_MSG)s running %(CallerName)s' % locals())

    for key, value in kwargs.items():
        ARLog(' -- %(key)s -> %(value)s' % locals())

    return res

# Copy and replace a file
def ARCopyAndReplaceFile(SrcFile, DstFile):
    if not os.path.exists(SrcFile):
        raise Exception('%(SrcFile)s does not exist' % locals())
    if not os.path.exists(os.path.dirname(DstFile)):
        os.makedirs(os.path.dirname(DstFile))
    shutil.copy2(SrcFile, DstFile)

def ar_copytree(src, dst, symlinks=False, ignore=None):
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.exists(dst):
        os.makedirs(dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                ar_copytree(srcname, dstname, symlinks, ignore)
            else:
                shutil.copy2(srcname, dstname)
            # XXX What about devices, sockets etc.?
        except (IOError, os.error) as why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except shutil.Error as err:
            errors.extend(err.args[0])
    try:
        shutil.copystat(src, dst)
    except shutil.WindowsError:
        # can't copy file access times on Windows
        pass
    except OSError as why:
        errors.extend((src, dst, str(why)))
    if errors:
        raise shutil.Error(errors)

# Recursive copy and replace of a directory.
# Can optionnaly delete the previous content of the destination directory
# instead of merging
def ARCopyAndReplace(SrcRootDir, DstRootDir, deletePrevious=False, ignoreRegexpsForDeletion=[]):
    if not os.path.exists(SrcRootDir):
        raise Exception('%(SrcRootDir)s does not exist' % locals())
    if deletePrevious:
        if ignoreRegexpsForDeletion:
            ARDeleteRecursivelyNonMatching(DstRootDir, regex=ignoreRegexpsForDeletion)
        else:
            ARDeleteIfExists(DstRootDir)
        ar_copytree(SrcRootDir, DstRootDir, symlinks=True)
        
    else:
        if not os.path.exists(DstRootDir):
            os.makedirs(DstRootDir)
        for SrcDir, directories, files in os.walk(SrcRootDir):
            DstDir = SrcDir.replace(SrcRootDir, DstRootDir)
            if not os.path.exists(DstDir):
                os.mkdir(DstDir)
            for _file in files:
                SrcFile = os.path.join(SrcDir, _file)
                DstFile = os.path.join(DstDir, _file)
                ARDeleteIfExists(DstFile)
                shutil.copy2(SrcFile, DstFile)

# Delete one or multiple files/directories
# Do not throw an error if the file/directory does not exists
def ARDeleteIfExists(*args):
    for fileOrDir in args:
        if os.path.exists(fileOrDir):
            if os.path.isdir(fileOrDir):
                shutil.rmtree(fileOrDir)
            else:
                os.remove(fileOrDir)

# Delete a file if it does not match any given regex
def ARDeleteFileIfNonMatching(path, regex=[]):
    if os.path.exists(path):
        name = os.path.basename(path)
        for exp in regex:
            if re.match(exp, name):
                break
        else:
            ARDeleteIfExists(path)

# Delete a directory contents except for files matching any given regex in a list
# Also deletes empty directories
def ARDeleteRecursivelyNonMatching(path, regex=[]):
    if not os.path.isdir(path):
        ARDeleteFileIfNonMatching(path, regex=regex)
    else:
        for tst in os.listdir(path):
            ARDeleteRecursivelyNonMatching(os.path.join(path, tst), regex=regex)
        try:
            os.rmdir(path)
        except OSError as e:
            if e.errno != errno.ENOTEMPTY:
                raise e

# Gets the number of available CPUs
# If the real number can not be determined, return 1
def ARGetNumberOfCpus():
    try:
        import multiprocessing
        return multiprocessing.cpu_count()
    except (ImportError, NotImplementedError):
        pass
    return 1

def ARReplaceEnvVars(source):
    envMatches = re.findall(r'%\{.*?\}%', source)
    for _match in envMatches:
        Match = _match.replace('%{', '').replace('}%', '')
        try:
            EnvMatch = os.environ[Match]
            source = source.replace(_match, EnvMatch)
        except (KeyError):
            ARLog('Environment variable %(Match)s is not set !' % locals())
            return None
    return source

def ARReplaceFileIfDifferent(oldFile, newFile):
    if not os.path.exists(oldFile) or not filecmp.cmp(oldFile, newFile):
        ARDeleteIfExists(oldFile)
        os.rename(newFile, oldFile)
    else:
        ARDeleteIfExists(newFile)

def ARCapitalize (arstr):
    nameParts = arstr.split('_')
    name = ''
    for part in nameParts:
        if len(part) > 1:
            name =  name + part[0].upper() + part[1:]
        elif len(part) == 1:
            name = name + part[0].upper()
    return name

def ARUncapitalize (arstr):
    if len(arstr) > 1:
        return arstr[0].lower() + arstr[1:]
    elif len(arstr) == 1:
        return arstr[0].lower()
    else:
        return ''

def ARStringIsInteger(arstr):
    try:
        int(arstr)
        return True
    except ValueError:
        return False

#
# Name generation functions
#

def ARMacroName (Module, Submodule, Name):
    # MODULE_SUBMODULE_NAME
    return Module.upper () + '_' + Submodule.upper () + '_' + Name.upper ()

def ARFunctionName (Module, Submodule, Name):
    # MODULE_Submodule_Name
    return Module.upper () + '_' + ARCapitalize (Submodule) + '_' + ARCapitalize (Name)

def ARTypeName (Module, Submodule, Name):
    # MODULE_Submodule[_Name]_t
    if '' != Name:
        return Module.upper () + '_' + ARCapitalize (Submodule) + '_' + ARCapitalize (Name) + '_t'
    else:
        return Module.upper () + '_' + ARCapitalize (Submodule) + '_t'

def ARGlobalName (Module, Submodule, Name):
    # MODULE_Submodule_Name
    return Module.upper () + '_' + ARCapitalize (Submodule) + '_' + ARCapitalize (Name)

def ARGlobalConstName (Module, Submodule, Name):
    # cMODULE_Submodule_Name
    return 'c' + Module.upper () + '_' + ARCapitalize (Submodule) + '_' + ARCapitalize (Name)

def AREnumValue (Module, Submodule, Enum, Name):
    # MODULE_SUBMODULE_ENUM_NAME
    if Enum.upper () == 'ERROR' and (Name.upper () == 'OK' or Name.upper () == 'ERROR'):
        return Module.upper () + '_' + Submodule.upper () + '_' + Name.upper ()
    else:
        return Module.upper () + '_' + Submodule.upper () + '_' + Enum.upper () + '_' + Name.upper ()

def AREnumName (Module, Submodule, Enum):
    # eMODULE_SUBMODULE_ENUM
    return 'e' + Module.upper () + '_' + Submodule.upper () + '_' + Enum.upper ()

def ARFlagValue (Module, Submodule, Enum, Name):
    return Module.upper () + '_FLAG_' + Submodule.upper () + '_' + Enum.upper () + '_' + Name.upper ()
    
def ARJavaEnumType (Module, Submodule, Enum):
    # MODULE_SUBMODULE_ENUM_"ENUM"
    return Module.upper () + '_' + Submodule.upper () + '_' + Enum.upper () + '_ENUM'

def ARJavaMultiSetType (Module, Submodule, multiset):
    # ModuleSubmoduleName
    return Module+ ARCapitalize (Submodule) + ARCapitalize (multiset)

def ARJavaEnumValDef (Module, Submodule, Enum, Name, oldFormat=False):
    # MODULE_SUBMODULE_ENUM_NAME
    if oldFormat:
        return AREnumValue (Module, Submodule, Enum, Name)
    elif Name[0].isdigit():
        return Enum.upper() + '_' + Name.upper ()
    else:
        return Name.upper ()

def ARJavaEnumValue (Module, Submodule, Enum, Name, oldFormat=False):
    # MODULE_SUBMODULE_ENUM_"ENUM".MODULE_SUBMODULE_ENUM_NAME
    return ARJavaEnumType (Module, Submodule, Enum) + '.' + ARJavaEnumValDef (Module, Submodule, Enum, Name, oldFormat)
