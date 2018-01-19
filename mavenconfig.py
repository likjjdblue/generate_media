# -*- coding: utf-8 -*-
'''
说明：
A、filtertype 对应maven 工程下"filters/"的目录结构；
   1、表示以文件个体的形式存放；2、表示以文件目录的形式存放
B、filterfiles: 模板文件的相对路径
'''

iipconfig={
    'filtertype':2,
    'filterfiles':[
        'application.properties',
        'ckm.properties',
        'db.properties',
        'elasticsearch.properties',
        'kpi.properties',
        'mas.properties',
        'mq.properties',
        'st.properties',
        'trsids-agent.properties',
        'TRSWCMApp.ini',
        'TRSWCMPhoto.properties',
        'weixin.properties',
        'wm.properties',
        'zabbix.properties',
        'cache/redis.properties',
    ],
    'path':'IIP/source/',
}

igsconfig={
    'filtertype':2,
    'filterfiles':[
        'application.properties',
        'trsids-agent.properties',
    ],
    'path':'IGS/source/',
}

ipmconfig={
    'filtertype':1,
    'filterfiles':[
        'dev.properties'
    ],
    'path':'IPM/source/',
}

irtconfig={
    'filtertype':1,
    'filterfiles':[
        'dev.properties'
    ],
    'path':'IRT/source/',
}


igiconfig={
    'filtertype':2,
    'fiterfiles':[
        'application.properties'
    ],
    'path':'/IGI/source/',
}

