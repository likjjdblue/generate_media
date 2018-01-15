def ReflateDictKey(keystring,TmpDict):
    '''
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


TmpDict={
    'foo':{
        "bar":{
            "name":['db']
        }
    }
}



print (type(ReflateDictKey('foo.bar.name',TmpDict)))