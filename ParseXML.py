# -*- coding: utf-8 -*-
import nodeinfo
from re import match,search,UNICODE,MULTILINE,IGNORECASE
from socket import inet_aton
from copy import deepcopy,copy
import xlrd
from os.path import isfile
from pprint import pprint

def isPortNumValid(port):
    ### 检查端口号是否是正确的,以下情况会判断为无效：###
    ###1、包含非数字字符;2、以“0”开头;3、范围不在 (0,65535] 区间
    if isinstance(port,int) or isinstance(port,float):
        return (port>0 and port<=65535)
    elif isinstance(port,str) or isinstance(port,unicode):
        port=port.strip()
        MatchedA=match(r'^\d{1,5}$',port)
        MatchedB=match(r'^[^0]+',port)
        MatchedB=match(r'^[^0]+',port)
        if MatchedA and MatchedB:
            port=int(port)
            return port>0 and port<=65535
    return False

def isIPValid(ip):
    if not isinstance(ip,str) and not isinstance(ip,unicode):
        return False
    ## 检查IP 地址是否有效###
    ip=ip.strip()
    if len(ip.split('.'))==4:
        try:
            inet_aton(ip)
            tmpList=filter(lambda x:match(r'^[^0]+',x) or match(r'^0$',x),ip.split('.'))
            if len(tmpList)!=4:
                return False
            return True
        except:
            return False
    return False


def ReflateDictKey(keystring,TmpDict):
    '''
    该函数用于将以字符串形式的dict-key 转换成实际的dict value;
    比如存在如下Dict的变量TmpDict:
    TmpDict={
    'foo':{
        "bar":{
            "name":['dblue']
        }
    }
}
    那么对于'foo','foo.bar'以及'foo.bar.name'都是有效的key-string;其他的字符串会返回None
    '''

    if not isinstance(TmpDict,dict):
        return None
    if (not isinstance(keystring,str)) and (not isinstance(keystring,unicode)):
        return None
    keystring=keystring.strip()
    TmpList=keystring.split('.')
    if len(TmpList)==1:
        if keystring in TmpDict:
            return TmpDict[keystring]
        else:
            return None
    elif len(TmpList)>1:
        if TmpList[0] not in TmpDict:
            return None
        elif TmpList[0] in TmpDict:
            return ReflateDictKey('.'.join(TmpList[1:]),TmpDict[TmpList[0]])


class ParseExcel:
    def __init__(self,filepath):
        if not isfile(filepath):
            raise Exception('无法找到指定文件:'+str(filepath))
        self.BookObj=xlrd.open_workbook(filepath,formatting_info=True)
        self.SheetObj=None

    def __PreParse(self):
        ### 自检提供的信息表内容是否完整，主要是“XXXX部署信息”sheet和 “数据库信息”sheet ###
        self.ParsedRowIndexList=[]   ###已经完成处理过的行号(用于"XXXX部署信息"sheet)###
        self.InvalidRowIndexList=[]  ###配置不正确的行号(用于"XXXX部署信息"sheet) ###

        self.ParsedRowIndexDBList=[]    ###已经完成处理过的行号(用于"数据库信息"sheet)###
        self.InvalidRowIndexDBList=[]    ###配置不正确的行号(用于"数据库信息"sheet) ###

        ##### 下面的这些list 存放从sheet中读取到的节点信息 ####
        self.NginxNodesList=[]
        self.NginxPublishNodesList=[]
        self.ElasticsearchNodesList=[]
        self.RedisNodesList=[]
        self.RabbitmqNodesList=[]
        self.MysqlNodesList=[]
        self.LogstashNodesList=[]
        self.IDSNodesList=[]
        self.MASNodesList=[]
        self.CKMNodesList=[]
        self.IIPNodesList=[]
        self.IGINodesList=[]
        self.IGSNodesList=[]
        self.IPMNodesList=[]
        self.IRTNodesList=[]

        #### 下面这些list 存放从“数据库信息”sheet中读取的节点信息####
        self.IIPDBList=[]
        self.IGIDBList=[]
        self.IGSDBList=[]
        self.IPMDBList=[]
        self.IRTDBList=[]
        self.IDODBList=[]
        self.IDSDBList=[]
        self.MASDBList=[]
        self.WECHATDBList=[]


        SheetNamesList=self.BookObj.sheet_names()
        MatchedSheetNameCounter=0
        for sheetname in SheetNamesList:
            if u'部署信息' in sheetname:
                MatchedSheetNameCounter+=1
            elif u'数据库信息' in sheetname:
                MatchedSheetNameCounter+=1
            if MatchedSheetNameCounter==2:
                break
        if MatchedSheetNameCounter<2:
            raise Exception(u"XXXX部署信息表不完整！")
        for index in range(len(SheetNamesList)):
            if u"部署信息" in SheetNamesList[index]:
                self.DeployInfoSheetIndex=index
            elif u'数据库信息' in SheetNamesList[index]:
                self.DatabaseInfoSheetIndex=index

    def __ParseDeploySheetRow(self,rowindex,servicename=None):
        ####   对"XXXX部署信息" sheet的每一行进行解析 #####
        #### 如果是聚合单元格，那么会传递“部署项”所在的列，否则就是非聚合单元格####
        ### 即servicename:None--->非合并单元格   servicename: not None ----->合并单元格
        if servicename is None:
            ServiceName=self.SheetObj.cell_value(rowindex,self.TmpServiceNamesIndex)
        else:
            ServiceName=servicename

        Port=self.SheetObj.cell_value(rowindex,self.TmpPortIndex)
        IPAddr=self.SheetObj.cell_value(rowindex,self.TmpIntranetIPIndex)

        try:
            IPAddr=IPAddr.strip()
            Port=Port.strip()
        except:
            pass

        if (not ServiceName) or (not IPAddr) or (not Port):   ###  三个列当中如果有一个为空，就判定为该行无效##
            self.InvalidRowIndexList.append(rowindex)
            return 1
        ServiceName=ServiceName.lower()
        ServiceName=ServiceName.strip()

        if ('nginx' in ServiceName) and (u'外网' in ServiceName):
            if not isIPValid(IPAddr) or not isPortNumValid(Port):
                self.InvalidRowIndexList.append(rowindex)
                return 1
            TmpNewNode=deepcopy(nodeinfo.nginxNodeInfo)
            TmpNewNode['nginx']['host']=IPAddr
            TmpNewNode['nginx']['port']=int(Port)
            self.NginxNodesList.append(TmpNewNode)
        elif ('nginx' in ServiceName) and (u'互联网' in ServiceName):
            if not isIPValid(IPAddr) or not isPortNumValid(Port):
                self.InvalidRowIndexList.append(rowindex)
                return 1
            TmpNewNode=deepcopy(nodeinfo.nginxPublishNodeInfo)
            TmpNewNode['nginxPub']['host']=IPAddr
            TmpNewNode['nginxPub']['port']=int(Port)
            self.NginxPublishNodesList.append(TmpNewNode)
        elif 'elasti' in ServiceName:
            if not isIPValid(IPAddr) or not isPortNumValid(Port):
                self.InvalidRowIndexList.append(rowindex)
                return 1
            TmpNewNode=deepcopy(nodeinfo.elasticsearchNodeInfo)
            TmpNewNode['elasticsearch']['host']=IPAddr
            TmpNewNode['elasticsearch']['port']=int(Port)
            self.ElasticsearchNodesList.append(TmpNewNode)
        elif 'redis' in ServiceName:
            if not isIPValid(IPAddr) or not isPortNumValid(Port):
                self.InvalidRowIndexList.append(rowindex)
                return 1
            TmpNewNode=deepcopy(nodeinfo.redisNodeInfo)
            TmpNewNode['redis']['host']=IPAddr
            TmpNewNode['redis']['port']=int(Port)
            self.RedisNodesList.append(TmpNewNode)
        elif 'rabbitmq'  in ServiceName:
            if not isIPValid(IPAddr):
                self.InvalidRowIndexList.append(rowindex)
                return 1
            TmpNewNode=deepcopy(nodeinfo.rabbitmqNodeInfo)
            TmpNewNode['rabbitmq']['host']=IPAddr
            if '5672'  not in Port:
                self.InvalidRowIndexList.append(rowindex)
                return 1
            TmpNewNode['rabbitmq']['port']=5672
            self.RabbitmqNodesList.append(TmpNewNode)
        elif 'mariadb' in ServiceName:
            if not isIPValid(IPAddr) or not isPortNumValid(Port):
                self.InvalidRowIndexList.append(rowindex)
                return 1
            TmpNewNode=deepcopy(nodeinfo.mysqlNodeInfo)
            TmpNewNode['mysql']['host']=IPAddr
            TmpNewNode['mysql']['port']=int(Port)
            self.MysqlNodesList.append(TmpNewNode)
        elif ('trs' in ServiceName) and ('ids' in ServiceName) :
            if not isIPValid(IPAddr)  or not isPortNumValid(Port):
                self.InvalidRowIndexList.append(rowindex)
                return 1
            TmpNewNode=deepcopy(nodeinfo.idsNodeInfo)
            TmpNewNode['ids']['host']=IPAddr
            TmpNewNode['ids']['port']=int(Port)
            self.IDSNodesList.append(TmpNewNode)
        elif ('trs' in ServiceName) and ('mas' in ServiceName) :
            if not isIPValid(IPAddr)  or not isPortNumValid(Port):
                self.InvalidRowIndexList.append(rowindex)
                return 1
            TmpNewNode=deepcopy(nodeinfo.masNodeInfo)
            TmpNewNode['mas']['host']=IPAddr
            TmpNewNode['mas']['port']=int(Port)
            self.MASNodesList.append(TmpNewNode)
        elif ('trs' in ServiceName) and ('ckm' in ServiceName) :
            if not isIPValid(IPAddr)  or not isPortNumValid(Port):
                self.InvalidRowIndexList.append(rowindex)
                return 1
            TmpNewNode=deepcopy(nodeinfo.ckmNodeInfo)
            TmpNewNode['ckm']['host']=IPAddr
            TmpNewNode['ckm']['port']=int(Port)
            self.CKMNodesList.append(TmpNewNode)
        elif u'全媒体采编'in ServiceName:
            MediaName=self.SheetObj.cell_value(rowindex,self.TmpMediaIndex)
            if isinstance(Port,str) or isinstance(Port,unicode):
                ### 对标准版的“特殊”记录方式进行处理 ####
                Port=Port.strip()
                Matched=match(r'^(\d+)',Port,flags=UNICODE)
                if Matched:Port=Matched.group(1)

            if (u'IIP.zip'in MediaName) and (u'后端' in MediaName):  ### 模糊匹配 IIP.zip（后端）   ###
                if not isIPValid(IPAddr) or not isPortNumValid(Port):
                    self.InvalidRowIndexList.append(rowindex)
                    return 1
                TmpNewNode=deepcopy(nodeinfo.iipNodeInfo)
                TmpNewNode['iip']['host']=IPAddr
                TmpNewNode['iip']['port']=int(Port)
                self.IIPNodesList.append(TmpNewNode)
        elif u'问政互动' in ServiceName:
            MediaName=self.SheetObj.cell_value(rowindex,self.TmpMediaIndex)
            if (u'IGI.zip' in MediaName) and (u'后端' in MediaName):  ###模糊匹配 IGI.zip（后端） ###
                if not isIPValid(IPAddr) or not isPortNumValid(Port):
                    self.InvalidRowIndexList.append(rowindex)
                    return 1
                TmpNewNode=deepcopy(nodeinfo.igiNodeInfo)
                TmpNewNode['igi']['host']=IPAddr
                TmpNewNode['igi']['port']=int(Port)
                self.IGINodesList.append(TmpNewNode)
        elif u'智能检索' in ServiceName:
            MediaName=self.SheetObj.cell_value(rowindex,self.TmpMediaIndex)
            if u'IGS.zip' in MediaName:
                if not isIPValid(IPAddr) or not isPortNumValid(Port):
                    self.InvalidRowIndexList.append(rowindex)
                    return 1
                TmpNewNode=deepcopy(nodeinfo.igsNodeInfo)
                TmpNewNode['igs']['host']=IPAddr
                TmpNewNode['igs']['port']=int(Port)
                self.IGSNodesList.append(TmpNewNode)
        elif u'绩效考核' in ServiceName:
            MediaName=self.SheetObj.cell_value(rowindex,self.TmpMediaIndex)
            if not isIPValid(IPAddr) or not isPortNumValid(Port):
                self.InvalidRowIndexList.append(rowindex)
                return 1
            if u'IPM.zip' in MediaName:
                TmpNewNode=deepcopy(nodeinfo.ipmNodeInfo)
                TmpNewNode['ipm']['host']=IPAddr
                TmpNewNode['ipm']['port']=int(Port)
                self.IPMNodesList.append(TmpNewNode)
            elif u'IRT.zip' in MediaName:
                TmpNewNode=deepcopy(nodeinfo.irtNodeInfo)
                TmpNewNode['irt']['host']=IPAddr
                TmpNewNode['irt']['port']=int(Port)
                self.IRTNodesList.append(TmpNewNode)

        ### 成功处理完每一行后，需要对行号进行记忆，避免重复处理，对于无效的行号在之前也进行了记忆 ###
        self.ParsedRowIndexList.append(rowindex)

    #####   处理 "XXXX部署信息"sheet   ###
    def ParseDeploySheet(self):
        self.__PreParse()
        ####定位“部署项”、“内网IP”，“开放端口”,"介质清单" 所在的列位置 ####
        self.SheetObj=self.BookObj.sheet_by_index(self.DeployInfoSheetIndex)
        TmpMatchedColNamesCounter=0
        for index in range(self.SheetObj.ncols):
            if u'部署项'==self.SheetObj.cell_value(0,index):
                self.TmpServiceNamesIndex=index
                TmpMatchedColNamesCounter+=1
            elif u'内网IP'==self.SheetObj.cell_value(0,index):
                self.TmpIntranetIPIndex=index
                TmpMatchedColNamesCounter+=1
            elif u'开放端口'==self.SheetObj.cell_value(0,index):
                self.TmpPortIndex=index
                TmpMatchedColNamesCounter+=1
            elif u'介质清单'==self.SheetObj.cell_value(0,index):
                self.TmpMediaIndex=index
                TmpMatchedColNamesCounter+=1
        if TmpMatchedColNamesCounter<4:
            raise Exception("XXXX部署信息sheet信息不全")

        MergedCellsList=self.SheetObj.merged_cells
        MergedCellsList=list(filter(lambda x:x[2]==self.TmpServiceNamesIndex,MergedCellsList))  ##筛选"部署项"这列被聚合的单元格 ###

        ###  step one:处理聚合的单元格包含的行号  ####
        for mergedinfo in MergedCellsList:
            lowrow,highrow=mergedinfo[0],mergedinfo[1]
            MergedCellsServiceName=''
            for rowindex in range(lowrow,highrow):
                if self.SheetObj.cell_value(rowindex,self.TmpServiceNamesIndex):MergedCellsServiceName=self.SheetObj.cell_value(rowindex,self.TmpServiceNamesIndex)
                if not MergedCellsServiceName:
                    self.InvalidRowIndexList.append(rowindex)
                    continue
                self.__ParseDeploySheetRow(rowindex,servicename=MergedCellsServiceName)

        ###  step two:  处理非聚合单元格所在的行号  ###
        for rowindex in range(self.SheetObj.nrows):
            if (rowindex in self.ParsedRowIndexList) or (rowindex in self.InvalidRowIndexList):
                continue
            self.__ParseDeploySheetRow(rowindex)




    ####  以下是处理"数据库信息" sheet 的部分    ######
    def ParseDBSheetRow(self,rowindex):
        TmpSoftwareName=self.SheetObj.cell_value(rowindex,self.TmpSoftwareNameIndex)
        TmpApplicationName=self.SheetObj.cell_value(rowindex,self.TmpApplicationNameIndex)
        TmpAccountDetail=self.SheetObj.cell_value(rowindex,self.TmpAccountDetailIndex)

        if (not TmpSoftwareName) or (not TmpApplicationName) or (not TmpAccountDetail):
            self.InvalidRowIndexDBList.append(rowindex)
            return 1
        TmpSoftwareName=TmpSoftwareName.lower().strip()
        TmpApplicationName=TmpApplicationName.lower().strip()

        if u'mariadb' in TmpSoftwareName:
            TmpColContent=self.SheetObj.cell_value(rowindex,self.TmpAccountDetailIndex)
            if not TmpColContent:
                self.InvalidRowIndexDBList.append(rowindex)
                return 1

            ReObj4ip=search(r'db.IP=([\S]+)\n{,1}',TmpColContent,flags=UNICODE|MULTILINE|IGNORECASE)
            ReObj4port=search(r'db.port=([\S]+)\n{,1}',TmpColContent,flags=UNICODE|MULTILINE|IGNORECASE)
            ReObj4database=search(r'db.name=([\S]+)\n{,1}',TmpColContent,flags=UNICODE|MULTILINE|IGNORECASE)
            ReObj4user=search(r'db.User=([\S]+)\n{,1}',TmpColContent,flags=UNICODE|MULTILINE|IGNORECASE)
            ReObj4password=search(r'db.Password=([\S]+)\n{,1}',TmpColContent,flags=UNICODE|MULTILINE|IGNORECASE)
     
            if (not ReObj4ip) or (not ReObj4port)  or (not ReObj4database) or (not ReObj4user) or (not ReObj4password):
                self.InvalidRowIndexDBList.append(rowindex)
                return 1
            
            ip,port,database=ReObj4ip.group(1),ReObj4port.group(1),ReObj4database.group(1)
            user,password=ReObj4user.group(1),ReObj4password.group(1)

            try:
                ip=ip.strip()
                database=database.strip()
                user=user.strip()
                password=password.strip()
                port=port.strip()
            except:
                pass
            
            if (not isIPValid(ip)) or (not isPortNumValid(port)) or (len(database)==0)  or (len(user)==0) or (len(password)==0):
                self.InvalidRowIndexDBList.append(rowindex)
                return 1

            TmpApplicationName=self.SheetObj.cell_value(rowindex,self.TmpApplicationNameIndex)
            TmpApplicationName=TmpApplicationName.lower().strip()  #### 转化成小写字母，最大限度支持模糊匹配  ###
            if TmpApplicationName==u'采编平台':
                tmpflag=False   ##这个flag 标记"数据库信息"sheet 是否与"XXXX部署信息"sheet中的信息一致  ###
                for mysqlnode in self.MysqlNodesList:
                    if (ip==mysqlnode['mysql']['host']) and (int(port)==int(mysqlnode['mysql']['port'])):
                        tmpflag=True
                        break

                if not tmpflag:
                    self.InvalidRowIndexDBList.append(rowindex)
                    return 1
                TmpNewCode=deepcopy(nodeinfo.iipDBInfo)
                TmpNewCode['iipdb']['host'],TmpNewCode['iipdb']['port']=ip,port
                TmpNewCode['iipdb']['database']=database
                TmpNewCode['iipdb']['user'],TmpNewCode['iipdb']['password']=user,password
                self.IIPDBList.append(TmpNewCode)
            elif u'问政互动政务' in TmpApplicationName:
                tmpflag=False   ##这个flag 标记"数据库信息"sheet 是否与"XXXX部署信息"sheet中的信息一致  ###
                for mysqlnode in self.MysqlNodesList:
                    if (ip==mysqlnode['mysql']['host']) and (int(port)==int(mysqlnode['mysql']['port'])):
                        tmpflag=True
                        break

                if not tmpflag:
                    self.InvalidRowIndexDBList.append(rowindex)
                    return 1
                TmpNewCode=deepcopy(nodeinfo.igiDBInfo)
                TmpNewCode['igidb']['host'],TmpNewCode['igidb']['port']=ip,port
                TmpNewCode['igidb']['database']=database
                TmpNewCode['igidb']['user'],TmpNewCode['igidb']['password']=user,password
                self.IGIDBList.append(TmpNewCode)
            elif TmpApplicationName==u'智能检索':
                tmpflag=False   ##这个flag 标记"数据库信息"sheet 是否与"XXXX部署信息"sheet中的信息一致  ###
                for mysqlnode in self.MysqlNodesList:
                    if (ip==mysqlnode['mysql']['host']) and (int(port)==int(mysqlnode['mysql']['port'])):
                        tmpflag=True
                        break

                if not tmpflag:
                    self.InvalidRowIndexDBList.append(rowindex)
                    return 1
                TmpNewCode=deepcopy(nodeinfo.igsDBInfo)
                TmpNewCode['igsdb']['host'],TmpNewCode['igsdb']['port']=ip,port
                TmpNewCode['igsdb']['database']=database
                TmpNewCode['igsdb']['user'],TmpNewCode['igsdb']['password']=user,password
                self.IGSDBList.append(TmpNewCode)
            elif TmpApplicationName==u'绩效考核':
                tmpflag=False   ##这个flag 标记"数据库信息"sheet 是否与"XXXX部署信息"sheet中的信息一致  ###
                for mysqlnode in self.MysqlNodesList:
                    if (ip==mysqlnode['mysql']['host']) and (int(port)==int(mysqlnode['mysql']['port'])):
                        tmpflag=True
                        break

                if not tmpflag:
                    self.InvalidRowIndexDBList.append(rowindex)
                    return 1
                TmpNewCode=deepcopy(nodeinfo.ipmDBInfo)
                TmpNewCode['ipmdb']['host'],TmpNewCode['ipmdb']['port']=ip,port
                TmpNewCode['ipmdb']['database']=database
                TmpNewCode['ipmdb']['user'],TmpNewCode['ipmdb']['password']=user,password
                self.IPMDBList.append(TmpNewCode)
            elif TmpApplicationName==u'统计报表':
                tmpflag=False   ##这个flag 标记"数据库信息"sheet 是否与"XXXX部署信息"sheet中的信息一致  ###
                for mysqlnode in self.MysqlNodesList:
                    if (ip==mysqlnode['mysql']['host']) and (int(port)==int(mysqlnode['mysql']['port'])):
                        tmpflag=True
                        break

                if not tmpflag:
                    self.InvalidRowIndexDBList.append(rowindex)
                    return 1
                TmpNewCode=deepcopy(nodeinfo.irtDBInfo)
                TmpNewCode['irtdb']['host'],TmpNewCode['irtdb']['port']=ip,port
                TmpNewCode['irtdb']['database']=database
                TmpNewCode['irtdb']['user'],TmpNewCode['irtdb']['password']=user,password
                self.IRTDBList.append(TmpNewCode)
            elif TmpApplicationName==u'运营中心':
                tmpflag=False   ##这个flag 标记"数据库信息"sheet 是否与"XXXX部署信息"sheet中的信息一致  ###
                for mysqlnode in self.MysqlNodesList:
                    if (ip==mysqlnode['mysql']['host']) and (int(port)==int(mysqlnode['mysql']['port'])):
                        tmpflag=True
                        break

                if not tmpflag:
                    self.InvalidRowIndexDBList.append(rowindex)
                    return 1
                TmpNewCode=deepcopy(nodeinfo.idoDBInfo)
                TmpNewCode['idodb']['host'],TmpNewCode['idodb']['port']=ip,port
                TmpNewCode['idodb']['database']=database
                TmpNewCode['idodb']['user'],TmpNewCode['idodb']['password']=user,password
                self.IDODBList.append(TmpNewCode)
            elif u'ids' in TmpApplicationName:
                tmpflag=False   ##这个flag 标记"数据库信息"sheet 是否与"XXXX部署信息"sheet中的信息一致  ###
                for mysqlnode in self.MysqlNodesList:
                    if (ip==mysqlnode['mysql']['host']) and (int(port)==int(mysqlnode['mysql']['port'])):
                        tmpflag=True
                        break

                if not tmpflag:
                    self.InvalidRowIndexDBList.append(rowindex)
                    return 1
                TmpNewCode=deepcopy(nodeinfo.idsDBInfo)
                TmpNewCode['idsdb']['host'],TmpNewCode['idsdb']['port']=ip,port
                TmpNewCode['idsdb']['database']=database
                TmpNewCode['idsdb']['user'],TmpNewCode['idsdb']['password']=user,password
                self.IDSDBList.append(TmpNewCode)
            elif u'wechat' in TmpApplicationName:
                tmpflag=False   ##这个flag 标记"数据库信息"sheet 是否与"XXXX部署信息"sheet中的信息一致  ###
                for mysqlnode in self.MysqlNodesList:
                    if (ip==mysqlnode['mysql']['host']) and (int(port)==int(mysqlnode['mysql']['port'])):
                        tmpflag=True
                        break

                if not tmpflag:
                    self.InvalidRowIndexDBList.append(rowindex)
                    return 1
                TmpNewCode=deepcopy(nodeinfo.wechatDBInfo)
                TmpNewCode['wechatdb']['host'],TmpNewCode['wechatdb']['port']=ip,port
                TmpNewCode['wechatdb']['database']=database
                TmpNewCode['wechatdb']['user'],TmpNewCode['wechatdb']['password']=user,password
                self.WECHATDBList.append(TmpNewCode)
        elif (u'redis' in TmpSoftwareName) or (u'redis' in TmpApplicationName):
            TmpColContent=self.SheetObj.cell_value(rowindex,self.TmpAccountDetailIndex)
            if len(TmpColContent)==0:
                self.InvalidRowIndexDBList.append(rowindex)
                return 1

            ReObj4ip=search(r'IP=([\S]+)\n{,1}',TmpColContent,flags=UNICODE|MULTILINE|IGNORECASE)
            ReObj4port=search(r'port=([\S]+)\n{,1}',TmpColContent,flags=UNICODE|MULTILINE|IGNORECASE)
            ReObj4password=search(r'password=([\S]+\n{,1})',TmpColContent,flags=UNICODE|MULTILINE|IGNORECASE)
            ReObj4database=search(r'db=([\S]+\n{,1})',TmpColContent,flags=UNICODE|MULTILINE|IGNORECASE)

            if (not ReObj4ip) or (not ReObj4port) or (not ReObj4password) or (not ReObj4database):
                self.InvalidRowIndexDBList.append(rowindex)
                return 1
            ip,port=ReObj4ip.group(1),ReObj4port.group(1)
            password,database=ReObj4password.group(1),ReObj4database.group(1)

            try:
                ip=ip.strip()
                password=password.strip()
                database=database.strip()
                port=port.strip()
            except:
                pass

            if (not isIPValid(ip)) or (not isPortNumValid(port)) or (len(password)==0) or (len(database)==0):
                self.InvalidRowIndexDBList.append(rowindex)
                return 1
            tmpflag=False     ##这个flag 标记"数据库信息"sheet 是否与"XXXX部署信息"sheet中的信息一致  ###
            for redisnode in self.RedisNodesList:
                if (ip==redisnode['redis']['host']) and (int(port)==int(redisnode['redis']['port'])):
                    redisnode['redis']['password']=password
                    redisnode['redis']['database']=database
                    tmpflag=True
                    break
            if not tmpflag:
                self.InvalidRowIndexDBList.append(rowindex)
                return 1
        elif (u'rabbitmq' in TmpSoftwareName) or (u'rabbitmq' in TmpApplicationName):
            TmpColContent=self.SheetObj.cell_value(rowindex,self.TmpAccountDetailIndex)
            if len(TmpColContent)==0:
                self.InvalidRowIndexDBList.append(rowindex)
                return 1

            ReObj4ip=search(r'IP=([\S]+\n{,1})',TmpColContent,flags=MULTILINE|UNICODE|IGNORECASE)
            ReObj4port=search(r'port=([\S]+)\n{,1}',TmpColContent,flags=MULTILINE|UNICODE|IGNORECASE)
            ReObj4user=search(r'User=([\S]+)\n{,1}',TmpColContent,flags=MULTILINE|UNICODE|IGNORECASE)
            ReObj4password=search(r'Password=([\S]+)\n{,1}',TmpColContent,flags=MULTILINE|UNICODE|IGNORECASE)

            if (not ReObj4ip) or (not ReObj4port) or (not ReObj4user) or (not ReObj4password):
                self.InvalidRowIndexDBList.append(rowindex)
                return 1

            ip,port=ReObj4ip.group(1),ReObj4port.group(1)
            user,password=ReObj4user.group(1),ReObj4password.group(1)
            try:
                ip=ip.strip()
                user=user.strip()
                password=password.strip()
                port=port.strip()
            except:
                pass

            #### 如果端口填的是"5672、15672",就当成是“5672”  ###
            if u'5672' in port:
                port=5672
            if (not isIPValid(ip)) or (not isPortNumValid(port)) or (len(user)==0) or (len(password)==0):
                self.InvalidRowIndexDBList.append(rowindex)
                return 1

            tmpflag=False
            for rabbitmqnode in self.RabbitmqNodesList:
                if (ip==rabbitmqnode['rabbitmq']['host']) and (int(port)==int(rabbitmqnode['rabbitmq']['port'])):
                    rabbitmqnode['rabbitmq']['user']=user
                    rabbitmqnode['rabbitmq']['password']=password
                    tmpflag=True
                    break
            if not tmpflag:
                self.InvalidRowIndexList.append(rowindex)



    def ParseDBSheet(self):
        self.SheetObj=self.BookObj.sheet_by_index(self.DatabaseInfoSheetIndex)
        ### 定位“软件”、“账号”、“应用”所在的列位置 ####
        TmpMatchedColNamesCounter=0
        for colindex in range(self.SheetObj.ncols):
            if u'软件'==self.SheetObj.cell_value(1,colindex):
                self.TmpSoftwareNameIndex=colindex
                TmpMatchedColNamesCounter+=1
            elif u'应用'==self.SheetObj.cell_value(1,colindex):
                self.TmpApplicationNameIndex=colindex
                TmpMatchedColNamesCounter+=1
            elif u'帐号信息'==self.SheetObj.cell_value(1,colindex):
                self.TmpAccountDetailIndex=colindex
                TmpMatchedColNamesCounter+=1
        if TmpMatchedColNamesCounter<3:
            raise Exception('"数据库信息"sheet 信息不全!')
        for rowindex  in range(self.SheetObj.nrows):
            self.ParseDBSheetRow(rowindex)

    def GetResource(self):
        TmpNodesList=self.NginxNodesList+self.NginxPublishNodesList+self.ElasticsearchNodesList+\
                self.RedisNodesList+self.RabbitmqNodesList+self.MysqlNodesList+\
                self.IDSNodesList+self.MASNodesList+self.CKMNodesList+self.IIPNodesList+\
                self.IGINodesList+self.IGSNodesList+self.IPMNodesList+self.IRTNodesList+\
                self.IIPDBList+self.IGIDBList+self.IGSDBList+self.IPMDBList+self.IRTDBList+\
                self.IDODBList+self.IDSDBList+self.RedisNodesList+self.RabbitmqNodesList
        TmpNodeForWhiteList=deepcopy(nodeinfo.whitelist)

        #### 生成IP 白名单 ####
        TmpIPList=[]
        for DictItem in TmpNodesList:
            for key in DictItem.keys():
                if DictItem[key]['host']:
                   TmpIPList.append(DictItem[key]['host'])
        TmpIPList=list(set(TmpIPList))  ### 去除重复的元素 ###
        TmpNodeForWhiteList['whitelist']['list']=TmpIPList
        TmpNodeForWhiteList['whitelist']['ip']=','.join(TmpNodeForWhiteList['whitelist']['list'])
        TmpNodesList.append(TmpNodeForWhiteList)
        return TmpNodesList


    def Run(self):
        self.ParseDeploySheet()
        self.ParseDBSheet()
        self.Display()


    def Display(self):
            print ('--------------- echo “XXXX部署信息”sheet 提取内容 --------------')
            print (self.NginxNodesList)
            print (self.NginxPublishNodesList)
            print (self.ElasticsearchNodesList)
            print (self.RedisNodesList)
            print (self.RabbitmqNodesList)
            print (self.MysqlNodesList)
            print (self.IDSNodesList)
            print (self.MASNodesList)
            print (self.CKMNodesList)
            print (self.IIPNodesList)
            print (self.IGINodesList)
            print (self.IGSNodesList)
            print (self.IPMNodesList)
            print (self.IRTNodesList)
            print ('--------------  echo “数据库信息”sheet" 提取内容 -------------------------')
            print (self.IIPDBList)
            print (self.IGIDBList)
            print (self.IGSDBList)
            print (self.IPMDBList)
            print (self.IRTDBList)
            print (self.IDODBList)
            print (self.IDSDBList)
            print (self.RedisNodesList)
            print (self.RabbitmqNodesList)
            print ('----------------   输出完毕  ---------')



if __name__=="__main__":
    tmpObj=ParseExcel(u'江门市政府 - 海云V8.0标准版部署信息表_1.1.xls')
    tmpObj.Run()
    tmpObj.GetResource()

