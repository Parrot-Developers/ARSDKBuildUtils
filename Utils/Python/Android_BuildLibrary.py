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
from Common_RunAntScript import *
from Android_CreateFiles import *
from Common_HandlePrebuiltDep import *
import shutil
from multiprocessing import Lock, Pool, Manager

KnownArchs = [{ 'arch' : 'arm',  'eabi' : 'armeabi',     'host' : 'arm-linux-androideabi' },
              { 'arch' : 'arm',  'eabi' : 'armeabi-v7a', 'host' : 'arm-linux-androideabi' },
              { 'arch' : 'mips', 'eabi' : 'mips',        'host' : 'mipsel-linux-android' },
              { 'arch' : 'x86',  'eabi' : 'x86',         'host' : 'i686-linux-android' },
]

def Android_BuildLibrary(target, lib, clean=False, debug=False, nodeps=False, inhouse=False, requestedArchs=None, isMp=False):
    args = dict(locals())

    StartDumpArgs(**args)

    ANDROID_SDK_VERSION = os.environ.get('AR_ANDROID_API_VERSION')

    # Check that ANDROID_SDK_PATH and ANDROID_NDK_PATH environment variables are set
    if not os.environ.get('ANDROID_SDK_PATH') or not os.environ.get('ANDROID_NDK_PATH'):
        ARLog('ANDROID_SDK_PATH and ANDROID_NDK_PATH environment variabled must be set to build a library for %(target)s' % locals())
        return EndDumpArgs(res=False, **args)

    # Sanity check : is library valid for this target
    if not lib.isAvailableForTarget(target):
        ARLog('lib%(lib)s does not need to be built for %(target)s' % locals())
        return EndDumpArgs(res=True, **args)

    KnownEabis =  [ arch['eabi'] for arch in KnownArchs ]

    ValidArchs = []

    if requestedArchs:
        ValidArchs = [ arch for arch in KnownArchs if arch['eabi'] in requestedArchs ]
        for ra in requestedArchs:
            if ra not in KnownEabis:
                ARLog('Error : requested arch %(ra)s is not available for target Android' % locals())
                ARLog('  Avaiable archs : %(KnownEabis)s' % locals())
                return EndDumpArgs(res=False, **args)
    if not ValidArchs:
        ValidArchs = KnownArchs


    # First thing : build deps
    if not nodeps:
        for pb in lib.pbdeps:
            abis = [arch['eabi'] for arch in ValidArchs]
            if not Common_HandlePrebuiltDep(target, pb, outputSuffixes=abis):
                ARLog('Error while handling prebuilt library %(pb)s' % locals())
                return EndDumpArgs(res=False, **args)
        for dep in lib.deps:
            ARLog('Building lib%(dep)s (dependancy of lib%(lib)s)' % locals())
            if target.hasAlreadyBuilt(dep):
                ARLog('Dependancy lib%(dep)s already built for %(target)s' % locals())
            elif not dep.isAvailableForTarget(target):
                ARLog('Dependancy lib%(dep)s does not need to be built for %(target)s' % locals())
            elif Android_BuildLibrary(target, dep, clean, debug, nodeps, inhouse, requestedArchs):
                ARLog('Dependancy lib%(dep)s built' % locals())
            else:
                ARLog('Error while building dependancy lib%(dep)s' %locals())
                return EndDumpArgs(res=False, **args)
    else:
        ARLog('Skipping deps building for %(lib)s' % locals())

    target.addTriedLibrary(lib)

    res = True

    libLower = lib.name.lower()
    suffix = '_dbg' if debug else ''
    libPrefix = 'lib' if not libLower.startswith('lib') else ''

    hasNative = False

    # 1> Autotools part (Optionnal)
    if Common_IsConfigureLibrary(lib):
        hasNative = True

        forcedMalloc = ARSetEnvIfEmpty('ac_cv_func_malloc_0_nonnull', 'yes')
        forcedRealloc = ARSetEnvIfEmpty('ac_cv_func_realloc_0_nonnull', 'yes')

        pool = Pool(processes=len(ValidArchs))
        poolResults = []
        retStatus = True
        bLock = Manager().Lock()
        cLock = Manager().Lock()
        mLock = None

        for archInfos in ValidArchs:
            # Read archInfos
            arch = archInfos['arch']
            eabi = archInfos['eabi']
            host = archInfos['host']
            # Check that the compiler is in the path
            compilerTestName = '%(host)s-gcc' % locals()
            if not ARExistsInPath(compilerTestName):
                ARLog('%(compilerTestName)s is not in your path' % locals())
                ARLog('You need to install it as a standalone toolchain to use this build script')
                ARLog('(See NDK Doc)')
                retStatus=False
                break

            # Add extra configure flags
            ExtraConfFlags = ['--host=%(host)s' % locals(),
                              '--disable-static',
                              '--enable-shared']
            LdFlagsArr=['-llog -lz']
            if not lib.ext:
                LdFlagsString = 'LDFLAGS=" ' + ARListAsBashArg(LdFlagsArr) + '"'
            else:
                LdFlagsString = 'LIBS=" ' + ARListAsBashArg(LdFlagsArr) + '"'

            ExtraConfFlags.append(LdFlagsString)
            if not lib.ext:
                ExtraConfFlags.append('--disable-so-version')
            if eabi == 'armeabi':
                ExtraConfFlags.append('CFLAGS=" -march=armv5te"')
            elif eabi == 'armeabi-v7a':
                ExtraConfFlags.append('CFLAGS=" -march=armv7-a"')

            # Call configure/make/make install
            stripVersionNumber = lib.ext and not clean

            if isMp:
                poolRes = pool.apply_async(Common_BuildConfigureLibrary,
                                           args=(target, lib,),
                                           kwds={'extraArgs':ExtraConfFlags,
                                                 'clean':clean,
                                                 'debug':debug,
                                                 'confdirSuffix':eabi,
                                                 'installSubDir':eabi,
                                                 'stripVersionNumber':stripVersionNumber,
                                                 'inhouse':inhouse,
                                                 'bootstrapLock':bLock,
                                                 'configureLock':cLock,
                                                 'makeLock':mLock,
                                                 'isMp':isMp,},
                                           callback=None)
                poolResults.append(poolRes)
            else:
                retStatus = Common_BuildConfigureLibrary(target, lib, extraArgs=ExtraConfFlags, clean=clean, debug=debug, confdirSuffix=eabi, installSubDir=eabi, stripVersionNumber=stripVersionNumber, inhouse=inhouse, bootstrapLock=bLock, configureLock=cLock, makeLock=mLock, isMp=False)

        if isMp:
            for p in poolResults:
                (p_res, p_updatedlib) = p.get()
                if not p_res:
                    retStatus = False
                else:
                    for p_lib in p_updatedlib.soLibs:
                        if not p_lib in lib.soLibs:
                            lib.soLibs.append(p_lib)
        pool.close()
        pool.join()

        if forcedMalloc:
            ARUnsetEnv('ac_cv_func_malloc_0_nonnull')
        if forcedRealloc:
            ARUnsetEnv('ac_cv_func_realloc_0_nonnull')
        if not retStatus:
            return EndDumpArgs(res=False, **args)

    # 2 Java part (Pure Java or Java + JNI), mandatory
    # Declare path
    JniPath = lib.path + '/JNI'
    AndroidPath = lib.path + '/Android'
    JavaBuildDir = ARPathFromHere('Targets/%(target)s/Build/%(libPrefix)s%(lib)s_Java' % locals())
    JavaBuildDirDbg = ARPathFromHere('Targets/%(target)s/Build/%(libPrefix)s%(lib)s_Java_dbg' % locals())
    OutputJarDir = ARPathFromHere('Targets/%(target)s/Install/jars/release/' % locals())
    OutputJar = '%(OutputJarDir)s/%(libPrefix)s%(lib)s.jar' % locals()
    OutputJarDirDbg = ARPathFromHere('Targets/%(target)s/Install/jars/debug/' % locals())
    OutputJarDbg = '%(OutputJarDirDbg)s/%(libPrefix)s%(lib)s_dbg.jar' % locals()
    AndroidSoLib = '%(libPrefix)s%(libLower)s_android.' % locals() + target.soext
    AndroidSoLibDbg = '%(libPrefix)s%(libLower)s_android_dbg.' % locals() + target.soext
    # Select build path depending on debug flag
    ActualJavaBuildDir = JavaBuildDir if not debug else JavaBuildDirDbg
    ActualOutputJarDir = OutputJarDir if not debug else OutputJarDirDbg
    ActualOutputJar    = OutputJar    if not debug else OutputJarDbg
    ActualAndroidSoLib = AndroidSoLib if not debug else AndroidSoLibDbg

    # Check for full java Android projects
    if os.path.exists(AndroidPath):
        BuildXmlFile = '%(AndroidPath)s/build.xml' % locals()
        if not os.path.exists(BuildXmlFile):
            ARLog('Unable to build %(libPrefix)s%(lib)s -> Missing build.xml script' % locals())
            return EndDumpArgs(res=False, **args)
        ClassPath=os.environ.get('ANDROID_SDK_PATH') + '/platforms/android-%(ANDROID_SDK_VERSION)s/android.jar' % locals()
        for dep in lib.deps:
            ClassPath += ':%(ActualOutputJarDir)s/lib%(dep)s%(suffix)s.jar' % locals()
        for pbdep in lib.pbdeps:
            ClassPath += ':%(OutputJarDir)s/%(pbdep)s.jar' % locals()
        if not os.path.exists(ActualJavaBuildDir):
            os.makedirs(ActualJavaBuildDir)
        if clean:
            if not ARExecute('ant -f %(BuildXmlFile)s -Ddist.dir=%(OutputJarDir)s -Dbuild.dir=%(JavaBuildDir)s -Dproject.classpath=%(ClassPath)s clean' % locals()):
                return EndDumpArgs(res=False, **args)
            if not ARExecute('ant -f %(BuildXmlFile)s -Ddist.dir=%(OutputJarDirDbg)s -Dbuild.dir=%(JavaBuildDirDbg)s -Dproject.classpath=%(ClassPath)s clean' % locals()):
                return EndDumpArgs(res=False, **args)
        elif debug:
            if not ARExecute('ant -f %(BuildXmlFile)s -Ddist.dir=%(ActualOutputJarDir)s -Dbuild.dir=%(ActualJavaBuildDir)s -Dproject.classpath=%(ClassPath)s debug' % locals()):
                return EndDumpArgs(res=False, **args)
        else:
            if not ARExecute('ant -f %(BuildXmlFile)s -Ddist.dir=%(ActualOutputJarDir)s -Dbuild.dir=%(ActualJavaBuildDir)s -Dproject.classpath=%(ClassPath)s release' % locals()):
                return EndDumpArgs(res=False, **args)
    # Else, search for JNI subprojects
    elif os.path.exists(JniPath):
        mustRunAnt = False
        # Declare dirs
        JniJavaDir  = '%(JniPath)s/java' % locals()
        JniCDir     = '%(JniPath)s/c' % locals()
        JniJavaGenDir = '%(JniPath)s/../gen/JNI/java' % locals()
        JniCGenDir = '%(JniPath)s/../gen/JNI/c' % locals()
        BuildSrcDir = '%(ActualJavaBuildDir)s/src' % locals()
        BuildJniDir = '%(ActualJavaBuildDir)s/jni' % locals()
        if not clean:
            # Copy files from JNI Dirs to Build Dir
            if not os.path.exists(ActualJavaBuildDir):
                os.makedirs(ActualJavaBuildDir)
            ARCopyAndReplace(JniJavaDir, BuildSrcDir, deletePrevious=True)
            if os.path.exists(JniJavaGenDir):
                ARCopyAndReplace(JniJavaGenDir, BuildSrcDir, deletePrevious=False)
            ARCopyAndReplace(JniCDir, BuildJniDir, deletePrevious=True, ignoreRegexpsForDeletion=[r'.*mk'])
            if os.path.exists(JniCGenDir):
                ARCopyAndReplace(JniCGenDir, BuildJniDir, deletePrevious=False)
            # Create Android.mk / Application.mk / AndroidManifest.xml
            Android_CreateApplicationMk(ActualJavaBuildDir, [arch['eabi'] for arch in ValidArchs])
            Android_CreateAndroidManifest(ActualJavaBuildDir, lib)
            Android_CreateAndroidMk(target, ActualJavaBuildDir, ARPathFromHere('Targets/%(target)s/Install' % locals()), lib, debug, hasNative, inhouse=inhouse)
            # Call ndk-build
            buildDir = Chdir(ActualJavaBuildDir)
            ndk_debug = ''
            if debug:
                ndk_debug = 'NDK_DEBUG=1'
            res = ARExecute(os.environ.get('ANDROID_NDK_PATH') + '/ndk-build -j ' + ndk_debug)
            buildDir.exit()
            if not res:
                ARLog('Error while running ndk-build')
                return EndDumpArgs(res=False, **args)
            # Call java build (+ make jar)
            classpath = ' -cp ' + os.environ.get('ANDROID_SDK_PATH') + '/platforms/android-%(ANDROID_SDK_VERSION)s/android.jar' % locals()
            if lib.deps or lib.pbdeps:
                classpath += ':"%(ActualOutputJarDir)s/*"' % locals()

            JavaFilesDir = '%(BuildSrcDir)s/com/parrot/arsdk/%(libLower)s/' % locals()
            JavaFiles = ARExecuteGetStdout(['find', JavaFilesDir, '-name', '*.java']).replace('\n', ' ')
            if not ARExecute('javac -source 1.6 -target 1.6 -sourcepath %(BuildSrcDir)s %(JavaFiles)s %(classpath)s' % locals()):
                ARLog('Error while building java sources')
                return EndDumpArgs(res=False, **args)
            if not os.path.exists(ActualOutputJarDir):
                os.makedirs(ActualOutputJarDir)
            # Move good files in a ./lib directory (instead of ./libs)
            for archInfos in ValidArchs:
                eabi = archInfos['eabi']
                JarLibDir = '%(ActualJavaBuildDir)s/lib/%(eabi)s' % locals()
                if not os.path.exists(JarLibDir):
                    os.makedirs(JarLibDir)
                for baseDir, directories, files in os.walk('%(ActualJavaBuildDir)s/libs/%(eabi)s' % locals()):
                    for _file in files:
                        if _file == '%(libPrefix)s%(libLower)s%(suffix)s.' % locals() + target.soext or _file == ActualAndroidSoLib:
                            shutil.copy2(os.path.join(baseDir, _file), os.path.join(JarLibDir, _file))
            # Create JAR File
            if not ARExecute('jar cf %(ActualOutputJar)s -C %(ActualJavaBuildDir)s ./lib -C %(BuildSrcDir)s .' % locals()):
                ARLog('Error while creating jar file')
                return EndDumpArgs(res=False, **args)
            # Copy output so libraries into target dir
            for archInfos in ValidArchs:
                eabi = archInfos['eabi']
                shutil.copy2('%(ActualJavaBuildDir)s/libs/%(eabi)s/%(ActualAndroidSoLib)s' % locals(),
                             ARPathFromHere('Targets/%(target)s/Install/%(eabi)s/lib/%(ActualAndroidSoLib)s' % locals()))
        else:
            ARDeleteIfExists(OutputJarDbg, OutputJar, JavaBuildDir, JavaBuildDirDbg)
            for archInfos in ValidArchs:
                eabi = archInfos['eabi']
                LibRelease = ARPathFromHere('Targets/%(target)s/Install/%(eabi)s/lib/%(AndroidSoLib)s' % locals())
                LibDebug = ARPathFromHere('Targets/%(target)s/Install/%(eabi)s/lib/%(AndroidSoLibDbg)s' % locals())
                ARDeleteIfExists(LibRelease, LibDebug)


    # For autotools only library, just make a jar containing the .so file
    elif Common_IsConfigureLibrary(lib):
        if not clean:
            if not os.path.exists(ActualOutputJarDir):
                os.makedirs(ActualOutputJarDir)
            LibsDir = '%(ActualJavaBuildDir)s/lib' % locals()
            if lib.customBuild is None:
                ARDeleteIfExists (LibsDir)
            if not os.path.exists(LibsDir):
                os.makedirs(LibsDir)
            for archInfos in ValidArchs:
                eabi = archInfos['eabi']
                eabiDir = '%(LibsDir)s/%(eabi)s' % locals()
                if not os.path.exists(eabiDir):
                    os.makedirs(eabiDir)
                for soname in lib.soLibs:
                    shutil.copy2(ARPathFromHere('Targets/%(target)s/Install/%(eabi)s/lib/%(soname)s' % locals()), '%(eabiDir)s/%(soname)s' % locals())
            if not ARExecute('jar cf %(ActualOutputJar)s -C %(ActualJavaBuildDir)s ./lib' % locals()):
                ARLog('Error while creating jar file')
                return EndDumpArgs(res=False, **args)
        else:
            ARDeleteIfExists(OutputJarDbg, OutputJar)

    # Mark library as built if all went good
    if res:
        target.addBuiltLibrary(lib)

    return EndDumpArgs(res, **args)
