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

def Android_AppendDepsPrebuiltAndroidMk(target, lib, mkfile, array, suffix, rootDir):
    
    for soName in lib.soLibs:
        libPrefix = 'lib' if not soName.startswith('lib') else ''
        libPrefixUpper = libPrefix.upper()
        
        soNameUpper = libPrefixUpper + soName.upper()
        soNameLower = libPrefix + soName.lower()
        pbName = '%(soNameUpper)s-prebuilt' % locals()
        if not pbName in array:
            mkfile.write('# %(soNameUpper)s\n' % locals())
            mkfile.write('include $(CLEAR_VARS)\n')
            mkfile.write('\n')
            mkfile.write('LOCAL_MODULE := %(pbName)s\n' % locals())

            mkfile.write('LOCAL_SRC_FILES := %(rootDir)s/$(TARGET_ARCH_ABI)/lib/%(soName)s' % locals() + '\n')
            
            mkfile.write('\n')
            mkfile.write('include $(PREBUILT_SHARED_LIBRARY)\n')
            mkfile.write('\n')
            array.append(pbName)
    

def Android_CreateApplicationMk(projectRoot, abis):
    appMkName = '%(projectRoot)s/jni/Application.mk' % locals()
    appMkTmpName = '%(projectRoot)s/jni/Application.mk.new' % locals()
    appMk = open(appMkTmpName, 'w')
    appMk.write('APP_ABI := ')
    for abi in abis:
        appMk.write (abi + ' ')
    appMk.write('\n')
    appMk.write('APP_PLATFORM := android-' + os.environ.get('AR_ANDROID_MIN_VERSION') + '\n')
    appMk.close()
    ARReplaceFileIfDifferent(appMkName, appMkTmpName)

def Android_CreateAndroidManifest(projectRoot, lib):
    androidManifestName = '%(projectRoot)s/AndroidManifest.xml' % locals()
    androidManifestTmpName = '%(projectRoot)s/AndroidManifest.xml.new' % locals()
    libLower = lib.name.lower()
    androidMinVersion = os.environ.get('AR_ANDROID_MIN_VERSION')
    androidTargetVersion = os.environ.get('AR_ANDROID_API_VERSION')
    androidManifest = open(androidManifestTmpName, 'w')
    androidManifest.write('<?xml version="1.0" encoding="utf-8"?>\n')
    androidManifest.write('<manifest xmlns:android="http://schemas.android.com/apk/res/android"\n')
    androidManifest.write('    package="com.parrot.arsdk.%(libLower)s"' % locals())
    androidManifest.write('  android:installLocation="auto"\n')
    androidManifest.write('  android:versionCode="1"\n')
    androidManifest.write('  android:versionName="1" >\n')
    androidManifest.write('\n')
    androidManifest.write('    <uses-sdk\n')
    androidManifest.write('      android:minSdkVersion="%(androidMinVersion)s"\n' % locals())
    androidManifest.write('      android:targetSdkVersion="%(androidTargetVersion)s" />\n' % locals())
    androidManifest.write('</manifest>\n')
    androidManifest.close()
    ARReplaceFileIfDifferent(androidManifestName, androidManifestTmpName)

def Android_CreateAndroidMk(target, projectRoot, installRoot, lib, debug, hasNative=True, inhouse=False):
    JniRootDir = '%(projectRoot)s/jni/' % locals()
    andMkName = '%(JniRootDir)s/Android.mk' % locals()
    andMkTmpName = '%(JniRootDir)s/Android.mk.new' % locals()

    suffix = '_dbg' if debug else ''
    prebuilts = []

    andMk = open(andMkTmpName, 'w')
    andMk.write('LOCAL_PATH := $(call my-dir)\n')
    andMk.write('\n')
    # Write prebuilt deps (use shared)
    lib.runOnAllDeps(target, Android_AppendDepsPrebuiltAndroidMk, mkfile=andMk, array=prebuilts, suffix=suffix, rootDir=installRoot)
    # Write prebuilt self (use shared)
    libUpper = lib.name.upper()
    libLower = lib.name.lower()
    if hasNative:
        andMk.write('# lib%(lib)s\n' % locals())
        andMk.write('include $(CLEAR_VARS)\n')
        andMk.write('\n')
        andMk.write('LOCAL_MODULE := LIB%(libUpper)s-prebuilt\n' % locals())
        andMk.write('LOCAL_SRC_FILES := %(installRoot)s/$(TARGET_ARCH_ABI)/lib/lib%(libLower)s%(suffix)s.' % locals() + target.soext + '\n')
        andMk.write('\n')
        andMk.write('include $(PREBUILT_SHARED_LIBRARY)\n')
        andMk.write('\n')
    # Write JNI Compiler wrapper
    andMk.write('# JNI Wrapper\n')
    andMk.write('include $(CLEAR_VARS)\n')
    andMk.write('\n')
    # TEMP ALWAYS USE -g !!!
    #andMk.write('LOCAL_CFLAGS := \n')
    andMk.write('LOCAL_CFLAGS := -g\n')
    # END OF TEMP ALWAYS USE -g !!!
    if inhouse:
        andMk.write('LOCAL_CFLAGS += -D_IN_HOUSE\n')
    andMk.write('ifeq ($(TARGET_ARCH_ABI), armeabi-v7a)\n')
    andMk.write('    LOCAL_CFLAGS += -mfloat-abi=softfp -mfpu=neon\n')
    andMk.write('endif\n')
    andMk.write('LOCAL_C_INCLUDES:= %(installRoot)s/$(TARGET_ARCH_ABI)/include\n' % locals())
    andMk.write('LOCAL_MODULE := lib%(libLower)s_android%(suffix)s\n' % locals())
    JniCFiles = []
    for Dir, directories, files in os.walk(JniRootDir):
        for _file in files:
            if _file.endswith('.c'):
                JniCFiles.append (os.path.join(Dir, _file).replace(JniRootDir, ''))
    if JniCFiles:
        andMk.write('LOCAL_SRC_FILES :=')
        for _file in JniCFiles:
            andMk.write(' %(_file)s' % locals())
        andMk.write('\n')
    andMk.write('LOCAL_LDLIBS := -llog -lz\n')
    if hasNative or prebuilts:
        andMk.write('LOCAL_SHARED_LIBRARIES :=')
    if hasNative:
        andMk.write(' LIB%(libUpper)s-prebuilt' % locals())
    for dep in prebuilts:
        andMk.write(' %(dep)s' % locals())
    andMk.write('\n')
    andMk.write('include $(BUILD_SHARED_LIBRARY)\n')
    andMk.close()
    ARReplaceFileIfDifferent(andMkName, andMkTmpName)
