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
    p = subprocess.Popen(args, shell=isShell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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

# Recursive copy and replace of a directory.
# Can optionnaly delete the previous content of the destination directory
# instead of merging
def ARCopyAndReplace(SrcRootDir, DstRootDir, deletePrevious=False):
    if not os.path.exists(SrcRootDir):
        raise Exception('%(SrcRootDir)s does not exist' % locals())
    if deletePrevious:
        ARDeleteIfExists(DstRootDir)
        shutil.copytree(SrcRootDir, DstRootDir, symlinks=True)
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
