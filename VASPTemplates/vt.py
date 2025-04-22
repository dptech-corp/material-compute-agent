#!/usr/bin/python3
from tarfile import DIRTYPE
import library
import sys
from library import pharser
from library import generator
filename=sys.argv[1]
calcdir=sys.argv[2]
#先将所有的内容展开
VTLines=[]
try:
    fp=open(filename,'r')
except:
    print("Failed to open file: %s"%filename)
Lines=fp.readlines()
Lines[-1]+='\n'
for Line in Lines:
    pharser.PushVTLines(VTLines,Line)
#再将所有的变量进行替换
INPUTLINES=pharser.pharseVTLines(VTLines)
#再将展开的内容扩展为四个输入文件
generator.writeinputfile(INPUTLINES,calcdir)
