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
import os
import argparse
from ARFuncs import *

defaultBaseRepoUrl = 'https://github.com/Parrot-Developers/'

class CommandLineParser:
    "Command line options parser for ARSDK 3 build script"
    def __init__(self, targets, libraries, binaries):
        self.availableTargets = targets
        self.availableLibraries = libraries
        self.availableBinaries = binaries
        self.activeTargets = []
        self.activeLibs = []
        self.activeBins = []
        self.isClean = False
        self.isDebug = False
        self.isInHouse = False
        self.isForceClean = False
        self.isForceCleanup = False
        self.genDoc = False
        self.installDoc = False
        self.doNothing = False
        self.noGit = False
        self.noDeps = False
        self.multiProcess = False
        self.threads = -1
        self.defaultBaseRepoUrl = defaultBaseRepoUrl
        self.repoBaseUrl = defaultBaseRepoUrl
        self.extraGitScripts = []
        self.archs = []
        self.parser = argparse.ArgumentParser()
        self.init_parser()

    def init_parser(self):
        targetsNames = [ t.name for t in self.availableTargets.list ]
        librariesNames = [ l.name for l in self.availableLibraries.list ]
        binariesNames = [ b.name for b in self.availableBinaries.list ]
        self.parser.add_argument('-t', '--target', action="append", choices=targetsNames, help="Target name (cumulative)")
        self.parser.add_argument('-l', '--library', action="append", choices=librariesNames, help="Library name (cumulative)")
        self.parser.add_argument('-b', '--binary', action="append", choices=binariesNames, help="Binary name (cumulative)")
        self.parser.add_argument('-c', '--clean', action="store_true", help="Clean all selected lib/bin")
        self.parser.add_argument('-d', '--debug', action="store_true", help="Build selected lib/bin in debug mode")
        self.parser.add_argument('--inhouse', action="store_true", help="Build the SDK for inhouse distribution")
        self.parser.add_argument('--force-clean', action="store_true", help="Wipe all targets (overrides any other setting)")
        self.parser.add_argument('--all-cleanup', action="store_true", help="Implies `--force-clean` and run all cleanup scripts in internal repositories")
        self.parser.add_argument('--doc', action="store_true", help="Generate documentation after building")
        self.parser.add_argument('--install-doc', action="store_true", help="Implies `--doc` and copy the generated documentation to Docs repository")
        self.parser.add_argument('--none', action="store_true", help="Do only GIT Checks, do not build / clean anything")
        self.parser.add_argument('--nogit', action="store_true", help="Do not run GIT checks")
        self.parser.add_argument('-j', type=int, help="The number of threads to use. Automatically set to the number of CPUs if not set")
        self.parser.add_argument('--nodep', action="store_true", help="Do not build deps. Use at your own risks.")
        self.parser.add_argument('--repo-base-url', action="store", help=("Use the following base URL instead of " + defaultBaseRepoUrl))
        self.parser.add_argument('--extra-git-script', action="append", help="Path (relative to ARSDKBuildUtils directory) to an extra script which will be run before updating git repo (with path as its first argument)")
        self.parser.add_argument('--arch', action="append", help="Architectures to be built. May be ignored depending of the target. May fail if an invalid arch name is provided. (Use only if you know what you're doing !)")
        self.parser.add_argument('--mp', action="store_true", help="Run in multiprocess mode (experimental !)")


    def parse(self, argv):

        AL_FILE=ARPathFromHere('.alreadyLaunched')
        if len(argv) == 1 and not os.path.exists(AL_FILE):
            ARPrint('This is the first time you run this script without arguments.')
            ARPrint('Running without arguments will build all available libraries/binaries for all available targets.')
            ARPrint('If you want to select which targets/libraries/binaries you want to build, use the command line options.')
            ARPrint('')
            ARPrint('If you rerun this command again, this message will not be displayed again and the build will be done.')
            ARPrint('')
            ARPrint(' --> Running with --help to show the possible options')
            tmp = open(AL_FILE, 'w')
            tmp.close()
            argv.append('--help')

        args=self.parser.parse_args(argv[1:])

        ARLog ('Args = ' + str(args))


        # Parse OPTs
        if args.force_clean:
            self.isForceClean = True
        if args.all_cleanup:
            self.isForceClean = True
            self.isForceCleanup = True
        if args.doc:
            self.genDoc = True
        if args.install_doc:
            self.genDoc = True
            self.installDoc = True
        if args.none:
            self.doNothing = True
        if args.nogit:
            self.noGit = True
        if args.nodep:
            self.noDeps = True
        if args.target:
            for arg in args.target:
                self.activeTargets.append(self.availableTargets.getTarget(arg))
        if args.binary:
            for arg in args.binary:
                t_bin = self.availableBinaries.getBin(arg)
                self.activeBins.append(t_bin)
        if args.library:
            for arg in args.library:
                t_lib = self.availableLibraries.getLib(arg)
                self.activeLibs.append(t_lib)
        if args.inhouse:
            self.isInHouse = True
        if args.clean:
            self.isClean = True
        if args.debug:
            self.isDebug = True
        if args.j and int(args.j) >= 0:
            self.threads = int(args.j)
        if args.repo_base_url:
            self.repoBaseUrl = args.repo_base_url
        if args.extra_git_script:
            self.extraGitScripts = args.extra_git_script[:]
        if args.arch:
            self.archs = args.arch[:]
        if args.mp:
            self.multiProcess = True

        # Fill default values if needed
        if not self.activeTargets:
            for tar in self.availableTargets.list:
                self.activeTargets.append(tar)
        if not self.activeBins and not self.activeLibs:
            for bin in self.availableBinaries.list:
                self.activeBins.append(bin)
            for lib in self.availableLibraries.list:
                self.activeLibs.append(lib)
        if self.threads == 0:
            self.threads = 1
        elif self.threads < 0:
            self.threads = ARGetNumberOfCpus()
            ARLog('Using automatic -j --> -j ' + str(self.threads))

        # If in clean mode, reverse build order(clean deps after)
        if self.isClean:
            newLibs = []
            for lib in reversed(self.activeLibs):
                newLibs.append(lib)
            self.activeLibs = newLibs
            newBins = []
            for bin in reversed(self.activeBins):
                newBins.append(bin)
            self.activeBins = newBins

    def dump(self):
        ARLog('Build script called with the following configuration:')
        ARLog(' - FORCE CLEANUP  = ' + str(self.isForceCleanup))
        ARLog(' - FORCE CLEAN    = ' + str(self.isForceClean))
        ARLog(' - DEBUG          = ' + str(self.isDebug))
        ARLog(' - CLEAN          = ' + str(self.isClean))
        ARLog(' - GENERATE DOC   = ' + str(self.genDoc))
        ARLog(' - INSTALL DOC    = ' + str(self.installDoc))
        ARLog(' - DO NOTHING     = ' + str(self.doNothing))
        ARLog(' - NO GIT         = ' + str(self.noGit))
        ARLog(' - NO DEPS        = ' + str(self.noDeps))
        ARLog(' - NB THREADS     = ' + str(self.threads))
        ARLog(' - MULTIPROCESS   = ' + str(self.multiProcess))
        ARLog('Active targets : {')
        for tar in self.activeTargets:
            ARLog(' - %(tar)s' % locals())
        ARLog('}')
        ARLog('Active libraries : {')
        for lib in self.activeLibs:
            ARLog(' - %(lib)s' % locals())
        ARLog('}')
        ARLog('Active binaries : {')
        for bin in self.activeBins:
            ARLog(' - %(bin)s' % locals())
        ARLog('}')
        ARLog('')
