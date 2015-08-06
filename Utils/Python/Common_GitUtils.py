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

def checkAllReposUpToDate(repos, MYDIR, baseRepoUrl, defaultBaseRepoUrl, nonInteractive=False, extraScripts=[]):
    for repo in repos.list:
        if not repo.ext:
            if not repo.forceBaseUrl:
                repoURL = baseRepoUrl + repo.name + '.git'
            else:
                repoURL = defaultBaseRepoUrl + repo.name + '.git'
        else:
            repoURL = repo.name
            repoURL = ARReplaceEnvVars(repoURL)
            if repoURL is None:
                EXIT(1)
        # Clone non existant repositories
        if not os.path.exists(repo.getDir()):
            ARLog('Cloning %(repo)s git repository' % locals())
            rDir = repo.getDir()
            newDir = Chdir(ARPathFromHere('..'))
            ARExecute('git clone %(repoURL)s' % locals() + ' ' + rDir, failOnError=(not repo.ext))
            newDir.exit()
        # Check for local changes + checkout + pull if needed
        gitscript = '%(MYDIR)s/Utils/updateGitStatus.bash' % locals()
        for patch in reversed(repo.patches):
            patchPath = ARPathFromHere(patch)
            repoDir = Chdir(repo.getDir())
            ARExecute('patch -tsNR -p0 < %(patchPath)s' % locals(), failOnError=False)
            repoDir.exit()
        failOnError = (not repo.ext) or repo.extra
        failArg = ' exitOnFailed' if nonInteractive else ''
        if not repo.ext or repo.extra:
            for scr in extraScripts:
                ARExecute(scr + ' ' + repo.getDir(), failOnError=False)
        ARExecute(gitscript + ' ' + repo.getDir() + ' ' + repoURL + ' ' + repo.rev + failArg, failOnError=failOnError)
        for patch in repo.patches:
            patchPath = ARPathFromHere(patch)
            repoDir = Chdir(repo.getDir())
            ARExecute('patch -tsN -p0 < %(patchPath)s' % locals(), failOnError=False)
            repoDir.exit()
        for cmd in repo.additionnalCommands:
            ARExecute(cmd)
    for webfile in repos.webfilesList:
        if not os.path.exists(webfile.storePath):
            os.makedirs(webfile.storePath)
        Url = webfile.url
        Dst = os.path.join(webfile.storePath, webfile.name)
        if not os.path.exists(Dst):
            downloadOk = False
            if ARExistsInPath('wget'):
                downloadOk = ARExecute('wget %(Url)s -O %(Dst)s' % locals(), failOnError=True)
            elif ARExistsInPath('curl'):
                downloadOk = ARExecute('curl -L %(Url)s -o %(Dst)s' % locals(), failOnError=True)
            if downloadOk:
                root, Ext = os.path.splitext(webfile.name)
                spath = Chdir(webfile.storePath)
                if Ext in ['.gz', '.tgz']:
                    ARExecute('tar xzf ' + webfile.name, failOnError=True)
                elif Ext in ['.bz2', '.tbz2']:
                    ARExecute('tar xjf ' + webfile.name, failOnError=True)
                elif Ext in ['.zip']:
                    ARExecute('unzip ' + webfile.name, failOnError=True)
                for cmd in webfile.additionnalCommands:
                    ARExecute(cmd, failOnError=True)
                spath.exit()
        for patch in webfile.patches:
            patchPath = ARPathFromHere(patch)
            repoDir = Chdir(webfile.storePath)
            ARExecute('patch -tsN -p0 < %(patchPath)s' % locals(), failOnError=False)
            repoDir.exit()

