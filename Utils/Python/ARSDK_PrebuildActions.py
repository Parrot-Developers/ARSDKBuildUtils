#!/usr/bin/env python3
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
import os
import re
from optparse import OptionParser

# Generated file disclaimer
GENERATED_FILE_DISCLAIMER='''/*
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
*/
/*
 * GENERATED FILE
 *  Do not modify this file, it will be erased during the next configure run 
 */
'''

from ARFuncs import *

#################################
# Add Prebuild processing here  #
#################################

#################################
# Generate JAVA Enums from C    #
#  Enums                        #
#################################

class AREnumType:
    def __init__(self):
        self.name = ''
        self.entries = []
        self.hasToString = False
        self.toStringFileName = ''
        self.toStringPrototype = ''
    def addEntry(self, entry):
        self.entries.append(entry)
    def setName(self, name):
        self.name = name
    def setToStringFileName(self, fname, prototype):
        self.hasToString = True
        self.toStringFileName = fname
        self.toStringPrototype = prototype

class AREnumEntry:
    "Represent an enum entry in C"
    def __init__(self, name, value, comment):
        self.name = name
        self.value = value
        self.comment = comment

def readEnumEntriesFromFile(filename, inputDir, outputDir):
    ALL_LINES = [line.strip() for line in open(filename)]
    DATA_LINES = []
    # Strip empty lines
    for line in ALL_LINES:
        if line:
            DATA_LINES.append(line)
    # Loop over lines to find enums
    currentEnumType = AREnumType()
    allEnums = []
    foundEnum = False
    noEnumInThisFile = False
    previousValue = -1 # So next value is zero
    for line in DATA_LINES:

        if line == '// ARSDK_NO_ENUM_PREPROCESS //':
            noEnumInThisFile = True
            break

        if not foundEnum:
            if line.startswith('typedef enum'):
                foundEnum = True
                previousValue = -1
            elif 'ToString' in line:
                _, _, enumName = line.partition('(')
                enumName, _, _ = enumName.partition(' ')
                for enum in allEnums:
                    if enum.name == enumName:
                        cFileName = os.path.dirname(filename) + '/' + os.path.basename(filename).replace('.h', '.c')
                        cFileName = cFileName.replace(inputDir, outputDir)
                        prototype = line.rstrip(';')
                        enum.setToStringFileName(cFileName, prototype)
                        break
        else:
            if line.startswith('}'):
                foundEnum = False
                enumName, _, _ = line.partition(';')
                _, _, enumName = enumName.partition('}')
                enumName = enumName.strip()
                currentEnumType.setName(enumName)
                allEnums.append(currentEnumType)
                currentEnumType = AREnumType()
            elif not line.startswith('{'):
                if re.match('[\ \t]*[/*]', line) is not None:
                    continue
                # Get name
                name, _, _ = line.partition(' ')
                name = name.strip(',')
                # Get value
                _, _, value = line.partition('=')
                value, _, _ = value.partition(',')
                value = value.strip()
                if not value:
                    value = str(previousValue + 1)
                while not ARStringIsInteger(value):
                    for prevEntry in currentEnumType.entries:
                        if prevEntry.name == value:
                            value = prevEntry.value
                            break
                    break
                previousValue = int(value)
                # Get comment
                _, _, comment = line.partition('/**<')
                comment, _, _ = comment.partition('*/')
                comment = comment.strip()
                # If the comment is not in /**< */ format, try ///< format
                if comment == '':
                    _, _, comment = line.partition('///<')
                    comment = comment.strip()
                entry = AREnumEntry(name, value, comment)
                currentEnumType.addEntry(entry)

    if noEnumInThisFile:
        return []
    else:
        return allEnums

def entryConstructor(entry, last=False):
    retVal = '   '
    if entry.comment != '':
        retVal += '/** ' + entry.comment + ' */\n    '
    if entry.comment == '':
        retVal += entry.name + ' (' + entry.value + ')'
    else:
        retVal += entry.name + ' (' + entry.value + ', "' + entry.comment + '")'
    if last:
        retVal += ';'
    else:
        retVal += ','
    retVal += '\n'
    return retVal

def writeEnumToJavaFile(enumType, outDir, javaPackage):
    CLASS_NAME = enumType.name.lstrip('e') + '_ENUM'
    JFILE_NAME = outDir + CLASS_NAME + '.java'
    jfile      = open(JFILE_NAME, 'w')

    jfile.write(GENERATED_FILE_DISCLAIMER)
    jfile.write('\n')
    jfile.write('package ' + javaPackage + ';\n')
    jfile.write('\n')
    jfile.write('import java.util.HashMap;\n')
    jfile.write('\n')
    jfile.write('/**\n')
    jfile.write(' * Java copy of the ' + enumType.name + ' enum\n')
    jfile.write(' */\n')
    jfile.write('public enum ' + CLASS_NAME + ' {\n')
    unknownEnumEntry = AREnumEntry(enumType.name + "_UNKNOWN_ENUM_VALUE", "Integer.MIN_VALUE", "Dummy value for all unknown cases")
    jfile.write(entryConstructor(unknownEnumEntry))
    for entry in enumType.entries[:-1]:
        jfile.write(entryConstructor(entry))
    entry = enumType.entries[-1]
    jfile.write(entryConstructor(entry, True))
    jfile.write('\n')
    jfile.write('    private final int value;\n')
    jfile.write('    private final String comment;\n');
    jfile.write('    static HashMap<Integer, ' + CLASS_NAME + '> valuesList;\n')
    jfile.write('\n')
    jfile.write('    ' + CLASS_NAME + ' (int value) {\n')
    jfile.write('        this.value = value;\n')
    jfile.write('        this.comment = null;\n')
    jfile.write('    }\n')
    jfile.write('\n')
    jfile.write('    ' + CLASS_NAME + ' (int value, String comment) {\n')
    jfile.write('        this.value = value;\n')
    jfile.write('        this.comment = comment;\n')
    jfile.write('    }\n')
    jfile.write('\n')
    jfile.write('    /**\n')
    jfile.write('     * Gets the int value of the enum\n')
    jfile.write('     * @return int value of the enum\n')
    jfile.write('     */\n')
    jfile.write('    public int getValue () {\n')
    jfile.write('        return value;\n')
    jfile.write('    }\n')
    jfile.write('\n')
    jfile.write('    /**\n')
    jfile.write('     * Gets the ' + CLASS_NAME + ' instance from a C enum value\n')
    jfile.write('     * @param value C value of the enum\n')
    jfile.write('     * @return The ' + CLASS_NAME + ' instance, or null if the C enum value was not valid\n')
    jfile.write('     */\n')
    jfile.write('    public static ' + CLASS_NAME + ' getFromValue (int value) {\n')
    jfile.write('        if (null == valuesList) {\n')
    jfile.write('            ' + CLASS_NAME + ' [] valuesArray = ' + CLASS_NAME + '.values ();\n')
    jfile.write('            valuesList = new HashMap<Integer, ' + CLASS_NAME + '> (valuesArray.length);\n')
    jfile.write('            for (' + CLASS_NAME + ' entry : valuesArray) {\n')
    jfile.write('                valuesList.put (entry.getValue (), entry);\n')
    jfile.write('            }\n')
    jfile.write('        }\n')
    jfile.write('        ' + CLASS_NAME + ' retVal = valuesList.get (value);\n')
    jfile.write('        if (retVal == null) {\n')
    jfile.write('            retVal = ' + unknownEnumEntry.name + ';\n')
    jfile.write('        }\n')
    jfile.write('        return retVal;')
    jfile.write('    }\n')
    jfile.write('\n')
    jfile.write('    /**\n')
    jfile.write('     * Returns the enum comment as a description string\n')
    jfile.write('     * @return The enum description\n')
    jfile.write('     */\n')
    jfile.write('    public String toString () {\n')
    jfile.write('        if (this.comment != null) {\n')
    jfile.write('            return this.comment;\n')
    jfile.write('        }\n')
    jfile.write('        return super.toString ();\n')
    jfile.write('    }\n')
    jfile.write('}\n')
    jfile.close()

def writeToStringFunction(enumType, libName):
    if not enumType.hasToString:
        return
    CNAME = os.path.basename(enumType.toStringFileName)
    HNAME = libName + '/' + CNAME.replace('.c', '.h')
    VARNAME, _, _ = enumType.toStringPrototype.partition(')')
    _, _, VARNAME = VARNAME.partition(enumType.name + ' ')

    cfile = open(enumType.toStringFileName, 'w')

    cfile.write(GENERATED_FILE_DISCLAIMER)
    cfile.write('\n')
    cfile.write('/**\n')
    cfile.write(' * @file ' + CNAME + '\n')
    cfile.write(' * @brief ToString function for ' + enumType.name + ' enum\n')
    cfile.write(' */\n')
    cfile.write('\n')
    cfile.write('#include <' + HNAME + '>\n')
    cfile.write('\n')
    cfile.write(enumType.toStringPrototype + '\n')
    cfile.write('{\n')
    cfile.write('    switch (' + VARNAME + ')\n')
    cfile.write('    {\n')
    for entry in enumType.entries:
        cfile.write('    case ' + entry.name + ':\n')
        cfile.write('        return "' + entry.comment + '";\n')
        cfile.write('        break;\n')
    cfile.write('    default:\n')
    cfile.write('        break;\n')
    cfile.write('    }\n')
    cfile.write('    return "Unknown value";\n')
    cfile.write('}\n')

    cfile.close()

#################################
# Generate JAVA Enums from C    #
# Main                          #
#################################

#################################
# Generic infos about the lib   #
#################################

def generateFiles(topDir, libName, outdir, options):
    # Directories
    INPUT_DIR = topDir + '/Includes/' + libName + '/'

    # Java/JNI package
    LIB_MODULE=libName.replace('lib', '')
    JAVA_PACKAGE = 'com.parrot.arsdk.' + LIB_MODULE.lower()
    JAVA_PACKAGE_DIR = JAVA_PACKAGE.replace('.', '/')


    OUTPUT_DIR = outdir + '/Sources/'
    JAVA_OUT_DIR = outdir + '/JNI/java/' + JAVA_PACKAGE_DIR + '/'


    # Create dir if neededif not os.path.exists(OUTPUT_DIR):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
    if not os.path.exists(JAVA_OUT_DIR):
        os.makedirs(JAVA_OUT_DIR)

    for fname in os.listdir(INPUT_DIR):
        if fname.endswith('.h'):
            completeFile = INPUT_DIR + fname
            allEnums = readEnumEntriesFromFile(completeFile, INPUT_DIR, OUTPUT_DIR)
            for enumType in allEnums:
                if not options.java_disabled:
                    writeEnumToJavaFile(enumType, JAVA_OUT_DIR, JAVA_PACKAGE)
                if not options.tostr_disabled:
                    writeToStringFunction(enumType, libName)

def main():
    parser = OptionParser()
    parser.add_option("-r", "--root", dest="root",
                      default='',
                      help="root directory")
    parser.add_option("-l", "--lib", dest="lib",
                      default='',
                      help="libAR* library name")
    parser.add_option("-o", "--outdir", dest="outdir",
                      default='',
                      help="output directory")
    parser.add_option("--disable-java", dest="java_disabled",
                      action="store_true",
                      default=False,
                      help="disable Java generation")
    parser.add_option("--disable-tostr", dest="tostr_disabled",
                      action="store_true",
                      default=False,
                      help="disable toString generation")
    (options, args) = parser.parse_args()
    if (options.root == '') and (options.lib == ''):
        confDir=sys.argv[1]
        configureAcFile = open(confDir + '/configure.ac', 'rb')
        AC_INIT_LINE=configureAcFile.readline().decode("utf-8")
        while not AC_INIT_LINE.startswith('AC_INIT') and '' != AC_INIT_LINE:
            AC_INIT_LINE=configureAcFile.readline().decode("utf-8")
        if '' == AC_INIT_LINE:
            ARPrint('Unable to read from configure.ac file !')
            sys.exit(1)
        AC_ARGS=re.findall(r'\[[^]]*\]', AC_INIT_LINE)
        libName=AC_ARGS[0].replace('[', '').replace(']', '')
        topDir=confDir + '/..'
    elif (options.root == '') or (options.lib == ''):
            ARPrint('--lib and --root must be present together !')
            sys.exit(1)
    else:
        libName=options.lib
        topDir=options.root
        outdir = options.outdir if options.outdir else topDir + '/gen'
    generateFiles(topDir, libName, outdir, options)
    generateFiles(outdir, libName, outdir, options)

if __name__ == '__main__':
    main()

#END
