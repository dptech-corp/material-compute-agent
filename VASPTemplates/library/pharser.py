import os
import re
from . import settings
def PushVTLines(VTLines,Line,*args):
    #print(Line)
    ROBOOTLine=Line.strip()
    if not len(ROBOOTLine):
        return 1
    #如果是VT注释，则直接忽略
    if ROBOOTLine[0:2]=='##':
        return 1
    #如果是命令行注释，则直接忽略
    if ROBOOTLine[0:2]=='#!':
        return 1    
    #如果是写在INCAR里的注释，则原样放上去
    if ROBOOTLine[0]=='#':
        VTLines.append(Line)
        return 1
    #如果式中含有%{1}-%{n}，则进行初步的替换
    FileParameters=re.findall(r'%{[0-9]+}',Line)
    if len(FileParameters):
        replaced=[]
        for FileParameter in FileParameters:
            if FileParameter in replaced:
                continue
            FileParameter_Index=int(FileParameter[2:-1])
            Line=Line.replace(FileParameter,args[FileParameter_Index-1])
            replaced.append(FileParameter)
        VTLines.append(Line)
        return 1
    #如果是%INCLUDE开头，就进行递归
    if ROBOOTLine[0:8]=="%INCLUDE":
        parameterlist=[]
        INCLUDENAME=ROBOOTLine.split('=')[1].split('#')[0].strip()
        Parameters=re.search(r'\(.+\)',INCLUDENAME)
        if Parameters:
            parameterlist=Parameters.group()[1:-1].split(',')
            INCLUDENAME=INCLUDENAME.split(Parameters.group())[0]
        filename=findvtfile(INCLUDENAME)
        if filename:
            fp=open(filename,'r')
            FileLines=fp.readlines()
            FileLines[-1]+='\n'
            fp.close()
            for FileLine in FileLines:
                PushVTLines(VTLines,FileLine,*parameterlist)
            return  1
        else:
            print("Did not find file" + INCLUDENAME)
            return 1
    VTLines.append(Line)
    return 1


def findvtfile(fname):
    if os.access(fname,os.R_OK):
        return fname
    EnviromentPathList=[]
    if os.getenv('VTPATH'):
        EnviromentPathList=os.getenv('VTPATH').split(':')
    SettingPathList=settings.vtlist
    librarypath=os.path.dirname(__file__)
    Paths=EnviromentPathList+SettingPathList+[librarypath]
    for Path in Paths:
        if os.access(os.path.join(Path,fname),os.R_OK):
            return os.path.join(Path,fname)
        if os.access(os.path.join(Path,fname+'.vt'),os.R_OK):
            return os.path.join(Path,fname+'.vt')
    return ""

def pharseVTLines(VTLines):
    ResultLines=[]
    ParaRefDict={}
    TAGRefDict={}
    PARAVALUE={}
    PARALINES={}
    def CiteParaDict(RBLine,CiteIndex):
        #如果式中含有%{PARANAME}，则进行标记
        VTParameters=re.findall(r'%{.+}',RBLine)
        if len(VTParameters):
            cited=[]
            for VTParameter in VTParameters:
                if VTParameter in cited:
                    continue
                VTName=VTParameter[2:-1]
                try:
                    ParaRefDict[VTName].append(CiteIndex)
                except:
                    ParaRefDict[VTName]=[CiteIndex]
                cited.append(VTName)
    def CiteTagDict(TagName,CiteIndex):
        TAGRefDict[TagName]=CiteIndex
    for Line in VTLines:
        ROBOOTLine=Line.strip()
        if not len(ROBOOTLine):
            continue
        #如果是VT注释，则直接忽略
        if ROBOOTLine[0:2]=='##':
            continue
        UNOTELine=ROBOOTLine.split('#')[0]
        #如果是INCARTAG的内容，则进行标记
        if '=' in UNOTELine and UNOTELine[0]!='%':
            TagName=UNOTELine.split('=')[0].strip()
            if TagName in TAGRefDict:
                ResultLines[TAGRefDict[TagName]]=Line
                CiteParaDict(ROBOOTLine,TAGRefDict[TagName])
            else:
                ResultLines.append(Line)
                CiteTagDict(TagName,len(ResultLines)-1)
                CiteParaDict(ROBOOTLine,len(ResultLines)-1)
            continue
        #如果是定义VT参数的值，则记录该值
        if '=' in UNOTELine and UNOTELine[0]=='%':
            VTName=UNOTELine.split('=')[0].strip().split('%')[1].strip()
            VTValue=UNOTELine.split('=')[1].strip()
            PARAVALUE[VTName]=VTValue
            PARALINES[VTName]=Line
            continue
        #其他东西也不管了，一股脑塞进去
        ResultLines.append(Line)
        CiteParaDict(ROBOOTLine,len(ResultLines)-1)
    #对设定好的值进行替换
    for VTName in PARAVALUE:
        if VTName in ParaRefDict:
            CHLines=ParaRefDict[VTName]
            for CHLIndex in CHLines:
                ResultLines[CHLIndex]=ResultLines[CHLIndex].replace('%{'+VTName+'}',PARAVALUE[VTName])
        else:
            ResultLines.append(PARALINES[VTName])
    return ResultLines





        