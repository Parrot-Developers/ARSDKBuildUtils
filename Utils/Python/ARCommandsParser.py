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
# #################################### #
# Parser module for ARCommands         #
# Also includes some utility functions #
# #################################### #

import os
from xml.dom.minidom import parseString

from ARFuncs import *


#
# String manipulation function
#

def ARCapitalize (arstr):
    if len(arstr) > 1:
        return arstr[0].upper() + arstr[1:]
    elif len(arstr) == 1:
        return arstr[0].upper()
    else:
        return ''

def ARUncapitalize (arstr):
    if len(arstr) > 1:
        return arstr[0].lower() + arstr[1:]
    elif len(arstr) == 1:
        return arstr[0].lower()
    else:
        return ''


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

def ARJavaEnumType (Module, Submodule, Enum):
    # MODULE_SUBMODULE_ENUM_"ENUM"
    return Module.upper () + '_' + Submodule.upper () + '_' + Enum.upper () + '_ENUM'

def ARJavaEnumValue (Module, Submodule, Enum, Name):
    # MODULE_SUBMODULE_ENUM_"ENUM".MODULE_SUBMODULE_ENUM_NAME
    return ARJavaEnumType (Module, Submodule, Enum) + '.' + AREnumValue (Module, Submodule, Enum, Name)

#
# Global "Has arg of type" array
#

hasArgOfType = {
    'u8': True, 'i8' : False,
    'u16': True, 'i16': False,
    'u32': False, 'i32': False,
    'u64': False, 'i64': False,
    'float': False, 'double': False,
    'string': False, 'enum': False
}

#
# Class definitions
#


class AREnum:
    "Represent an enum of an argument"
    def __init__(self, enumName):
        self.name     = enumName
        self.comments = []
    def addCommentLine(self, newCommentLine):
        self.comments.append(newCommentLine)
    def check(self):
        ret = ''
        if len (self.comments) == 0:
            ret = ret + '\n--- Enum ' + self.name + ' don\'t have any comment !'
        return ret

class ARArg:
    "Represent an argument of a command"
    def __init__(self, argName, argType):
        self.name     = argName
        self.type     = argType
        hasArgOfType[argType] = True
        self.comments = []
        self.enums    = []
    def addCommentLine(self, newCommentLine):
        self.comments.append(newCommentLine)
    def addEnum(self, newEnum):
        self.enums.append(newEnum)
    def check(self):
        ret = ''
        enumret = ''
        if len (self.comments) == 0:
            ret = ret + '\n--- Argument ' + self.name + ' don\'t have any comment !'
        for enum in self.enums:
            enumret = enumret + enum.check ()
        if len (enumret) != 0:
            ret = ret + '\n-- Argument ' + self.name + ' has errors in its enums:'
        ret = ret + enumret
        return ret

class ARCommandListType:
    NONE = 0
    LIST = 1
    MAP = 2
    @staticmethod
    def getFromString(val):
        if val == 'NONE':
            return ARCommandListType.NONE
        elif val == 'LIST':
            return ARCommandListType.LIST
        elif val == 'MAP':
            return ARCommandListType.MAP
        else:
            raise ValueError
    @staticmethod
    def toString(val):
        if val == ARCommandListType.NONE:
            return 'NONE'
        elif val == ARCommandListType.LIST:
            return 'LIST'
        elif val == ARCommandListType.MAP:
            return 'MAP'
        else:
            return 'Unknown'

class ARCommandBuffer:
    NON_ACK = 0
    ACK = 1
    HIGH_PRIO = 2
    @staticmethod
    def getFromString(val):
        if val == 'NON_ACK':
            return ARCommandBuffer.NON_ACK
        elif val == 'ACK':
            return ARCommandBuffer.ACK
        elif val == 'HIGH_PRIO':
            return ARCommandBuffer.HIGH_PRIO
        else:
            raise ValueError
    @staticmethod
    def toString(val):
        if val == ARCommandBuffer.NON_ACK:
            return 'NON_ACK'
        elif val == ARCommandBuffer.ACK:
            return 'ACK'
        elif val == ARCommandBuffer.HIGH_PRIO:
            return 'HIGH_PRIO'
        else:
            return 'Unknown'
    

class ARCommandTimeoutPolicy:
    POP = 0
    RETRY = 1
    FLUSH = 2
    @staticmethod
    def getFromString(val):
        if val == 'POP':
            return ARCommandTimeoutPolicy.POP
        elif val == 'RETRY':
            return ARCommandTimeoutPolicy.RETRY
        elif val == 'FLUSH':
            return ARCommandTimeoutPolicy.FLUSH
        else:
            raise ValueError
    @staticmethod
    def toString(val):
        if val == ARCommandTimeoutPolicy.POP:
            return 'POP'
        elif val == ARCommandTimeoutPolicy.RETRY:
            return 'RETRY'
        elif val == ARCommandTimeoutPolicy.FLUSH:
            return 'FLUSH'
        else:
            return 'Unknown'

class ARCommand:
    "Represent a command"
    def __init__(self, cmdName):
        self.name     = cmdName
        self.comments = []
        self.args     = []
        self.buf      = ARCommandBuffer.ACK
        self.timeout  = ARCommandTimeoutPolicy.POP
        self.listtype = ARCommandListType.NONE
    def setListType(self, ltype):
        self.listtype = ltype
    def setBufferType(self, btype):
        self.buf      = btype
    def setTimeoutPolicy(self, pol):
        self.timeout  = pol
    def addCommentLine(self, newCommentLine):
        self.comments.append(newCommentLine)
    def addArgument(self, newArgument):
        self.args.append(newArgument)
    def check(self):
        ret = ''
        argret = ''
        if len (self.comments) == 0:
            ret = ret + '\n-- Command ' + self.name + ' don\'t have any comment !'
        for arg in self.args:
            argret = argret + arg.check ()
        if len (argret) != 0:
            ret = ret + '\n-- Command ' + self.name + ' has errors in its arguments:'
        ret = ret + argret
        return ret

MAX_CLASS_ID = 255
CLASS_MAX_CMDS = 65536
class ARClass:
    "Represent a class of commands"
    def __init__(self, className, ident):
        self.name     = className
        self.ident    = ident
        self.comments = []
        self.cmds     = []
        self.projExt  = ''
    def addCommentLine(self, newCommentLine):
        self.comments.append(newCommentLine)
    def addCommand(self, newCommand):
        self.cmds.append(newCommand)
    def check(self):
        ret = ''
        cmdret = ''
        if len (self.comments) == 0:
            ret = ret + '\n- Class ' + self.name + ' don\'t have any comment !'
        if int (self.ident) > MAX_PROJECT_ID:
            ret = ret + '\n- Class ' + self.name + ' has a too big id number (' + self.ident + '). Maximum is ' + str (MAX_CLASS_ID) + '.'
        if len (self.cmds) > CLASS_MAX_CMDS:
            ret = ret + '\n- Class ' + self.name + ' has too many commands (' + str (len (self.cmds)) + '). Maximum number of commands is ' + str(CLASS_MAX_CMDS) + '.'
        for cmd in self.cmds:
            cmdret = cmdret + cmd.check ()
        if len (cmdret) != 0:
            ret = ret + '\n- Class ' + self.name + ' has errors in its commands:'
        ret = ret + cmdret
        return ret

PROJECT_MAX_CLASS = 256
MAX_PROJECT_ID = 255
class ARProject:
    "Represent a project (an XML file)"
    def __init__(self, projectName, ident):
        self.name     = projectName
        self.ident    = ident
        self.comments = []
        self.classes  = []
    def addCommentLine(self, newCommentLine):
        self.comments.append (newCommentLine)
    def addClass(self, newClass):
        self.classes.append(newClass)
    def addDebugClasses(self, newClasses):
        for newClass in newClasses:
            newClass.projExt = 'Debug'
            self.classes.append (newClass)
    def check(self):
        ret = ''
        clsret = ''
        if len (self.comments) == 0:
            ret = ret + '\nProject ' + self.name + ' don\'t have any comment !'
        if int (self.ident) > MAX_PROJECT_ID:
            ret = ret + '\nProject ' + self.name + ' has a too big id number (' + self.ident + '). Maximum is ' + str (MAX_PROJECT_ID) + '.'
        if len (self.classes) > PROJECT_MAX_CLASS:
            ret = ret + '\nProject ' + self.name + ' has too many classes (' + str (len (self.classes)) + '). Maximum number of classes is ' + str(PROJECT_MAX_CLASS) + '.'
        for cls in self.classes:
            clsret = clsret + cls.check ()
        if len (clsret) != 0:
            ret = ret + '\nProject ' + self.name + ' has errors in its classes:'
        ret = ret + clsret
        return ret

#
# Parser functions
#
def parseXml(fileName, projectName, previousProjects):
    if not os.path.exists(fileName):
        return None
    file = open (fileName, 'r')
    data = file.read ()
    file.close ()
    xmlfile = parseString (data)

    # Check if the XMLFile only contains ONE project (not zero, nor more)
    xmlproj = xmlfile.getElementsByTagName ('project')
    if len (xmlproj) != 1:
        ARPrint (fileName + ' should contain exactly ONE project tag.')
        EXIT (1)
    proj = ARProject (projectName, xmlproj[0].attributes["id"].nodeValue)

    # Check if project id and name are unique
    for p2 in previousProjects:
        if p2.ident == proj.ident:
            ARPrint ('Project `' + projectName + '` has the same id as project `' + p2.name + '`.')
            ARPrint (' --> Project ID must be unique, and must NEVER change')
            ARPrint (' --> Debug Project ID are usually Project ID + 128')
            EXIT (1)
        if p2.name == proj.name:
            ARPrint ('Project `' + projectName + '` exists twice.')
            ARPrint (' --> Project must have a unique name within the application')
            EXIT (1)

    # Get project comments
    projComments = xmlproj[0].firstChild.data.splitlines ()
    for projComm in projComments:
        stripName = projComm.strip ()
        if len (stripName) != 0:
            proj.addCommentLine (stripName)

    classes = xmlfile.getElementsByTagName ('class')
    for cmdclass in classes:
        # Get class name
        currentClass = ARClass(cmdclass.attributes["name"].nodeValue, cmdclass.attributes["id"].nodeValue)
        # Check if class id and name are unique within the project
        for cls in proj.classes:
            if cls.ident == currentClass.ident:
                ARPrint ('Class `' + currentClass.name + '` has the same id as class `' + cls.name + '` within project `' + proj.name + '`.')
                ARPrint (' --> Class ID must be unique within their project, and must NEVER change')
                EXIT (1)
            if cls.name == currentClass.name:
                ARPrint ('Class `' + cls.name + '` appears multiple times in `' + proj.name + '` !')
                ARPrint (' --> Classes must have unique names in a given project (but can exist in multiple projects)')
                EXIT (1)
        # Get class comments
        classComments = cmdclass.firstChild.data.splitlines ()
        for classComm in classComments:
            stripName = classComm.strip ()
            if len (stripName) != 0:
                currentClass.addCommentLine(stripName)
        commands = cmdclass.getElementsByTagName ('cmd')
        for command in commands:
            # Get command name
            currentCommand = ARCommand(command.attributes["name"].nodeValue)
            # Check if command name is unique
            for cmd in currentClass.cmds:
                if cmd.name == currentCommand.name:
                    ARPrint ('Command `' + cmd.name + '` appears multiple times in `' + proj.name + '.' + currentClass.name + '` !')
                    ARPrint (' --> Commands must have unique names in a given class (but can exist in multiple classes)')
                    EXIT (1)

            # Try to get the suggested buffer type for the command
            try:
                cmdBufferType = ARCommandBuffer.getFromString(command.attributes["buffer"].nodeValue)
                currentCommand.setBufferType(cmdBufferType)
            except KeyError:
                pass
                
            # Try to get the suggested timeout policy for the command
            try:
                cmdTimeoutPolicy = ARCommandTimeoutPolicy.getFromString(command.attributes["timeout"].nodeValue)
                currentCommand.setTimeoutPolicy(cmdTimeoutPolicy)
            except KeyError:
                pass

            # Try to get the list type of the command
            try:
                cmdListType = ARCommandListType.getFromString(command.attributes["listtype"].nodeValue)
                currentCommand.setListType(cmdListType)
            except KeyError:
                pass

            # Get command comments
            commandComments = command.firstChild.data.splitlines ()
            for commandComm in commandComments:
                stripName = commandComm.strip ()
                if len (stripName) != 0:
                    currentCommand.addCommentLine (stripName)
            args = command.getElementsByTagName ('arg')
            for arg in args:
                # Get arg name / type
                currentArg = ARArg (arg.attributes["name"].nodeValue, arg.attributes["type"].nodeValue)
                # Check if arg name is unique
                for argTest in currentCommand.args:
                    if argTest.name == currentArg.name:
                        ARPrint ('Arg `' + currentArg.name + '` appears multiple time in `' + proj.name + '.' + currentClass.name + '.' + currentCommand.name + '` !')
                        ARPrint (' --> Args must have unique name in a given command (but can exist in multiple commands)')
                        EXIT (1)
                # Get arg comments
                argComments = arg.firstChild.data.splitlines ()
                for argComm in argComments:
                    stripName = argComm.strip ()
                    if len (stripName) != 0:
                        currentArg.addCommentLine (stripName)

                enums = arg.getElementsByTagName ('enum')
                for enum in enums:
                    currentEnum = AREnum(enum.attributes["name"].nodeValue)
                    # Get command comments
                    enumComments = enum.firstChild.data.splitlines ()
                    for enumComm in enumComments:
                        stripName = enumComm.strip ()
                        if len (stripName) != 0:
                            currentEnum.addCommentLine (stripName)
                    # Check if arg name is unique
                    for enumTest in currentArg.enums:
                        if enumTest.name == currentEnum.name:
                            ARPrint ('Enum `' + currentEnum.name + '` appears multiple time in `' + proj.name + '.' + currentClass.name + '.' + currentCommand.name + '` !')
                            ARPrint (' --> Enums must have unique name in a given command (but can exist in multiple commands)')
                            EXIT (1)
                    currentArg.addEnum(currentEnum)
                currentCommand.addArgument (currentArg)
            currentClass.addCommand (currentCommand)
        proj.addClass (currentClass)
    return proj

def parseAllProjects(projects, pathToARCommands, genDebug=False, mergeDebugProjectInReleaseProjects=False):
    XMLFILENAME_PREFIX=pathToARCommands + '/Xml/'
    XMLFILENAME_SUFFIX='_commands.xml'
    XMLDEBUGFILENAME_SUFFIX="_debug.xml"

    if 'all' in projects:
        projects = []
        listDir = os.listdir(XMLFILENAME_PREFIX)
        listDir = sorted(listDir, key=str)
        for files in listDir:
            if files.endswith (XMLFILENAME_SUFFIX):
                proj = files.replace (XMLFILENAME_SUFFIX,'')
                projects.append (proj)

    allProjects = []
    for projectName in projects:
        pr = parseXml(XMLFILENAME_PREFIX + projectName + XMLFILENAME_SUFFIX, projectName, allProjects)
        if pr is not None:
            allProjects.append(pr)
        if genDebug:
            dbgpr = parseXml(XMLFILENAME_PREFIX + projectName + XMLDEBUGFILENAME_SUFFIX, projectName + 'Debug', allProjects)
            if dbgpr is not None:
                if mergeDebugProjectInReleaseProjects:
                    pr.addDebugClasses(dbgpr.classes)
                else:
                    allProjects.append(dbgpr)

    return allProjects
