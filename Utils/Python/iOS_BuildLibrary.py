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
from Darwin_RunXcodeBuild import *
from iOS_HandlePrebuiltDep import *
import shutil
import re
from multiprocessing import Lock, Pool, Manager

XCRunCache = {}

def iOS_getXCRunExec(program, sdk, failOnError=True):
    if XCRunCache.get(sdk):
        if XCRunCache[sdk].get(program):
            val = XCRunCache[sdk][program]
            return val
    val = ARExecuteGetStdout(["xcrun", "--sdk", sdk, "--find", program], failOnError=failOnError)
    if not XCRunCache.get(sdk):
        cacheDict = { program: val }
        XCRunCache[sdk] = cacheDict
    else:
        XCRunCache[sdk][program] = val
    return val

def iOS_GetXcodeProject(lib):
    # 1st check : the iOS dir must exist
    iOSPath = lib.path + '/iOS'
    if not os.path.exists(iOSPath):
        return None
    # 2nd check, the iOS dir must contain a .xcodeproj directory
    directories = [ d for d in os.listdir(iOSPath) if os.path.isdir(os.path.join(iOSPath, d))]
    for d in directories:
        if '.xcodeproj' in d:
            return os.path.join(iOSPath, d)
    return None

def iOS_HasXcodeProject(lib):
    return iOS_GetXcodeProject(lib) is not None

def iOS_MakePostProcessCb(lib, BuiltLibs, sslLibs, cryptoLibs, Strip, ArchLibDir):
    def iOS_PostProcessCb(arg):
        p_res = arg[0]
        p_updatedlib = arg[1]
            
        # Get the static libs installed
        if p_res:
            liblower = lib.name.lower()
            newLibs = [ os.path.join(ArchLibDir, l) for l in os.listdir(ArchLibDir) if '.a' in l]
            if lib.ext:
                for libToStrip in newLibs:
                    ARExecute(Strip + ' -S ' + libToStrip, failOnError=False)
            if (lib.name == 'libressl'):
                sslLibs.extend([os.path.join(ArchLibDir, 'libssl.a')])
                cryptoLibs.extend([os.path.join(ArchLibDir, 'libcrypto.a')])
                ARExecute('libtool -static -o ' + os.path.join(ArchLibDir, 'libressl.a') + ' ' + os.path.join(ArchLibDir, 'libssl.a') + ' ' + os.path.join(ArchLibDir, 'libcrypto.a'), failOnError=False)
                BuiltLibs.extend([os.path.join(ArchLibDir, 'libressl.a')])
            else:
                BuiltLibs.extend(newLibs)
        
    return iOS_PostProcessCb

def iOS_BuildLibrary(target, lib, clean=False, debug=False, nodeps=False, inhouse=False, requestedArchs=None, isMp=False):
    args = dict(locals())

    StartDumpArgs(**args)

    # Sanity check : is library valid for this target
    if not lib.isAvailableForTarget(target):
        ARLog('lib%(lib)s does not need to be built for %(target)s' % locals())
        return EndDumpArgs(res=True, **args)

    # First thing : build deps
    if not nodeps:
        for pb in lib.pbdeps:
            if not iOS_HandlePrebuiltDep(target, pb, clean=clean, debug=debug):
                ARLog('Error while handling prebuilt library %(pb)s' % locals())
                return EndDumpArgs(res=False, **args)
        for dep in lib.deps:
            ARLog('Building lib%(dep)s (dependancy of lib%(lib)s)' % locals())
            if target.hasAlreadyBuilt(dep):
                ARLog('Dependancy lib%(dep)s already built for %(target)s' % locals())
            elif not dep.isAvailableForTarget(target):
                ARLog('Dependancy lib%(dep)s does not need to be built for %(target)s' % locals())
            elif iOS_BuildLibrary(target, dep, clean, debug, nodeps, inhouse, requestedArchs):
                ARLog('Dependancy lib%(dep)s built' % locals())
            else:
                ARLog('Error while building dependancy lib%(dep)s' %locals())
                return EndDumpArgs(res=False, **args)
    else:
        ARLog('Skipping deps building for %(lib)s' % locals())

    target.addTriedLibrary(lib)

    # Check that we're building on Mac OSX
    if not ARExecute('test $(uname) = Darwin',
                     failOnError=False,
                     printErrorMessage=False):
        ARLog('Can\'t build an iOS library while not on Mac OSX (Darwin)')
        return EndDumpArgs(res=True, **args)

    # iOS libraries consists of two exclusive parts
    # 1> An autotools library
    # 2> An Xcode project

    KnownArchs = [ { 'arch':'armv7', 'platform':'iPhoneOS', 'minos':'iphoneos' },
                   { 'arch':'armv7s', 'platform':'iPhoneOS', 'minos':'iphoneos' },
                   { 'arch':'arm64', 'platform':'iPhoneOS', 'minos':'iphoneos' },
    #               { 'arch':'i386', 'platform':'iPhoneSimulator', 'minos':'ios-simulator' },
                   { 'arch':'x86_64', 'platform':'iPhoneSimulator', 'minos':'ios-simulator' }]

    KnownEabis = [ arch['arch'] for arch in KnownArchs ]
    ValidArchs = []

    if requestedArchs:
        ValidArchs = [ arch for arch in KnownArchs if arch['arch'] in requestedArchs ]
        for ra in requestedArchs:
            if ra not in KnownEabis:
                ARLog('Error : requested arch %(ra)s is not available for target iOS' % locals())
                ARLog('  Avaiable archs : %(KnownEabis)s' % locals())
                return EndDumpArgs(res=False, **args)
    if not ValidArchs:
        ValidArchs = KnownArchs


    InstallDir    = ARPathFromHere('Targets/%(target)s/Install/' % locals())
    FrameworksDir = '%(InstallDir)s/Frameworks/' % locals()

    libLower = lib.name.lower()
    libPrefix = 'lib' if ((not libLower.startswith('lib')) and (not lib.ext)) else ''
    
    Framework     = '%(FrameworksDir)s/%(libPrefix)s%(lib)s.framework' % locals()
    FrameworkDbg  = '%(FrameworksDir)s/%(libPrefix)s%(lib)s_dbg.framework' % locals()

    # Build the autotools part
    BuiltLibs = []
    sslLibs = []
    cryptoLibs = []
    if Common_IsConfigureLibrary(lib):
        # Add extra exports to force configure to assume that we have a working malloc
        # If not set, configure will fail the malloc test and will use 'rpl_malloc' and 'rpl_realloc'
        # for libraries which defines the AC_FUNC_MALLOC in their configure.ac
        # This leads to link issues for programs.
        forcedMalloc = ARSetEnvIfEmpty('ac_cv_func_malloc_0_nonnull', 'yes')
        forcedRealloc = ARSetEnvIfEmpty('ac_cv_func_realloc_0_nonnull', 'yes')
        pool = Pool(processes=len(ValidArchs))
        poolResults = []
        retStatus = True
        bLock = Manager().Lock()
        cLock = Manager().Lock()
        mLock = None
        
        for dictionnary in ValidArchs:
            arch = dictionnary['arch']
            platform = dictionnary['platform']
            minos = dictionnary['minos']
            # Find latest iOS platform
            iOSSDKRoot = '/Applications/Xcode.app/Contents/Developer/Platforms/%(platform)s.platform/Developer/SDKs/' % locals()
            Subdirs = os.walk(iOSSDKRoot).next()[1]
            Subdirs.sort()
            if len(Subdirs) > 0:
                Sysroot = iOSSDKRoot + Subdirs[-1]
            else:
                ARLog('Unable to find a suitable iOS SDK for %(platform)s' % locals())
                return EndDumpArgs(res=False, **args)
            SdkVersionMatch = re.search(r'[0-9]*\.[0-9]*', Subdirs[-1])
            if SdkVersionMatch:
                SdkVersion = SdkVersionMatch.group(0)
            else:
                ARLog('Unable to find a suitable iOS SDK for %(platform)s' % locals())
                return EndDumpArgs(res=False, **args)
            SdkLower = platform.lower()
            Compiler = iOS_getXCRunExec('clang', SdkLower)
            Ar = iOS_getXCRunExec('ar', SdkLower)
            Ranlib = iOS_getXCRunExec('ranlib', SdkLower)
            Strip = iOS_getXCRunExec('strip', SdkLower)

            # Generate unique alternate install dir for libs
            ArchLibDir = ARPathFromHere('Targets/%(target)s/Build/.install_%(lib)s_%(arch)s_%(debug)s' % locals())
            # Add extra configure flags
            ExtraCommonFlags = [ "-arch %(arch)s" % locals(),
                                 "-isysroot %(Sysroot)s" % locals() ]
            ExtraCommonClangFlags = [ "-std=gnu99" ]
            ExtraCommonNonLlvmFlags = [ "-m%(minos)s-version-min=%(SdkVersion)s" % locals() ]
            ExtraCFlags = []
            ExtraCClangFlags = [ "-x c" ]
            ExtraASFlags = []
            ExtraASClangFlags = [ "-x assembler-with-cpp" ]
            ExtraOBJCFlags = []
            ExtraOBJCClangFlags = [ "-x objective-c",
                                    "-fobjc-arc" ]
                                    
            CFLAGSString = 'CFLAGS="'
            OBJCFLAGSString = 'OBJCFLAGS="'
            CPPFLAGSString = 'CPPFLAGS="'
            ASFLAGSString = 'CCASFLAGS="'
            
            if not lib.ext:
                for flag in ExtraCClangFlags:
                    CFLAGSString = '%(CFLAGSString)s %(flag)s' % locals()
                for flag in ExtraOBJCClangFlags:
                    OBJCFLAGSString = '%(OBJCFLAGSString)s %(flag)s' % locals()
                for flag in ExtraASClangFlags:
                    ASFLAGSString = '%(ASFLAGSString)s %(flag)s' % locals()
                for flag in ExtraCommonClangFlags:
                    CFLAGSString = '%(CFLAGSString)s %(flag)s' % locals()
                    OBJCFLAGSString = '%(OBJCFLAGSString)s %(flag)s' % locals()
                    CPPFLAGSString = '%(CPPFLAGSString)s %(flag)s' % locals()
                    ASFLAGSString = '%(ASFLAGSString)s %(flag)s' % locals()
                    
            for flag in ExtraCommonNonLlvmFlags:
                CFLAGSString = '%(CFLAGSString)s %(flag)s' % locals()
                OBJCFLAGSString = '%(OBJCFLAGSString)s %(flag)s' % locals()
                CPPFLAGSString = '%(CPPFLAGSString)s %(flag)s' % locals()
                ASFLAGSString = '%(ASFLAGSString)s %(flag)s' % locals()
            for flag in ExtraCFlags:
                CFLAGSString = '%(CFLAGSString)s %(flag)s' % locals()
            for flag in ExtraOBJCFlags:
                OBJCFLAGSString = '%(OBJCFLAGSString)s %(flag)s' % locals()
            for flag in ExtraASFlags:
                ASFLAGSString = '%(ASFLAGSString)s %(flag)s' % locals()
            for flag in ExtraCommonFlags:
                CFLAGSString = '%(CFLAGSString)s %(flag)s' % locals()
                OBJCFLAGSString = '%(OBJCFLAGSString)s %(flag)s' % locals()
                CPPFLAGSString = '%(CPPFLAGSString)s %(flag)s' % locals()
                ASFLAGSString = '%(ASFLAGSString)s %(flag)s' % locals()
            CFLAGSString = CFLAGSString + '"'
            OBJCFLAGSString = OBJCFLAGSString + '"'
            CPPFLAGSString = CPPFLAGSString + '"'
            ASFLAGSString = ASFLAGSString + '"'
            ExtraConfFlags = ['--host=arm-apple',
                              '--disable-shared',
                              '--libdir=%(ArchLibDir)s' % locals(),
                              'CC=%(Compiler)s' % locals(),
                              'OBJC=%(Compiler)s' % locals(),
                              'CCAS=%(Compiler)s' % locals(),
                              'AR=%(Ar)s' % locals(),
                              'RANLIB=%(Ranlib)s' % locals(),
                              CFLAGSString,
                              OBJCFLAGSString,
                              CPPFLAGSString,
                              ASFLAGSString]
            
            block_MakePostProcess = iOS_MakePostProcessCb(lib, BuiltLibs, sslLibs, cryptoLibs, Strip, ArchLibDir)
            
            if isMp:
                poolRes = pool.apply_async(Common_BuildConfigureLibrary,
                                           args=(target, lib,),
                                           kwds={'extraArgs':ExtraConfFlags,
                                                 'clean':clean,
                                                 'debug':debug,
                                                 'confdirSuffix':arch,
                                                 'noSharedObjects':True,
                                                 'inhouse':inhouse,
                                                 'bootstrapLock':bLock,
                                                 'configureLock':cLock,
                                                 'makeLock':mLock,
                                                 'isMp':isMp,},
                                           callback=block_MakePostProcess)
                poolResults.append(poolRes)
            else:
                retStatus = Common_BuildConfigureLibrary(target, lib, extraArgs=ExtraConfFlags, clean=clean, debug=debug, confdirSuffix=arch, noSharedObjects=True, inhouse=inhouse, bootstrapLock=bLock, configureLock=cLock, makeLock=mLock, isMp=False)
                block_MakePostProcess((retStatus, lib))

        if isMp:
            for p in poolResults:
                (p_res, p_updatedlib) = p.get()
                if not p_res:
                    retStatus = False

        # Remove any added export
        if forcedMalloc:
            ARUnsetEnv('ac_cv_func_malloc_0_nonnull')
        if forcedRealloc:
            ARUnsetEnv('ac_cv_func_realloc_0_nonnull')
        if not retStatus:
            return EndDumpArgs(res=False, **args)
        
        res = True
        if not clean:
            # Make fat library
            OutputDir     = '%(InstallDir)s/lib/' % locals()
            
            libPrefix = 'lib' if not lib.ext else ''
            
            if (lib.name == 'libressl'):
                lipoSsl = '%(OutputDir)s/libssl.a' % locals()
                cryptoSsl = '%(OutputDir)s/libcrypto.a' % locals()
                ARExecute('lipo ' + ARListAsBashArg(sslLibs) + ' -create -output ' + lipoSsl)
                ARExecute('lipo ' + ARListAsBashArg(cryptoLibs) + ' -create -output ' + cryptoSsl)

            OutputLibrary = '%(OutputDir)s/%(libPrefix)s%(lib)s.a' % locals()
            if debug:
                OutputLibrary = '%(OutputDir)s/%(libPrefix)s%(lib)s_dbg.a' % locals()
            if not os.path.exists(OutputDir):
                os.makedirs(OutputDir)
            res = ARExecute('lipo ' + ARListAsBashArg(BuiltLibs) + ' -create -output ' + OutputLibrary)
            # Create framework
            FinalFramework = Framework
            if debug:
                FinalFramework = FrameworkDbg
            suffix = '_dbg' if debug else ''
            FrameworkLib     = '%(FinalFramework)s/%(libPrefix)s%(lib)s%(suffix)s' % locals()
            FrameworkHeaders = '%(FinalFramework)s/Headers/' % locals()
            ARDeleteIfExists(FinalFramework)
            os.makedirs(FinalFramework)
            libIncDirPrefix = 'lib' if not lib.ext else ''
            if (lib.name == 'libressl'):
                shutil.copytree('%(InstallDir)s/include/openssl' % locals(), FrameworkHeaders)
            else:
                shutil.copytree('%(InstallDir)s/include/%(libIncDirPrefix)s%(lib)s' % locals(), FrameworkHeaders)
            shutil.copyfile(OutputLibrary, FrameworkLib)

    elif iOS_HasXcodeProject(lib):
        res = Darwin_RunXcodeBuild(target, lib, iOS_GetXcodeProject(lib), ValidArchs, debug, clean)

    else:
        ARLog('The library lib%(lib)s does not contains either an autotools or an Xcode project' % locals())
        res = False

    if res:
        target.addBuiltLibrary(lib)

    return EndDumpArgs(res, **args)
