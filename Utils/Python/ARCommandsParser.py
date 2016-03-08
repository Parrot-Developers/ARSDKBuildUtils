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

BITFIELD_TYPES = ['u8', 'u16', 'u32']
BITFIELD_TYPES_MAX_VAL = [2**7, 2**15, 2**31]

#
# Class definitions
#

class AREnumVal:
    "Represent an value of an Enum"
    def __init__(self, enumName):
        self.name     = enumName
        self.val      = None
        self.comments = []
    def addCommentLine(self, newCommentLine):
        self.comments.append(newCommentLine)
    def check(self):
        ret = ''
        if len (self.comments) == 0:
            ret = ret + '\n--- Enum value ' + self.name + ' don\'t have any comment !'
        return ret
    def __str__(self):
        desc = 'AREnumVal name:' + self.name
        desc = desc + '\n comments:' + str(self.comments)
        return desc
        
class AREnum:
    "Represent an Enum"
    def __init__(self, enumName):
        self.name     = enumName
        self.values = []
        self.comments = []
        self.usedLikeBitfield = False
    def addCommentLine(self, newCommentLine):
        self.comments.append(newCommentLine)
    def addValue(self, newValue):
        self.values.append(newValue)
    def check(self):
        ret = ''
        if len (self.enumValues) == 0:
            ret = ret + '\n--- Enum ' + self.name + ' don\'t have any values !'
        if len (self.comments) == 0:
            ret = ret + '\n--- Enum ' + self.name + ' don\'t have any comment !'
        return ret
    def __str__(self):
        desc = 'AREnum name:' + self.name
        desc = desc + '\n comments:' + str(self.comments)
        return desc
        
class ARBitfield:
    "Represent an bitfield"
    def __init__(self, enum, lenType):
        self.enum = enum
        self.type = lenType
    def check(self):
        ret = ''
        if not self.enum:
            ret = ret + '\n--- Bitfield ' + self.enum + ' don\'t have any values !'
        return ret
    def __str__(self):
        desc = 'ARBitfield of :' + self.enum.name
        return desc
    
    @staticmethod
    def checkBitfieldEnum(enum, type):
        ret = True
        enumMaxVal = 0
        for value in enum.values:
            enumVal = int(value.val) if value.val is not None else enum.values.index(value)
            if enumVal > enumMaxVal:
                enumMaxVal = enumVal
         
        typeIndex = BITFIELD_TYPES.index(type)
        bitfieldMaxVal = BITFIELD_TYPES_MAX_VAL[typeIndex]
        if (2 ** enumMaxVal) > bitfieldMaxVal:
            ret = False
            
        return ret
    
class ARArg:
    "Represent an argument of a command"
    def __init__(self, argName, argType):
        self.name     = argName
        self.type     = argType
        
        if isinstance(argType, AREnum):
            hasArgOfType['enum'] = True
        elif isinstance(argType, ARBitfield):
            hasArgOfType[argType.type] = True
        else:
            hasArgOfType[argType] = True
            
        self.comments = []
        self.enums    = [] #only for project
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
    def __str__(self):
        desc = 'ARArg name:' + self.name
        if isinstance(self.type, AREnum):
            desc = desc + '\n type:' + self.type.name
        if isinstance(self.type, ARBitfield):
            desc = desc + '\n type:bitfield:' + self.type.type + ':' + self.type.enum.name
        else:
            desc = desc + '\n type:' + self.type
        desc = desc + '\n comments:' + str(self.comments)
        return desc

class ARCommandListType:
    NONE = 0
    LIST = 1
    MAP = 2
    @staticmethod
    def getFromString(val):
        if val == 'NONE':
            return ARCommandListType.NONE
        elif val == 'LIST_ITEM':
            return ARCommandListType.LIST
        elif val == 'MAP_ITEM':
            return ARCommandListType.MAP
        else:
            raise ValueError
    @staticmethod
    def toString(val):
        if val == ARCommandListType.NONE:
            return 'NONE'
        elif val == ARCommandListType.LIST:
            return 'LIST_ITEM'
        elif val == ARCommandListType.MAP:
            return 'MAP_ITEM'
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

class ARCommandNotification:
    @staticmethod
    def getFromString(val):
        if val == 'TRUE':
            return True
        elif val == 'FALSE':
            return False
        else:
            raise ValueError

class ARComment:
    "Commentary of command or event"
    def __init__(self, title):
        self.title      = title
        self.desc       = None
        self.support    = []
        self.triggered  = None
        self.result     = None
    def addSupport(self, newSupport):
        self.support.append(newSupport)
    def check(self):
        ret = ''
        if len (self.title) == 0:
            ret = ret + '\n-- Comment don\'t have any title !'
        if len (self.support) != 0:
            ret = ret + '\n-- Comment don\'t have any support  !'
        if self.triggered == None and self.result == None:
            ret = ret + '\n-- Comment don\'t have neither triggered nor result !'
        return ret
    def __str__(self):
        desc = 'ARComment title:' + self.title
        desc = desc + '\n desc:' + str(self.desc)
        desc = desc + '\n support:' + str(self.support)
        desc = desc + '\n triggered:' + str(self.triggered)
        desc = desc + '\n result:' + str(self.result)
        return desc


class ARMessage :
    "Represent a message"
    def __init__(self, cmdName, ident):
        self.name     = cmdName
        self.ident    = ident
        self.comments = []
        self.args     = []
        self.buf      = ARCommandBuffer.ACK
        self.timeout  = ARCommandTimeoutPolicy.POP
        self.listtype = ARCommandListType.NONE
        self.isNotif  = False
        self.mapKey   = None
        self.comment  = None #TODO sup
        self.cls      = None #project only
        
    def setListType(self, ltype):
        self.listtype = ltype
    def setBufferType(self, btype):
        self.buf      = btype
    def setTimeoutPolicy(self, pol):
        self.timeout  = pol
    def setIsNotif(self, isnotif):
        self.isNotif  = isnotif
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
    def __str__(self):
        desc = self.__class__.__name__ + ' name:' + self.name
        desc = desc + '\n ident:' + self.ident

        desc = desc + '\n isNotif:' + str(self.isNotif)
        desc = desc + '\n comment:' + str(self.comment)
        desc = desc + '\n comments:' + str(self.comments)
        desc = desc + '\n args:['
        for arg in self.args:
            desc = desc + '\n' + str(arg)
        desc = desc + ']\n buf:' + str(self.buf)
        desc = desc + '\n timeout:' + str(self.timeout)
        desc = desc + '\n listtype:' + str(self.listtype)
        desc = desc + '\n mapKey:' + str(self.mapKey)
        return desc
        
    def strType(self):
        return 'Message'
        
    def formattedName(self, underscore=False):#projetc only
        if underscore:
            return ARCapitalize(self.name) if self.cls is None else ARCapitalize(self.cls.name) + '_'+  ARCapitalize(self.name)
        else:
            return self.name if self.cls is None else self.cls.name + ARCapitalize(self.name)
    def getListFlagsArg(self):
        for arg in self.args:
            if arg.name == 'list_flags':
                return arg
        return None
        
class ARCommand (ARMessage):
    "Represent a command"
    def __init__(self, cmdName, ident):
        ARMessage.__init__(self, cmdName, ident)
    def strType(self):
        return 'Command'
        
class AREvent (ARMessage):
    "Represent a event"
    def __init__(self, cmdName, ident):
        ARMessage.__init__(self, cmdName, ident)
    def strType(self):
        return 'Event'

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
        
MAX_FEATURE_ID = 255
FEATURE_MAX_CMDS_EVTS = 65536
class ARFeature:
    "Represent a feature (an XML file)"
    def __init__(self, featureName, ident):
        self.name       = featureName
        self.ident      = ident
        self.comments   = []
        self.enums      = []
        self.cmds       = []
        self.evts       = []
        self.classes    = None
    
    def addCommentLine(self, newCommentLine):
        self.comments.append (newCommentLine)
    def addEnum(self, newEnum):
        self.enums.append(newEnum)
    def addCmd(self, newCmd):
        self.cmds.append(newCmd)
    def addEvt(self, newEvt):
        self.evts.append(newEvt)
    def check(self):
        ret = ''
        clsret = ''
        if len (self.comments) == 0:
            ret = ret + '\nFeature ' + self.name + ' don\'t have any comment !'
        if int (self.ident) > MAX_FEATURE_ID:
            ret = ret + '\nFeature ' + self.name + ' has a too big id number (' + self.ident + '). Maximum is ' + str (MAX_FEATURE_ID) + '.'
        if (len (self.cmds) + len (self.evts)) > FEATURE_MAX_CMDS_EVTS:
            ret = ret + '\nFeature' + self.name + ' has too many commands and events (' + str (len (self.cmds) + len (self.evts)) + '). Maximum number of commands and events is ' + str(FEATURE_MAX_CMDS_EVTS) + '.'
        return ret
    
    def __str__(self):
        desc = 'ARFeature name:' + self.name
        desc = desc + '\n ident:' + self.ident
        desc = desc + '\n comments:' + str(self.comments)
        desc = desc + '\n enums:['
        for enum in self.enums:
            desc = desc + ' ' + str(enum)
        desc = desc + ']\n cmd:['
        for cmd in self.cmds:
            desc = desc + '\n' + str(cmd)
        desc = desc + ']\n evts:['
        for evt in self.evts:
            desc = desc + '\n' + str(evt)
        desc = desc + ']'
        return desc
    
    @staticmethod
    def fromProject(project):
        feature = ARFeature (project.name, project.ident)
        feature.comments   = project.comments
        feature.classes    = project.classes
        
        for cl in project.classes:
            for cmd in cl.cmds:
                if "event" in cl.name.lower() or "state" in cl.name.lower():
                    newCmd = AREvent(cmd.name, cl.cmds.index(cmd))
                else:
                    newCmd = ARCommand(cmd.name, cl.cmds.index(cmd))
                
                newCmd.comments = cmd.comments
                newCmd.args     = cmd.args
                newCmd.buf      = cmd.buf
                newCmd.timeout  = cmd.timeout
                newCmd.listtype = cmd.listtype
                if cmd.listtype == ARCommandListType.MAP:
                    newCmd.mapKey   = cmd.args[0]
                newCmd.isNotif  = cmd.isNotif
                newCmd.comment  = cmd.comment #TODO see
                newCmd.cls      = cl
                
                #copy enums
                for arg in cmd.args:
                    if len(arg.enums) > 0:
                        newEnum = AREnum(cl.name + '_' + cmd.name + '_' + arg.name)
                        newEnum.comments = arg.comments
                        for val in arg.enums:
                            newEnumVal = AREnumVal(val.name)
                            newEnumVal.comments = val.comments
                            newEnum.addValue(newEnumVal)
                        feature.addEnum(newEnum)
                        arg.type = newEnum
                
                if isinstance(newCmd, AREvent):
                    feature.addEvt(newCmd)
                else:
                    feature.addCmd(newCmd)
                
        return feature

#
# Parser functions
#
def parseXml(fileName, featureName, previousFeatures, genericFeature=None):
    if not os.path.exists(fileName):
        return None
    file = open (fileName, 'r')
    data = file.read ()
    file.close ()
    xmlfile = parseString (data)
    feature = None
    
    # Check if the XMLFile contains Feature
    xmlFeature = xmlfile.getElementsByTagName ('feature')
    if len (xmlFeature) > 0:
        feature = parseFeatureXml(fileName, featureName, previousFeatures, genericFeature)
    else:
        # Check if the XMLFile contains project 
        xmlproj = xmlfile.getElementsByTagName ('project')
        if len (xmlproj) > 0:
            proj = parseProjectXml(fileName, featureName, previousFeatures)
            # Convert project to feature
            feature = ARFeature.fromProject(proj)
            
    return feature

#
# Parser functions
#
def parseProjectXml(fileName, projectName, previousProjects):
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
            # Get command name / id
            currentCommand = ARCommand(command.attributes["name"].nodeValue, command.attributes["id"].nodeValue)
            # Check if command is unique
            for cmd in currentClass.cmds:
                # Check if command name is unique
                if cmd.name == currentCommand.name:
                    ARPrint ('Command `' + cmd.name + '` appears multiple times in `' + proj.name + '.' + currentClass.name + '` !')
                    ARPrint (' --> Commands must have unique names in a given class (but can exist in multiple classes)')
                    EXIT (1)
                    
                # Check if command id is unique
                if cmd.ident == currentCommand.ident:
                    ARPrint ('Command id:`' + cmd.ident + '` appears multiple times in `' + proj.name + '.' + currentClass.name + '` !')
                    ARPrint (' --> Commands must have unique id in a given class (but can exist in multiple classes)')
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
                cmdListType = ARCommandListType.getFromString(command.attributes["type"].nodeValue)
                currentCommand.setListType(cmdListType)
            except KeyError:
                pass
                
            # Try to get the notification value of the command
            try:
                isNotification = ARCommandNotification.getFromString(command.attributes["notification"].nodeValue)
                currentCommand.setIsNotif(isNotification)
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
                        ARPrint ('Arg `' + currentArg.name + '` appears multiple time in `' + ftr.name + '.' + currentCommand.name + '` !')
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
                    currentEnum = AREnumVal(enum.attributes["name"].nodeValue)
                    # Get enum comments
                    enumComments = enum.firstChild.data.splitlines ()
                    for enumComm in enumComments:
                        stripName = enumComm.strip ()
                        if len (stripName) != 0:
                            currentEnum.addCommentLine (stripName)
                    # Check if enum name is unique
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
        pr = parseProjectXml(XMLFILENAME_PREFIX + projectName + XMLFILENAME_SUFFIX, projectName, allProjects)
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

#
# Parser functions
#
def parseFeatureXml(fileName, featureName, previousFeatures, genericFtr=None):
    ARPrint ('parseFeatureXml ...')
    
    if not os.path.exists(fileName):
        return None
    file = open (fileName, 'r')
    data = file.read ()
    file.close ()
    xmlfile = parseString (data)

    # Check if the XMLFile only contains ONE feature (not zero, nor more)
    xmlproj = xmlfile.getElementsByTagName ('feature')
    if len (xmlproj) != 1:
        ARPrint (fileName + ' should contain exactly ONE feature tag.')
        EXIT (1)
    ftr = ARFeature (xmlproj[0].attributes["name"].nodeValue, xmlproj[0].attributes["id"].nodeValue)

    # Check if project id and name are unique
    for f2 in previousFeatures:
        #TODO check id >= 133 ?
        if f2.ident == ftr.ident:
            ARPrint ('Feature `' + featureName + '` has the same id as feature `' + f2.name + '`.')
            ARPrint (' --> Feature ID must be unique, and must NEVER change')
            ARPrint (' --> Debug Feature ID are usually Feature ID + 128')
            EXIT (1)
        if f2.name == ftr.name:
            ARPrint ('Feature `' + featureName + '` exists twice.')
            ARPrint (' --> Feature must have a unique name within the application')
            EXIT (1)

    # Get feature comments
    ftrComments = xmlproj[0].firstChild.data.splitlines ()
    for ftrComm in ftrComments:
        stripName = ftrComm.strip ()
        if len (stripName) != 0:
            ftr.addCommentLine (stripName)
    
    # Get enums
    tagEnums = xmlfile.getElementsByTagName ('enums')
    if len (tagEnums) == 1:
        enums = tagEnums[0].getElementsByTagName ('enum')
        for enum in enums:
            # Get enum name
            currentEnum = AREnum(enum.attributes["name"].nodeValue)
            # Check if enum name is unique
            for enum2 in ftr.enums:
                if enum2.name == currentEnum.name:
                    ARPrint ('Enum `' + enum2.name + '` appears multiple times in `' + ftr.name + '` !')
                    ARPrint (' --> Enumerations must have unique names in a given feature (but can exist in multiple features)')
                    EXIT (1)
            # Get enum comments
            enumComments = enum.firstChild.data.splitlines ()
            for enumComm in enumComments:
                stripName = enumComm.strip ()
                if len (stripName) != 0:
                    currentEnum.addCommentLine(stripName)
            # Get enum values
            tagEnumValues = enum.getElementsByTagName ('value')
            for value in tagEnumValues:
                # Get enum value name
                currentEnumValue = AREnumVal(value.attributes["name"].nodeValue)
                
                # Try to get the specified value
                try:
                    currentEnumValue.val = value.attributes["val"].nodeValue
                except KeyError:
                    pass
                
                # Check if enum name is unique
                for value2 in currentEnum.values:
                    if value2.name == currentEnumValue.name:
                        ARPrint ('Enum Value `' + value2.name + '` appears multiple times in `' + ftr.name + '.' + currentEnum.name + '` !')
                        ARPrint (' --> Enumerations value must have unique names in a given feature (but can exist in multiple Enumerations)')
                        EXIT (1)
                # Get enum comments
                enumValueComments = value.firstChild.data.splitlines ()
                for enumValComm in enumValueComments:
                    stripName = enumValComm.strip ()
                    if len (stripName) != 0:
                        currentEnumValue.addCommentLine(stripName)
                currentEnum.addValue(currentEnumValue)
                    
            ftr.addEnum(currentEnum)
    elif len (tagEnums) > 1:
        ARPrint (fileName + ' should contain maximally ONE enums tag.')
        EXIT (1)
    
    # Get msgs
    msgs = xmlfile.getElementsByTagName ('msgs')
    
    if len (msgs) != 1:
        ARPrint (fileName + ' should contain maximally ONE msgs tag.')
        EXIT (1)
    
    cmds = msgs[0].getElementsByTagName ('cmd')
    evts = msgs[0].getElementsByTagName ('evt')
    for msg in cmds + evts:
        # Get command name
        if msg in cmds:
            currentMessage = ARCommand(msg.attributes["name"].nodeValue, msg.attributes["id"].nodeValue)
        else:
            currentMessage = AREvent(msg.attributes["name"].nodeValue, msg.attributes["id"].nodeValue)
            
        # Check if message name is unique
        for ftr_msg in ftr.cmds + ftr.evts:
            # Check message
            if ftr_msg.name == currentMessage.name:
                ARPrint (ftr_msg.strType() + ' `' + ftr_msg.name + '` appears multiple times in `' + ftr.name + ' !')
                ARPrint (' --> '+ ftr_msg.strType() + ' must have unique names in a given feature (but can exist in multiple features)')
                EXIT (1)
            # Check if message id is unique
            if ftr_msg.ident == currentMessage.ident:
                ARPrint (ftr_msg.strType() + ' ' + ftr.name + '.' + msg.name + '.id ('+ftr_msg.ident+') is the same of the message `'+ ftr.name + '.' + currentMessage.name + ' !')
                ARPrint (' --> '+ ftr_msg.strType() + ' must have unique id in a given feature (but can be duplicated in multiple features)')
                EXIT (1)
        
        # Try to get the list type of the command
        try:
            msgType = msg.attributes["type"].nodeValue
            #Check if the a key is specified : type=<type:key>
            if ':' in msgType:
                listInfo = msgType.split(":")
                currentMessage.setListType(ARCommandListType.getFromString(listInfo[0]))
                mapKeyName = listInfo[1]
            else:
                currentMessage.setListType(ARCommandListType.getFromString(msgType))
        except KeyError:
            pass
        
        # get comment of command
        comment = msg.getElementsByTagName ('comment')
        if len (comment) != 1:
            ARPrint (currentMessage.name + ' should contain maximally ONE comment tag.')
            EXIT (1)
        comment = comment[0]
        currentComment = ARComment(comment.attributes["title"].nodeValue)
        
        # Try to get the description for the comment of the command
        try:
            currentComment.desc = comment.attributes["desc"].nodeValue
        except KeyError:
            #if comment has no desc, get its title has dec
            currentComment.desc = currentComment.title
        
        #if command has no multiline comments get its comment.desc has comments
        if len(currentMessage.comments) == 0:
                currentMessage.addCommentLine(currentComment.desc)
        
        # Try to get the support for the comment of the command
        try:
            supportStr = comment.attributes["support"].nodeValue
            for support in supportStr.split(";"):
                currentComment.addSupport(support)
        except KeyError:
            pass
            
        # Try to get the triggered for the comment of the command
        try:
            currentComment.triggered = comment.attributes["triggered"].nodeValue
        except KeyError:
            pass
            
        # Try to get the result for the comment of the command
        try:
            currentComment.result = comment.attributes["result"].nodeValue
        except KeyError:
            pass
        currentMessage.comment = currentComment

        # Try to get the suggested buffer type for the command
        try:
            cmdBufferType = ARCommandBuffer.getFromString(comment.attributes["buffer"].nodeValue)
            currentMessage.setBufferType(cmdBufferType)
        except KeyError:
            pass
            
        # Try to get the suggested timeout policy for the command
        try:
            cmdTimeoutPolicy = ARCommandTimeoutPolicy.getFromString(comment.attributes["timeout"].nodeValue)
            currentMessage.setTimeoutPolicy(cmdTimeoutPolicy)
        except KeyError:
            pass
            
        # Try to get the notification value of the command
        try:
            isNotification = ARCommandNotification.getFromString(comment.attributes["notification"].nodeValue)
            currentMessage.setIsNotif(isNotification)
        except KeyError:
            pass
    
        # Get args
        args = msg.getElementsByTagName ('arg')
        for arg in args:
            # Get arg name
            argName = arg.attributes["name"].nodeValue
            # Get arg type
            argType = arg.attributes["type"].nodeValue

            # Check if specific type
            specificParts = argType.split(':')
            if len(specificParts) > 1:
                if specificParts[0] == "bitfield":
                    if len(specificParts) == 3:
                        bfLen = specificParts[1]
                        bfEnum = specificParts[2]
                        # Check bitfield type
                        if not bfLen in BITFIELD_TYPES:
                            ARPrint ('Bitfield length ('+str(bfLen)+') of the argument '+argName+' of the command ' + ftr.name + '.' + currentMessage.name + ' is not correct.')
                            ARPrint (' --> Bitfield length must be unsigned type [\'u8\' ; \'u16\' ; \'u32\'].')
                            EXIT (1)
                    else:
                        ARPrint ('Bitfield Type of the argument '+argName+' of the command ' + ftr.name + '.' + currentMessage.name + ' is not correctly declared.')
                        ARPrint (' --> Bitfield must be declared like "bitfield:<unsigned type>:<enum name>".')
                        EXIT (1)
                        
                    # Check if the enum type exists
                    enumFound = None
                    for enum2 in genericFtr.enums + ftr.enums:
                        if enum2.name == bfEnum:
                            enumFound = enum2
                    if enumFound:
                        # Check if the enum can be used by bitfield
                        if not ARBitfield.checkBitfieldEnum(enumFound, bfLen):
                            ARPrint ('Bitfield of enum ('+str(bfEnum)+') in ('+bfLen+') of the argument '+argName+' of the command ' + ftr.name + '.' + currentMessage.name + ' is not correct.')
                            ARPrint (' --> Bitfield must use an enum with its maximum value compatible with the Bitfield length.')
                            EXIT (1)
                        argType =  ARBitfield(enumFound, bfLen)
                        enumFound.usedLikeBitfield = True
                    else:
                        ARPrint ('Enum Type ('+str(bfEnum)+') of the argument '+argName+' of the command ' + ftr.name + '.' + currentMessage.name + ' not known.')
                        ARPrint (' --> Enum must be declared at the start of the xml file.')
                        EXIT (1)
                        
                elif specificParts[0] == "enum":
                    enumType = specificParts[1]
                    
                    # Check if the enum type exists
                    enumFound = None
                    for enum2 in genericFtr.enums + ftr.enums:
                        if enum2.name == enumType:
                            enumFound = enum2
                    if enumFound:
                        argType = enumFound 
                    else:
                        ARPrint ('Enum Type ('+str(enumType)+') of the argument '+argName+' of the command ' + ftr.name + '.' + currentMessage.name + ' not known.')
                        ARPrint (' --> Enum must be declared at the start of the xml file.')
                        EXIT (1)
            
            # new arg
            currentArg = ARArg (argName, argType)
            # Check if arg name is unique
            for argTest in currentMessage.args:
                if argTest.name == currentArg.name:
                    ARPrint ('Arg `' + currentArg.name + '` appears multiple time in `' + proj.name + '.' + currentClass.name + '.' + currentMessage.name + '` !')
                    ARPrint (' --> Args must have unique name in a given command (but can exist in multiple commands)')
                    EXIT (1)
            
            # Try Get arg multiline comment
            if arg.firstChild:
                argComments = arg.firstChild.data.splitlines ()
                for argComm in argComments:
                    stripName = argComm.strip ()
                    if len (stripName) != 0:
                        currentArg.addCommentLine (stripName)
            
            # Try to get the description for the comment of the arg
            try:
                currentArg.addCommentLine(comment.attributes["desc"].nodeValue)
            except KeyError:
                pass
            currentMessage.addArgument (currentArg)
        
        # Find mapKey
        if currentMessage.listtype == ARCommandListType.MAP:
            if mapKeyName is None:
                currentMessage.mapKey = currentMessage.args[0]
            else:
                found = False
                for arg in currentMessage.args:
                    if arg.name == mapKeyName:
                        currentMessage.mapKey = arg
                        found = True
                        break
                if not found:
                    ARPrint ('Map Key ('+ mapKeyName +') of the '+currentMessage.strType()+' ' + ftr.name + '.' + currentMessage.name + ' is not an argument of the '+currentMessage.strType()+'.')
                    ARPrint (' --> Message of type MAP_ITEM:<Map key> must contain the map key as argument.')
                    EXIT (1)
        
        # Add the command or the event
        if isinstance(currentMessage, AREvent):
            ftr.addEvt(currentMessage)
        else:
            ftr.addCmd(currentMessage)
    return ftr

def parseAllFeatures(features, pathToARCommands, genDebug=False):
    XMLFILENAME_PREFIX=pathToARCommands + '/Xml/'
    XMLFILENAME_SUFFIX='_commands.xml'
    XMLDEBUGFILENAME_SUFFIX="_debug.xml"
    GENERIC_XML='generic.xml'

    if 'all' in features:
        features = []
        listDir = os.listdir(XMLFILENAME_PREFIX)
        listDir = sorted(listDir, key=str)
        for files in listDir:
            if files.endswith (XMLFILENAME_SUFFIX):
                ftr = files.replace (XMLFILENAME_SUFFIX,'')
                features.append (ftr)

    allFeatures = []
    
    #parse generic xml
    genericFtr = parseXml(XMLFILENAME_PREFIX + GENERIC_XML, 'generic', allFeatures)
    if genericFtr is not None:
        allFeatures.append(genericFtr)
    else:
        ARPrint ('Error during the parsing of generic.xml.')
        EXIT (1)
    
    for featureName in features:
        ft = parseXml(XMLFILENAME_PREFIX + featureName + XMLFILENAME_SUFFIX, featureName, allFeatures, genericFtr)
        if ft is not None:
            allFeatures.append(ft)
        if genDebug:
            dbgFt = parseXml(XMLFILENAME_PREFIX + featureName + XMLDEBUGFILENAME_SUFFIX, featureName + 'Debug', allFeatures)
            if dbgFt is not None:
                allFeatures.append(dbgFt)

    return allFeatures
