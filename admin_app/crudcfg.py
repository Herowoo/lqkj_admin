from django.shortcuts import render,redirect,HttpResponse
from django.db import connection, transaction
from django.forms.models import model_to_dict
import json
from admin_app import public
from admin_app import models
import datetime

#获取数据库中的所有表名
def GetTableList(request):
    log = public.logger
    log.info('----------------------Admin-GetTable-begin---------------------------')

    #获取所有的表名：
    try:
        cur=connection.cursor()

        sql='select table_name,table_comment from information_schema.tables where table_schema <> "information_schema" order by table_name asc'
        cur.execute(sql)
        rows = cur.fetchall()
        tableinfo_json=[]
        for item in rows:
            tableitem={}
            tableitem["value"] = item[0]
            tableitem["lable"] = item[0]+'  '+item[1]
            tableinfo_json.append(tableitem)
        cur.close()
    except :
        log.warning("系统异常", exc_info = True)
        cur.close()
        s = public.setrespinfo({"respcode": "100002", "respmsg": "系统异常"})
        return HttpResponse(s)

    s = json.dumps(tableinfo_json, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Admin-GetTable-end---------------------------')
    return HttpResponse(s)

#获取表结构体--使用crud的json报文格式，方便前端上送数据
def GetTableInfo(request):
    log = public.logger
    log.info('----------------------Admin-GetTableField-begin---------------------------')

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)

    appid=reqest_body.get('APP_ID',None)
    # print(appid)
    if appid:
        #如果有上送APP_ID，则是修改配置，以APP_ID为准.
        log.info('有上送APP_ID，则是修改配置，以APP_ID为准.')
        return GetCrud(request)

    tablename = reqest_body['tablename'].upper()
    if tablename == None or tablename=='':
        s = public.setrespinfo({"respcode": "300001", "respmsg": "请输入表名"})
        return HttpResponse(s)

    #获取表信息：
    try:
        cur=connection.cursor()
        sql="SELECT column_name, column_comment, data_type, is_nullable,  " \
            "column_key, column_default, character_maximum_length,  numeric_precision, " \
            "extra "
        sql = sql+"FROM information_schema.columns WHERE UPPER(table_name) = UPPER(%s)"
        log.info(sql % tablename)
        cur.execute(sql, tablename)
        rows = cur.fetchall()
        tableinfo_json={"respcode": "000000",
                        "respmsg": "交易成功", "trantype": "addcrud", "tranreg":{}, "tranlist":[]}

        #appid='ap'+datetime.datetime.now().strftime('%Y%m%d')
        appid="" #改为数据库自动生成
        tableinfo_json["tranreg"]["APP_ID"] = appid
        tableinfo_json["tranreg"]["TRAN_ID"] = ""
        tableinfo_json["tranreg"]["TRAN_DESC"] = "请输入交易描述"
        tableinfo_json["tranreg"]["WHERE_CTRL"] = ""
        tableinfo_json["tranreg"]["ORDER_CTRL"] = ""
        tableinfo_json["tranreg"]["TABLE_NAME"] = tablename
        tableinfo_json["tranreg"]["DATA_SOURCE"] = ""
        tableinfo_json["tranreg"]["MAIN_CONTROL"] = ""
        tableinfo_json["tranreg"]["SELECT_ABLE"] = True
        tableinfo_json["tranreg"]["INSERT_ABLE"] = False
        tableinfo_json["tranreg"]["UPDATE_ABLE"] = False
        tableinfo_json["tranreg"]["DELETE_ABLE"] = False
        tableinfo_json["tranreg"]["EXPORT_ABLE"] = False
        tableinfo_json["tranreg"]["PLUGINS"] = ""
        tableinfo_json["tranreg"]["SNOTE"] = "SNOTE"

        loopid=0
        for item in rows:
            tableitem={}
            loopid=loopid+1
            tableitem["APP_ID"] = appid
            tableitem["TRAN_ID"] = ""
            tableitem["FIELD_ID"]=item[0]
            tableitem["FIELD_NAME"] = item[1]
            tableitem["STATE"] = True
            tableitem["DATA_TYPE"] = item[2]
            tableitem["UI_TYPE"] = "text" #先默认是文本
            if item[3]=="YES" or item[3]=="yes":
                tableitem["ALLOW_BLANK"] = True
            else:
                tableitem["ALLOW_BLANK"] = False
            if item[4]=="PRI" :
                tableitem["IS_KEY"] = True
            else:
                tableitem["IS_KEY"] = False
            tableitem["SEARCH_TYPE"] = ""
            tableitem["SEARCH_EXTS"] = ""
            tableitem["EDIT_ABLE"] = False
            tableitem["DEF_VALUE"] = item[5]
            tableitem["ORDER_ID"] = str(loopid)
            tableitem["SNOTE"] = ""

            if item[6] and len( str(item[6]) )>0:
                maxlength= item[6]
            else:
                maxlength = item[7]
            if maxlength == None or maxlength=='':
                if tableitem["DATA_TYPE"] in ['date','DATE']:
                    maxlength = 10
                    tableitem["UI_TYPE"] = 'date'
                elif tableitem["DATA_TYPE"] in ['time','TIME']:
                    maxlength = 8
                    tableitem["UI_TYPE"] = 'time'
                elif tableitem["DATA_TYPE"] in ['datetime', 'DATETIME']:
                    maxlength = 19
                    tableitem["UI_TYPE"] = 'datetime'
                elif tableitem["DATA_TYPE"] in ['timestamp', 'TIMESTAMP']:
                    maxlength = 23
                    tableitem["UI_TYPE"] = 'datetime'
                else:
                    maxlength =23

            showlength=None
            if item[8]=='auto_increment': #自增变量
                tableitem["UI_TYPE"] = 'auto_increment'
                showlength = 4

            #显示长度初始值
            if showlength == 0 or showlength==None:
                showlength= len(tableitem["FIELD_NAME"])
            if showlength==0:
                showlength = 8
            #print('maxlength=',maxlength)
            maxlength=int(maxlength)
            if maxlength > 30:
                tableitem["FIELD_LENGTH"] = 30
            elif maxlength < 4:
                tableitem["FIELD_LENGTH"] = 4
            else:
                tableitem["FIELD_LENGTH"] = showlength
            tableitem["MAX_LENGTH"] = maxlength

            tableinfo_json["tranlist"].append(tableitem)
        cur.close()
    except :
        log.warning("系统异常", exc_info = True)
        cur.close()
        s = public.setrespinfo({"respcode": "100003", "respmsg": "系统异常"})
        return HttpResponse(s)

    s = json.dumps(tableinfo_json, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-GetTableField-end---------------------------')
    return HttpResponse(s)

#增加增删改查配置
def AddCrud(request):
    log = public.logger
    log.info('----------------------Admin-AddCrud-begin---------------------------')

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    log.info(reqest_body)

    #使用models插入数据库,增删改查配置注册表
    Req_TranReg = reqest_body['tranreg']
    #print(Req_TranReg)
    if Req_TranReg.get('APP_ID',None):
        tranreg = models.IrsadminDbTranReg(
            app_id=Req_TranReg.get('APP_ID',None), #为空时自增，自动生成
            tran_id=Req_TranReg['TRAN_ID'],
            tran_desc=Req_TranReg['TRAN_DESC'],
            where_ctrl = Req_TranReg['WHERE_CTRL'],
            order_ctrl = Req_TranReg['ORDER_CTRL'],
            group_ctrl = Req_TranReg.get('GROUP_CTRL',""),
            table_name = Req_TranReg['TABLE_NAME'],
            data_source = Req_TranReg['DATA_SOURCE'],
            main_control = Req_TranReg['MAIN_CONTROL'],
            select_able = public.True2y(Req_TranReg['SELECT_ABLE']),
            insert_able = public.True2y(Req_TranReg['INSERT_ABLE']),
            update_able = public.True2y(Req_TranReg['UPDATE_ABLE']),
            delete_able = public.True2y(Req_TranReg['DELETE_ABLE']),
            export_able=public.True2y(Req_TranReg.get('EXPORT_ABLE',True)),
            plugins = Req_TranReg['PLUGINS'],
            snote = Req_TranReg['SNOTE'],
            create_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    else:
        tranreg = models.IrsadminDbTranReg(
            tran_id=Req_TranReg['TRAN_ID'],
            tran_desc=Req_TranReg['TRAN_DESC'],
            where_ctrl=Req_TranReg['WHERE_CTRL'],
            order_ctrl=Req_TranReg['ORDER_CTRL'],
            group_ctrl=Req_TranReg.get('GROUP_CTRL', ""),
            table_name=Req_TranReg['TABLE_NAME'],
            data_source=Req_TranReg['DATA_SOURCE'],
            main_control=Req_TranReg['MAIN_CONTROL'],
            select_able=public.True2y(Req_TranReg['SELECT_ABLE']),
            insert_able=public.True2y(Req_TranReg['INSERT_ABLE']),
            update_able=public.True2y(Req_TranReg['UPDATE_ABLE']),
            delete_able=public.True2y(Req_TranReg['DELETE_ABLE']),
            export_able=public.True2y(Req_TranReg.get('EXPORT_ABLE', True)),
            plugins=Req_TranReg['PLUGINS'],
            snote=Req_TranReg['SNOTE'],
            create_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    tranreg.save()
    log.info('登记IrsadminDbTranReg成功')
    # 使用models插入数据库,增删改查配置明细表
    Req_TranList = reqest_body['tranlist']

    KeyFlag=False  #是否有主键，具有修改和删除功能时必须上送主键
    for TranList in Req_TranList:
        #print( TranList['DATA_TYPE'] )
        if public.True2y(TranList['IS_KEY'])=='Y':
            KeyFlag=True
        if public.True2y(TranList['IS_KEY']) == 'Y' and public.True2y(TranList['ALLOW_BLANK']) == 'Y':
            # tranlist = models.IrsadminDbTranList.objects.filter(app_id=tranreg.app_id)
            # tranlist.delete()
            # tranreg.delete()
            s = public.setrespinfo({"respcode": "3000003", "respmsg": "主键不允许修改"})
            return HttpResponse(s)
        if TranList['MAX_LENGTH'] == None or TranList['MAX_LENGTH'] == 0:
            # tranlist = models.IrsadminDbTranList.objects.filter(app_id=tranreg.app_id)
            # tranlist.delete()
            # tranreg.delete()
            s = public.setrespinfo({"respcode": "3000003", "respmsg": "最大长度不可为空"})
            return HttpResponse(s)

        if TranList.get('ID',None):
            tranlist = models.IrsadminDbTranList(
                id=TranList.get('ID',None),
                app_id=tranreg.app_id,
                tran_id=TranList['TRAN_ID'],
                field_id=TranList['FIELD_ID'],
                field_name=TranList['FIELD_NAME'],
                state=public.True2y(TranList['STATE']),
                data_type=TranList['DATA_TYPE'],
                field_length=TranList['FIELD_LENGTH'],
                max_length=TranList['MAX_LENGTH'],
                ui_type=TranList['UI_TYPE'],
                allow_blank=public.True2y(TranList['ALLOW_BLANK']),
                is_key=public.True2y(TranList['IS_KEY']),
                search_type=TranList['SEARCH_TYPE'],
                search_exts=TranList['SEARCH_EXTS'],
                edit_able=public.True2y(TranList['EDIT_ABLE']),
                def_value=TranList['DEF_VALUE'],
                order_id=TranList['ORDER_ID'],
                snote=TranList['SNOTE']
            )
        else:
            tranlist = models.IrsadminDbTranList(
                app_id=tranreg.app_id,
                tran_id=TranList['TRAN_ID'],
                field_id=TranList['FIELD_ID'],
                field_name=TranList['FIELD_NAME'],
                state=public.True2y(TranList['STATE']),
                data_type=TranList['DATA_TYPE'],
                field_length=TranList['FIELD_LENGTH'],
                max_length=TranList['MAX_LENGTH'],
                ui_type=TranList['UI_TYPE'],
                allow_blank=public.True2y(TranList['ALLOW_BLANK']),
                is_key=public.True2y(TranList['IS_KEY']),
                search_type=TranList['SEARCH_TYPE'],
                search_exts=TranList['SEARCH_EXTS'],
                edit_able=public.True2y(TranList['EDIT_ABLE']),
                def_value=TranList['DEF_VALUE'],
                order_id=TranList['ORDER_ID'],
                snote=TranList['SNOTE']
            )
        tranlist.save()
        log.info('登记IrsadminDbTranList成功')

    if KeyFlag==False:
        if public.True2y(Req_TranReg['UPDATE_ABLE'])=='Y' or public.True2y(Req_TranReg['DELETE_ABLE'])=='Y':
            # tranlist=models.IrsadminDbTranList.objects.filter(app_id=tranreg.app_id)
            # tranreg.delete()
            s = public.setrespinfo({"respcode": "3000002", "respmsg": "具有修改和删除功能时必须上送主键"})
            return HttpResponse(s)

    resp={"respcode":"000000", "respmsg":"交易成功", "APP_ID":tranreg.app_id}
    s = json.dumps(resp, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-AddCrud-end---------------------------')
    return HttpResponse(s)


#获取增删改查配置
def GetCrud(request):
    log = public.logger
    log.info('----------------------Admin-GetCrud-begin---------------------------')

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    log.info(reqest_body)

    appid = reqest_body['APP_ID'].upper()

    try:
        tranreg = models.IrsadminDbTranReg.objects.get( app_id=appid)
    except models.IrsadminDbTranReg.DoesNotExist:
        tranreg = None
        s = public.setrespinfo({"respcode": "300020", "respmsg": "应用配置不存在"})
        return HttpResponse(s)

    try:
        TranList = models.IrsadminDbTranList.objects.filter( app_id=appid).order_by('order_id')
    except models.IrsadminDbTranList.DoesNotExist:
        TranList = None
        s = public.setrespinfo({"respcode": "300021", "respmsg": "应用配置明细项不存在"})
        return HttpResponse(s)

    tableinfo_json = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": "getcrud",
        "tranreg": {},
        "tranlist": []
    }

    #配置明细信息赋值
    for listitem in TranList:
        listitem=model_to_dict(listitem)
        listinfo = {}
        for item in listitem:
            mkey=str(item).upper()
            if type(listitem[item])=='datetime':
                mvalue=listitem[item]
            else:
                mvalue = listitem[item]

            if mkey in ['STATE','ALLOW_BLANK','IS_KEY','EDIT_ABLE']:
                if mvalue=='Y' or mvalue=='y':
                    listinfo[mkey] = True
                else:
                    listinfo[mkey] = False
            else:
                listinfo[mkey] = mvalue
        tableinfo_json['tranlist'].append(listinfo)

    # 配置注册信息赋值
    # print('tranreg:',type(tranreg),tranreg)
    regitem = model_to_dict(tranreg)
    reginfo = {}
    for item in regitem:
        mkey = str(item).upper()
        # print('mkey=',mkey,'---type(listitem[item])=',type(regitem[item]))
        mvalue = regitem[item]

        if mkey in ['SELECT_ABLE', 'INSERT_ABLE', 'UPDATE_ABLE', 'DELETE_ABLE', 'EXPORT_ABLE']:
            if mvalue == 'Y' or mvalue == 'y':
                reginfo[mkey] = True
            else:
                reginfo[mkey] = False
        else:
            reginfo[mkey] = mvalue
    tableinfo_json['tranreg']=reginfo

    s = json.dumps(tableinfo_json, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-GetCrud-end---------------------------')
    return HttpResponse(s)

