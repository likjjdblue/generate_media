# -*- coding: utf-8 -*-
import ParseXML
import mavenconfig
import re
import codecs
from os.path import isfile,isdir,exists
import os
from os import walk
import os.path
import shutil


tmpObj=ParseXML.ParseExcel(u'海云V8.0精简版部署信息表-宁波出入境检疫局.xls')
tmpObj.Run()
ContextList=tmpObj.GetResource()


def RenderFile(file):
    with codecs.open(file,'r','utf-8') as f:
        FileContent=f.read()

    TmpTupleList=re.findall(r'({{(.*?)}})',FileContent,flags=re.UNICODE)
    for tupleitem in TmpTupleList:
        for context in ContextList:
            contextvalue=ParseXML.ReflateDictKey(tupleitem[1].strip(),context)
            if not contextvalue:
                continue
            FileContent=re.sub(tupleitem[0],unicode(str(contextvalue)),FileContent,flags=re.UNICODE|re.MULTILINE)
    return FileContent



def RenderTemplate(typename):
    typename=typename.upper()
    BasePath=os.path.dirname(os.path.abspath(__file__))
    while True:
        newname=raw_input('输入新名称:')
        Matched=re.match(r'^[a-zA-Z0-9]+$',newname)
        if not Matched:
            print ('名称只能包含字母、数字')
            continue
        break
    if typename=='IRT':
        TmpConfig=mavenconfig.irtconfig
    elif typename=='IIP':
        TmpConfig=mavenconfig.iipconfig
    elif typename=='IGS':
        TmpConfig=mavenconfig.igsconfig
    elif typename=='IPM':
        TmpConfig=mavenconfig.ipmconfig


    NewTargetFolder=BasePath+'/template/'+typename+'/data/'+str(newname)
    NewTargetFolder=os.path.normpath(NewTargetFolder)

    if isdir(NewTargetFolder):
        print (u"新建失败，目录已经存在："+str(NewTargetFolder))
        return 1

    SrcTemplatePath=BasePath+'/template/'+typename+'/source'
    SrcTemplatePath=os.path.normpath(SrcTemplatePath)

    FlagOfCreated=False
    for item in walk(SrcTemplatePath):
        if item[0]==SrcTemplatePath:
            if len(item[1])>0:
                FlagOfCreated=True
                print ('拷贝目录.....')
                shutil.copytree(SrcTemplatePath,NewTargetFolder)
            if not FlagOfCreated:
                print ('新建目录:'+str(NewTargetFolder))
                os.mkdir(NewTargetFolder)
                
            for subfile in item[2]:
                print ('拷贝文件:'+str(subfile)+'...')
                shutil.copy(os.path.join(item[0],subfile),NewTargetFolder)

    #### 以下部分对模板文件进行内容 替换    ###
    FlagNeedToRename=False   ### 标识文件是否需要被重名为变量"newname"
    if TmpConfig['filtertype']==1:
        FlagNeedToRename=True

    for item in walk(NewTargetFolder):
        if len(item[2])>0:
            for subfile in item[2]:
                CurrentFile=os.path.join(item[0],subfile)
                RenderedFileContent=RenderFile(CurrentFile)
                with codecs.open(CurrentFile,'w','utf-8') as f:
                    f.write(RenderedFileContent)
                if FlagNeedToRename:
                    NewFileName=re.sub(r'^[a-zA-Z0-9]+\.properties$',str(newname)+'.properities',subfile)
                    os.rename(CurrentFile,os.path.join(item[0],NewFileName))


RenderTemplate('iip')