from django.shortcuts import render,redirect,HttpResponse
from django.db import connection, transaction
import json
from admin_app import public
from admin_app import models
from admin_app import texcfg
from admin_app import userrole


#获取表头字段
def selectTableHead(request):
    log = public.logger
    log.info('----------------------Admin-selectTableHead-begin---------------------------')

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    log.info(reqest_body)
    menuid=reqest_body.get('MENU_ID',None)
    if menuid == None:
        s = public.setrespinfo({"respcode": "310001", "respmsg": "菜单编号必输!"})
        return HttpResponse(s)
    try:
        MenuTable = models.IrsadminMenu.objects.get(menu_id=menuid)
    except models.IrsadminMenu.DoesNotExist:
        MenuTable = None
        s = public.setrespinfo({"respcode": "310002", "respmsg": "菜单编号不存在!"})
        return HttpResponse(s)
    try:
        TranRegTable=models.IrsadminDbTranReg.objects.get(app_id=MenuTable.app_id)
    except models.IrsadminDbTranReg.DoesNotExist:
        TranRegTable = None
        s = public.setrespinfo({"respcode": "310003", "respmsg": "应用编号不存在!"})
        return HttpResponse(s)

    #校验权限
    flag=userrole.checkauth(request.session.get('user_id', None), MenuTable.menu_id)
    if flag==False:
        s = public.setrespinfo({"respcode": "349921", "respmsg": "用户权限不正确!"})
        return HttpResponse(s)

    cur = connection.cursor()
    sql = "select FIELD_ID, FIELD_NAME, FIELD_LENGTH, SEARCH_TYPE, " \
          " UI_TYPE,MAX_LENGTH, EDIT_ABLE, ALLOW_BLANK, IS_KEY, DATA_TYPE, DEF_VALUE " \
          " from IRSADMIN_DB_TRAN_LIST where STATE='Y' and APP_ID=%s order by ORDER_ID asc"
    log.info(sql % MenuTable.app_id)
    cur.execute(sql, MenuTable.app_id)
    rows = cur.fetchall()

    data={
           "respcode": "000000",
           "respmsg": "交易成功",
           "trantype": "selecttablehead",
           "tableHead":[],
           "ButtonInfo":[],
           "searchinfo": [{
               "SearchInfo": {
               "selectoptions": [],
                   "selecttypes":[],
                   "selectoption":{
                       "label":'',
                       "value":'',
                       "uitype":''
                   },
                       "selecttype": "",
                       "selectvalue": "",
               }
           }],
           "tableAble":{
               "INSERT_ABLE": public.Y2True(TranRegTable.insert_able),
               "UPDATE_ABLE": public.Y2True(TranRegTable.update_able),
               "DELETE_ABLE": public.Y2True(TranRegTable.delete_able),
               "SELECT_ABLE": public.Y2True(TranRegTable.select_able),
               "EXPORT_ABLE": public.Y2True(TranRegTable.export_able),
           }
       }

    data['searchinfo'][0]['SearchInfo']['selecttypes'] =public.selecttypes
    tableHead=[]
    selectoptions=[]
    for item in rows:
        # print(item)
        tableitem = {}
        tableitem["label"] = item[1]
        tableitem["property"] = item[0]

        #页面显示的列宽度width
        fieldlength=item[2]
        # print(type(fieldlength), fieldlength)
        if fieldlength == None or not fieldlength:
            fieldlength=len(item[1])

        fieldlength=int(fieldlength)
        if fieldlength>30:
            tableitem["width"] = 30*14
        elif fieldlength <= len(item[1]):
            tableitem["width"] = len(item[1]) * 14
        else:
            tableitem["width"] = fieldlength * 14

        tableitem["width"] = fieldlength * 14
        tableitem["uitype"] = item[4]
        tableitem["MAX_LENGTH"] = item[5]

        if item[6]=='Y' or item[6]=='y':
            tableitem["EDIT_ABLE"] = True
        else:
            tableitem["EDIT_ABLE"] = False

        #是否为空属性
        if item[7]=='Y' or item[7]=='y':
            tableitem["ALLOW_BLANK"] = True
        else:
            tableitem["ALLOW_BLANK"] = False
        #主键不允许为空
        if item[8] == 'Y' or item[8] == 'y':
            tableitem["ALLOW_BLANK"] = False

        #数据类型
        tableitem["DATA_TYPE"] = item[9]

        tableitem["DEF_VALUE"] = item[10]  #默认值

        tableHead.append(tableitem)

        #查询条件配置
        if item[3] == None or item[3]=="":
            pass
        else:
            searchitem={}
            searchitem["label"] = item[1]
            searchitem["value"] = item[0]
            searchitem["uitype"] = item[4]
            selectoptions.append(searchitem)

    #特殊处理，新增UITYPE='transfer'穿梭框,用于有些表的联表操作
    if str(menuid) == '6':
        #角色授权管理
        tableitem = {}
        tableitem["label"] = '角色权限配置'
        tableitem["property"] = 'ROLE_TRANSFER'
        tableitem["width"] = 120
        tableitem["uitype"] = 'transfer'
        tableitem["MAX_LENGTH"] = 254
        tableitem["EDIT_ABLE"] = True
        tableitem["ALLOW_BLANK"] = True
        tableitem["DATA_TYPE"]='VARCHAR'
        tableHead.append(tableitem)
    elif str(menuid) == '2':
        #用户角色管理
        tableitem = {}
        tableitem["label"] = '用户角色配置'
        tableitem["property"] = 'USER_TRANSFER'
        tableitem["width"] = 120
        tableitem["uitype"] = 'transfer'
        tableitem["MAX_LENGTH"] = 254
        tableitem["EDIT_ABLE"] = True
        tableitem["ALLOW_BLANK"] = True
        tableitem["DATA_TYPE"]='VARCHAR'
        tableHead.append(tableitem)

    data['tableHead']=tableHead
    if selectoptions.__len__()>0:
        data['searchinfo'][0]['SearchInfo']['selectoptions'] = selectoptions
    else:
        #没有查询条件
        data.pop('searchinfo')

    #设置用户编辑权限
    data['tableAble']['INSERT_ABLE'] = False
    data['tableAble']['UPDATE_ABLE'] = False
    data['tableAble']['DELETE_ABLE'] = False
    data['tableAble']['EXPORT_ABLE'] = False

    # 角色数据编辑导出权限控制
    sql = "select b.insert_able,d.insert_able,b.update_able,d.update_able,b.delete_able,d.delete_able,b.export_able,d.export_able " \
          "from irsadmin_user_rule a, irsadmin_role_duecfg b, irsadmin_menu c, irsadmin_db_tran_reg d  " \
          "where a.role_id=b.role_id and b.menu_id=c.menu_id and c.app_id=d.app_id and c.menu_id='%s' and user_id='%s' " \
          % (menuid, request.session.get('user_id', None))
    log.info("查询角色数据编辑导出权限控制："+sql)
    cur.execute(sql)
    rows = cur.fetchall()

    for item in rows:
        if data['tableAble']['INSERT_ABLE'] == True:
            pass
        else:
            if item[0] == 'Y' and item[1] == 'Y':
                data['tableAble']['INSERT_ABLE'] = True
            else:
                data['tableAble']['INSERT_ABLE'] = False

        if data['tableAble']['UPDATE_ABLE'] == True:
            pass
        else:
            if item[2] == 'Y' and item[3] == 'Y':
                data['tableAble']['UPDATE_ABLE'] = True
            else:
                data['tableAble']['UPDATE_ABLE'] = False

        if data['tableAble']['DELETE_ABLE'] == True:
            pass
        else:
            if item[4] == 'Y' and item[5] == 'Y':
                data['tableAble']['DELETE_ABLE'] = True
            else:
                data['tableAble']['DELETE_ABLE'] = False

        if data['tableAble']['EXPORT_ABLE'] == True:
            pass
        else:
            if item[6] == 'Y' and item[7] == 'Y':
                data['tableAble']['EXPORT_ABLE'] = True
            else:
                data['tableAble']['EXPORT_ABLE'] = False

    cur.close()

    if len(TranRegTable.tran_id) > 0 and str(TranRegTable.tran_id)!='0':
        log.info('获取按钮配置信息')
        #获取按钮配置信息
        try:
            ButtonCfg=models.IrsadminTranCfg.objects.filter(id__in= str(TranRegTable.tran_id).split(','))
        except models.IrsadminTranCfg.DoesNotExist:
            ButtonCfg = None
        if ButtonCfg:
            buttonlength=30
            for item in ButtonCfg:
                buttonitem={}
                buttonitem['BUTTON_NAME']=item.button_name
                buttonitem['BUTTON_COLOR'] = item.button_color
                buttonitem['BUTTON_TYPE'] = item.button_type
                buttonitem['BUTTON_TRANTYPE'] = item.button_trantype
                data['ButtonInfo'].append(buttonitem)
                buttonlength=buttonlength+30+item.button_length
            data['ButtonLength']=buttonlength

    s = json.dumps(data, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info('----------------------Admin-selectTableHead-end---------------------------')
    return HttpResponse(s)

#获取表数据
def selectTableData(request):
    log = public.logger
    log.info('----------------------Admin-selectTableData-begin---------------------------')
    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    log.info(reqest_body)
    # log.info(reqest_body.get('MENU_ID',"5"))
    menuTable=models.IrsadminMenu.objects.get(menu_id=reqest_body.get('MENU_ID',""))
    TranRegTable=models.IrsadminDbTranReg.objects.get(app_id=menuTable.app_id)

    #校验权限
    flag=userrole.checkauth(request.session.get('user_id', None), menuTable.menu_id)
    if flag==False:
        s = public.setrespinfo({"respcode": "349921", "respmsg": "用户权限不正确!"})
        return HttpResponse(s)

    pagesize = int(reqest_body.get('pagesize', "10"))
    pagenum = int(reqest_body.get('pagenum', "1"))

    searchinfo=reqest_body.get('searchinfo',None)
    whereinfo=""
    #print(type(searchinfo), searchinfo)
    if searchinfo:
        #有查询条件
        for item in searchinfo:
            selectid=item.get('selectid', None)
            selecttype=item.get('selecttype', None)
            selectvalue = item.get('selectvalue', None)

            if selectid==None or selectid=="":
                continue
            if selecttype==None or selecttype=="":
                continue

            # if item['uitype'] == 'datetime' and selectvalue:
            #     selectvalue = datetime.datetime.strptime(selectvalue, "%Y-%m-%d %H:%M:%S")
            if selecttype == 'like' and selectvalue:
                selectvalue="%"+selectvalue+"%"
            wheretemp=" and "+selectid+" "+selecttype+" '"+selectvalue+"'"
            #print(wheretemp)
            if whereinfo == "":
                whereinfo = wheretemp
            else:
                whereinfo = whereinfo+' '+wheretemp

    if TranRegTable.where_ctrl==None:
        TranRegTable.where_ctrl=""
    if TranRegTable.order_ctrl==None:
        TranRegTable.order_ctrl=""

    cur = connection.cursor()
    sql = "select FIELD_ID,UI_TYPE,SEARCH_EXTS from IRSADMIN_DB_TRAN_LIST where STATE='Y' and APP_ID=%s order by ORDER_ID asc"
    log.info(sql % menuTable.app_id)
    cur.execute(sql, menuTable.app_id)
    rows = cur.fetchall()
    fieldlist=""
    field_uitype_list = []
    field_search_list = []  #查询配置，用于枚举转换
    for item in rows:
        if fieldlist.__len__()==0:
            fieldlist = item[0]
        else:
            fieldlist=fieldlist+','+item[0]
        #获取uitype,对multipleimage要使用list返回结果
        field_uitype_list.append(item[1])
        field_search_list.append(item[2])
        #根据查询配置获取反回结果


    if TranRegTable.where_ctrl==None or TranRegTable.where_ctrl=="":
        if whereinfo.__len__()>0:
            TranRegTable.where_ctrl="where 1=1"
    else:
        if 'WHERE' not in TranRegTable.where_ctrl.upper():
            TranRegTable.where_ctrl='where '+TranRegTable.where_ctrl
        if '${ORGID}' in TranRegTable.where_ctrl:
            orgidsql="(SELECT org_id FROM irsadmin_user_org WHERE user_id='%s')" % request.session.get('user_id', None)
            TranRegTable.where_ctrl = TranRegTable.where_ctrl.replace('${ORGID}', orgidsql)

    #获取总笔数,分页使用
    selsql = "select count(1) from "+ TranRegTable.table_name+" "+TranRegTable.where_ctrl+" "+whereinfo+" "
    log.info(selsql)
    cur.execute(selsql)
    row = cur.fetchone()
    totalnum =row[0]

    #分页查询
    if pagesize==0 or not pagesize:
        pagesize = 10
    if pagenum==0  or not pagenum:
        pagenum = 1
    startno = (pagenum - 1) * pagesize
    # endno = (pagenum) * pagesize

    selsql = "select " + fieldlist + " from " + TranRegTable.table_name + " " + TranRegTable.where_ctrl + " " + whereinfo + " " + TranRegTable.order_ctrl
    selsql = selsql +" limit %s, %s" % (startno, pagesize)
    log.info(selsql)
    cur.execute(selsql)
    rows = cur.fetchall()

    fieldlist=fieldlist.split(',')
    #print("查询时获取的表头字段:",fieldlist)
    data = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": "selecttabledata",
        "totalnum":"0",
        "tabledata":[]
    }

    for item in rows:
        dataitem={}
        loopid = 0
        for subitem in item:
            if subitem==None or len(str(subitem))==0:
                subitem=""

            dataitem[fieldlist[loopid]] = subitem

            if field_search_list[loopid] and field_uitype_list[loopid] !='transfer':
                if '${THIS}' in (field_search_list[loopid]): #有查询配置，获取值对应的描述信息
                    if len(str(subitem))>0:
                        descsql = field_search_list[loopid].replace('${THIS}', '%s')
                        desccur = connection.cursor()
                        # log.info(descsql % str(subitem))
                        desccur.execute(descsql % str(subitem))
                        descrow = desccur.fetchone()
                        if descrow != None:
                            dataitem[fieldlist[loopid]] = str(subitem) + ' - ' + str(descrow[0])
                        desccur.close()

            # log.info('fieldname='+fieldlist[loopid]+',uitype='+field_uitype_list[loopid]+',value='+str(subitem) )
            if field_uitype_list[loopid]=='multipleimage':
                dataitem[fieldlist[loopid]] = []
                for itemlist in str(subitem).split(';'):
                    if len(itemlist) > 0:
                        dataitem[fieldlist[loopid]].append(itemlist)
                #图片不存在时，显示图片不存在的默认图片
                # if len(dataitem[fieldlist[loopid]])==0:
                #     dataitem[fieldlist[loopid]].append(public.localurl+'static/images/irs_noimg_exists.png')
            #循环数+1
            loopid = loopid + 1

        data['tabledata'].append(dataitem)
    cur.close()
    data['totalnum']=totalnum
    s = json.dumps(data, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info('----------------------Admin-selectTableData-end---------------------------')
    return HttpResponse(s)

#插入表数据
def AddTableData(request):
    log = public.logger
    log.info('----------------------Admin-selectTableData-begin---------------------------')

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    log.info(reqest_body)
    menuid = reqest_body.get('MENU_ID', None)
    if menuid == None:
        s = public.setrespinfo({"respcode": "310001", "respmsg": "菜单编号必输!"})
        return HttpResponse(s)
    try:
        MenuTable = models.IrsadminMenu.objects.get(menu_id=menuid)
    except models.IrsadminMenu.DoesNotExist:
        MenuTable = None
        s = public.setrespinfo({"respcode": "310002", "respmsg": "菜单编号不存在!"})
        return HttpResponse(s)
    try:
        TranRegTable=models.IrsadminDbTranReg.objects.get(app_id=MenuTable.app_id)
    except models.IrsadminDbTranReg.DoesNotExist:
        TranRegTable = None
        s = public.setrespinfo({"respcode": "310003", "respmsg": "应用编号不存在!"})
        return HttpResponse(s)

    if TranRegTable.insert_able!='Y':
        s = public.setrespinfo({"respcode": "320001", "respmsg": "该交易没有添加数据的权限!"})
        return HttpResponse(s)

    #校验权限
    flag=userrole.checkauth(request.session.get('user_id', None), MenuTable.menu_id)
    if flag==False:
        s = public.setrespinfo({"respcode": "349921", "respmsg": "用户权限不正确!"})
        return HttpResponse(s)

    #上送字段等数据
    DataReq = reqest_body['datainfo']
    fieldlist=''
    for item in DataReq.keys():
        #print(item)
        if fieldlist=='':
            fieldlist=item
        else:
            fieldlist=fieldlist+','+item

    valuelist = ''
    valuedata=()
    for item in DataReq.values():
        #print(item)
        if valuelist == '':
            valuelist = '%s'
        else:
            valuelist = valuelist+','+'%s'
        if type(item) == type([]) :
            tmpvalue=""
            for tmpitem in item:
                if tmpvalue=="":
                    tmpvalue=tmpitem
                else:
                    tmpvalue=tmpvalue+';'+tmpitem
            item = tmpvalue
        if item=="":
            item=None
        tmptuple=(item,)
        valuedata=valuedata+tmptuple
    # print('fieldlist=', fieldlist)
    # print('valuelist=',valuelist)
    # print('valuedata=', valuedata)

    if  str(menuid) == '2': #新增用户，主要解决传输框数据问题
        fieldlist_dict=fieldlist.split(',')
        # print('valuedata=',valuedata)

        i=0
        data_dict = {}
        for item in fieldlist_dict:
            data_dict[item.lower()]=valuedata[i]
            i=i+1
        if data_dict['user_id']==None or data_dict['user_id']=='':
            del data_dict['user_id']
        # print('IrsadminUser data_dict=', data_dict)
        IrsadminUser=models.IrsadminUser(**data_dict)
        IrsadminUser.save()
        # print('IrsadminUser=',IrsadminUser)

        #传输框数据处理
        Transfer = reqest_body['transfer_data']
        # print(type(Transfer),Transfer)
        for item in Transfer:
            # print('item=',item)
            RolePurvTable = models.IrsadminUserRule(
                user_id=IrsadminUser.user_id,
                role_id=item
            )
            RolePurvTable.save(force_insert=True)
    else: #其它数据表的新增，走通用处理
        sql = 'insert into '+TranRegTable.table_name+'('+fieldlist+') values ('+valuelist+')'
        log.info(sql % valuedata)
        cur = connection.cursor()
        cur.execute(sql, valuedata)
        cur.close()

    # 特殊处理，新增UITYPE='transfer'穿梭框,用于有些表的联表操作
    if str(menuid) == '6': #新增角色
        Transfer=reqest_body['transfer_data']
        # print(type(Transfer),Transfer)
        for item in Transfer:
            # print('item=',item)
            RolePurvTable=models.IrsadminRolePurv(
                role_id=DataReq['ROLE_ID'],
                menu_id=item
            )
            RolePurvTable.save(force_insert=True)
        # texcfg.addrolepurv()

    resp = {"respcode": "000000", "respmsg": "交易成功"}
    s = json.dumps(resp, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-selectTableData-end---------------------------')
    return HttpResponse(s)

#删除表数据
def DelTableData(request):
    log = public.logger
    log.info('----------------------Admin-DelTableData-begin---------------------------')

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    log.info(reqest_body)
    menuid = reqest_body.get('MENU_ID', None)
    if menuid == None:
        s = public.setrespinfo({"respcode": "310001", "respmsg": "菜单编号必输!"})
        return HttpResponse(s)
    try:
        MenuTable = models.IrsadminMenu.objects.get(menu_id=menuid)
    except models.IrsadminMenu.DoesNotExist:
        MenuTable = None
        s = public.setrespinfo({"respcode": "310002", "respmsg": "菜单编号不存在!"})
        return HttpResponse(s)
    try:
        TranRegTable=models.IrsadminDbTranReg.objects.get(app_id=MenuTable.app_id)
    except models.IrsadminDbTranReg.DoesNotExist:
        TranRegTable = None
        s = public.setrespinfo({"respcode": "310003", "respmsg": "应用编号不存在!"})
        return HttpResponse(s)

    if TranRegTable.delete_able!='Y':
        s = public.setrespinfo({"respcode": "320002", "respmsg": "该交易没有删除数据的权限!"})
        return HttpResponse(s)

    try:
        TranList=models.IrsadminDbTranList.objects.filter(app_id=MenuTable.app_id, is_key='Y').values('field_id','ui_type','search_exts')
    except models.IrsadminDbTranList.DoesNotExist:
        TranList = None
        s = public.setrespinfo({"respcode": "310004", "respmsg": "应用配置不存在!"})
        return HttpResponse(s)

    #校验权限
    flag=userrole.checkauth(request.session.get('user_id', None), MenuTable.menu_id)
    if flag==False:
        s = public.setrespinfo({"respcode": "349921", "respmsg": "用户权限不正确!"})
        return HttpResponse(s)

    keylist=[]
    for item in TranList:
        #print(item['field_id'])
        keylist.append(item['field_id'])

    # print('keylist=',keylist)
    #上送字段等数据
    DataReqList = reqest_body['datainfo']
    #print(type(DataReqList),DataReqList)
    for DataReq in DataReqList:
        #print(type(DataReq), DataReq)
        wheresql=''
        for item in DataReq:
            #print(item, '===', DataReq[item])
            if item not in keylist:
                continue

            if wheresql=='':
                wheresql=item+'="'+str(DataReq[item])+'"'
            else:
                wheresql = wheresql+' and '+str(item) + '="' + str(DataReq[item]) + '"'

        if wheresql == '':
            s = public.setrespinfo({"respcode": "320003", "respmsg": "删除数据必须上送主键做为删除条件!"})
            return HttpResponse(s)


        #print('wheresql=',wheresql)
        sql = 'delete from '+TranRegTable.table_name+' where '+wheresql
        log.info(sql)
        cur = connection.cursor()
        cur.execute(sql)
        cur.close()

    # 特殊处理，新增UITYPE='transfer'穿梭框,用于有些表的联表操作
    if str(menuid) == '6':
        RolePurvTable = models.IrsadminRolePurv(
            role_id=DataReq['ROLE_ID']
        )
        RolePurvTable.delete()
    if str(menuid) == '2':
        UserRoleTable = models.IrsadminUserRule(
            user_id=DataReq['USER_ID']
        )
        UserRoleTable.delete()

    # 处理穿梭框的数据
    tranfercfg_id = None
    for item in TranList:
        if item['ui_type'] == 'transfer':
            tranfercfg_id = item['search_exts']
            break
    # tranfercfg_id中存的就是穿梭框的数据
    if tranfercfg_id:
        try:
            TranferCfg = models.IrsadminDbTranferCfg.objects.get(id=tranfercfg_id)
        except models.IrsadminDbTranferCfg.DoesNotExist:
            TranferCfg = None

        if TranferCfg:
            data = deltransferdata(TranferCfg, reqest_body)

    resp = {"respcode": "000000", "respmsg": "交易成功"}
    s = json.dumps(resp, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-DelTableData-end---------------------------')
    return HttpResponse(s)

#新更表数据
def UpdTableData(request):
    log = public.logger
    log.info('----------------------Admin-UpdTableData-begin---------------------------')

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    log.info(reqest_body)
    menuid = reqest_body.get('MENU_ID', None)
    if menuid == None:
        s = public.setrespinfo({"respcode": "310001", "respmsg": "菜单编号必输!"})
        return HttpResponse(s)
    try:
        MenuTable = models.IrsadminMenu.objects.get(menu_id=menuid)
    except models.IrsadminMenu.DoesNotExist:
        MenuTable = None
        s = public.setrespinfo({"respcode": "310002", "respmsg": "菜单编号不存在!"})
        return HttpResponse(s)
    try:
        TranRegTable=models.IrsadminDbTranReg.objects.get(app_id=MenuTable.app_id)
    except models.IrsadminDbTranReg.DoesNotExist:
        TranRegTable = None
        s = public.setrespinfo({"respcode": "310003", "respmsg": "应用编号不存在!"})
        return HttpResponse(s)
    if TranRegTable.update_able!='Y':
        s = public.setrespinfo({"respcode": "320003", "respmsg": "该交易没有更新数据的权限!"})
        return HttpResponse(s)

    try:
        TranList=models.IrsadminDbTranList.objects.filter(app_id=MenuTable.app_id).values('field_id','is_key','search_exts','ui_type')
    except models.IrsadminDbTranList.DoesNotExist:
        TranList = None
        s = public.setrespinfo({"respcode": "310004", "respmsg": "应用配置不存在!"})
        return HttpResponse(s)

    #校验权限
    flag=userrole.checkauth(request.session.get('user_id', None), MenuTable.menu_id)
    if flag==False:
        s = public.setrespinfo({"respcode": "349921", "respmsg": "用户权限不正确!"})
        return HttpResponse(s)

    keylist=[]
    field_search_list={}
    for item in TranList:
        if item['is_key']=='Y':  #获取主键列表
            keylist.append(item['field_id'])
        field_search_list[item['field_id']]=item['search_exts']

    #print('keylist=',keylist)
    # print('field_search_list=', field_search_list)
    #上送字段等数据
    DataReq = reqest_body['datainfo']
    #print(type(DataReq),DataReq)
    wheresql=''
    updatesql=''
    updatevalue=()
    for item in DataReq:
        if item not in keylist:
            if DataReq[item]=='' or DataReq[item]==None \
                or DataReq[item]=='null' or DataReq[item]=='NULL' \
                or DataReq[item] =='Null':
                DataReq[item]=None
            if updatesql=='':
                updatesql=item+'=%s'
            else:
                updatesql = updatesql+','+str(item) + '=%s'

            # print(item,'=',type(DataReq[item]),DataReq[item])
            if type(DataReq[item]) == type([]):
                tmpvalue = ""
                for tmpitem in DataReq[item]:
                    #上送的是图片不存在的图片，跳过不处理
                    # if 'irs_noimg_exists.png' in tmpitem:
                    #     continue

                    if tmpvalue == "":
                        tmpvalue = tmpitem
                    else:
                        tmpvalue = tmpvalue + ';' + tmpitem
            else:
                tmpvalue=DataReq[item]

            #去掉查询配置生成的解释说明
            if field_search_list[item]:
                if '${THIS}' in (field_search_list[item]):
                    if DataReq[item]:
                        # log.info('item=' + str(item) + ',DataReq[item]=' + str(DataReq[item]))
                        tmpvalue = str(DataReq[item]).split(' - ')[0]

            tmptuple = (tmpvalue,)
            updatevalue = updatevalue + tmptuple
        else:
            if wheresql=='':
                wheresql=item+'="'+str(DataReq[item])+'"'
            else:
                wheresql = wheresql+' and '+item + '="' + DataReq[item] + '"'

    if wheresql == '':
        s = public.setrespinfo({"respcode": "320002", "respmsg": "更新数据必须上送主键做为更新条件!"})
        return HttpResponse(s)

    #print('wheresql=',wheresql)
    sql = 'update '+TranRegTable.table_name+' set '+updatesql+' where '+wheresql
    log.info(sql % updatevalue)
    cur = connection.cursor()
    effect_row = cur.execute(sql, updatevalue)
    cur.close()
    # print(effect_row)
    if effect_row <= 0:
        s=public.setrespinfo({"respcode": "310010", "respmsg": "更新数据失败，找不到记录!"})
        return HttpResponse(s)

    # 特殊处理，新增UITYPE='transfer'穿梭框,用于有些表的联表操作
    if str(menuid) == '6':
        Transfer = reqest_body['transfer_data']
        # print(type(Transfer), Transfer)
        RolePurvTable = models.IrsadminRolePurv(
            role_id=DataReq['ROLE_ID']
        )
        RolePurvTable.delete()
        for item in Transfer:
            RolePurvTable = models.IrsadminRolePurv(
                role_id=DataReq['ROLE_ID'],
                menu_id=item
            )
            RolePurvTable.save(force_insert=True)
        # texcfg.addrolepurv()

    # 特殊处理，新增UITYPE='transfer'穿梭框,用于有些表的联表操作
    if str(menuid) == '2':
        Transfer = reqest_body['transfer_data']
        # print(type(Transfer), Transfer)
        UserRoleTable = models.IrsadminUserRule(
            user_id=DataReq['USER_ID']
        )
        UserRoleTable.delete()
        for item in Transfer:
            UserRoleTable = models.IrsadminUserRule(
                user_id=DataReq['USER_ID'],
                role_id=item
            )
            UserRoleTable.save(force_insert=True)
            # texcfg.addrolepurv()

    #处理穿梭框的数据
    tranfercfg_id = None
    for item in TranList:
        if item['ui_type'] == 'transfer':
            tranfercfg_id=item['search_exts']
            break
    #tranfercfg_id中存的就是穿梭框的数据
    if tranfercfg_id:
        try:
            TranferCfg=models.IrsadminDbTranferCfg.objects.get(id=tranfercfg_id)
        except models.IrsadminDbTranferCfg.DoesNotExist:
            TranferCfg=None

        if TranferCfg:
            data=updatetransferdata(TranferCfg, reqest_body)

    resp = {"respcode": "000000", "respmsg": "交易成功"}
    s = json.dumps(resp, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('--------------------Admin-UpdTableData-end-------------------------')
    return HttpResponse(s)

#获取下拉列表配置数据
def GetListData(request):
    log = public.logger
    log.info('--------------------Admin-GetListData-begin-------------------------')

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    log.info(reqest_body)
    menuid = reqest_body.get('MENU_ID', None)
    if menuid == None:
        s = public.setrespinfo({"respcode": "310001", "respmsg": "菜单编号必输!"})
        return HttpResponse(s)
    try:
        MenuTable = models.IrsadminMenu.objects.get(menu_id=menuid)
    except models.IrsadminMenu.DoesNotExist:
        MenuTable = None
        s = public.setrespinfo({"respcode": "310002", "respmsg": "菜单编号不存在!"})
        return HttpResponse(s)
    try:
        TranRegTable=models.IrsadminDbTranReg.objects.get(app_id=MenuTable.app_id)
    except models.IrsadminDbTranReg.DoesNotExist:
        TranRegTable = None
        s = public.setrespinfo({"respcode": "310003", "respmsg": "应用编号不存在!"})
        return HttpResponse(s)

    try:
        TranList=models.IrsadminDbTranList.objects.filter(app_id=MenuTable.app_id)
    except models.IrsadminDbTranList.DoesNotExist:
        TranList = None
        s = public.setrespinfo({"respcode": "310004", "respmsg": "应用配置不存在!"})
        return HttpResponse(s)

    resp = {"respcode": "000000",
            "respmsg": "交易成功",
            "trantype": "getlistdata",
            "listinfo":{}}
    # 获取数据字典配置--begin
    for itemlist in TranList:
        if itemlist.ui_type in ['list']:
            #自定义配置
            if itemlist.search_exts:
                cur = connection.cursor()
                sql = itemlist.search_exts
                if '${ORGID}' in sql:
                    orgidsql = "(SELECT org_id FROM irsadmin_user_org WHERE user_id='%s')" % request.session.get('user_id', None)
                    sql = sql.replace('${ORGID}', orgidsql)
                log.info('自定义下拉数据：'+sql)
                cur.execute(sql)
                rows = cur.fetchall()
                listinfo = []
                for item in rows:
                    listtemp = {}
                    listtemp['value'] = str(item[0])
                    listtemp['label'] = str(item[1])
                    listinfo.append(listtemp)
                resp["listinfo"][itemlist.field_id] = listinfo
                cur.close()
            else: #默认配置
                listkey = TranRegTable.table_name + "." + itemlist.field_id
                #print(listkey)
                try:
                    DictTable = models.IrsYwtyDict.objects.filter(dict_name=listkey)
                    #print(DictTable)
                except models.IrsYwtyDict.DoesNotExist:
                    DictTable = None
                    continue

                if DictTable.__len__() == 0:
                    continue

                listinfo = []
                for item in DictTable:
                    listtemp = {}
                    listtemp['value'] = item.dict_code
                    listtemp['label'] = item.dict_target
                    listinfo.append(listtemp)
                resp["listinfo"][itemlist.field_id]=listinfo
    # 获取数据字典配置--end

    s = json.dumps(resp, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-GetListData-end---------------------------')
    return HttpResponse(s)

#获取穿梭框数据
def GetTransferData(request):
    log = public.logger
    log.info('----------------------Admin-selectTableData-begin---------------------------')

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    log.info(reqest_body)
    menuid = reqest_body.get('MENU_ID', None)
    if menuid == None:
        s = public.setrespinfo({"respcode": "310001", "respmsg": "菜单编号必输!"})
        return HttpResponse(s)
    try:
        MenuTable = models.IrsadminMenu.objects.get(menu_id=menuid)
    except models.IrsadminMenu.DoesNotExist:
        MenuTable = None
        s = public.setrespinfo({"respcode": "310002", "respmsg": "菜单编号不存在!"})
        return HttpResponse(s)
    try:
        TranRegTable = models.IrsadminDbTranReg.objects.get(app_id=MenuTable.app_id)
    except models.IrsadminDbTranReg.DoesNotExist:
        TranRegTable = None
        s = public.setrespinfo({"respcode": "310003", "respmsg": "应用编号不存在!"})
        return HttpResponse(s)

    try:
        TranList = models.IrsadminDbTranList.objects.filter(app_id=MenuTable.app_id)
    except models.IrsadminDbTranList.DoesNotExist:
        TranList = None
        s = public.setrespinfo({"respcode": "310004", "respmsg": "应用配置不存在!"})
        return HttpResponse(s)

    data = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": "gettransferdata",
        "left_title": "左边标题",
        "left_data": [],
        "right_title": "右边标题",
        "right_data": []
    }
    # print('TranRegTable.table_name=',TranRegTable.table_name)
    # 特殊处理，新增UITYPE='transfer'穿梭框,用于有些表的联表操作
    if str(menuid) == '6':  #用户权限配置
        data=texcfg.getrolepurv(data, reqest_body)
    if str(menuid) == '2':  #用户角色配置
        data=texcfg.getuserrole(data, reqest_body)
    else:
        tranfercfg_id=None
        for item in TranList:
            if item.ui_type == 'transfer':
                tranfercfg_id=item.search_exts
                break
        #item中存的就是穿梭框的数据
        if tranfercfg_id:
            try:
                TranferCfg=models.IrsadminDbTranferCfg.objects.get(id=item.search_exts)
            except models.IrsadminDbTranferCfg.DoesNotExist:
                TranferCfg=None

            if TranferCfg:
                data=gettransferdata(TranferCfg, reqest_body)

    s = json.dumps(data, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-selectTableData-end---------------------------')
    return HttpResponse(s)

#获取穿梭框的数据
def gettransferdata(TranferCfg, reqest_body):
    log = public.logger
    data = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": "gettransferdata",
        "left_title": TranferCfg.left_title,
        "left_data": [],
        "right_title": TranferCfg.right_title,
        "right_data": []
    }

    #获取左边的数据
    if reqest_body.get('data',None): #修改数据
        selsql = sqlreplace(TranferCfg.left_sql, reqest_body['data'])
    else: #新增数据
        selsql = TranferCfg.left_sql
    log.info("获取穿梭框左边的数据"+selsql)
    cur = connection.cursor()
    try:
        cur.execute(selsql)
        datalist = cur.fetchall()
        for item in datalist:
            data['left_data'].append({"key": str(item[0]), "label": str(item[1])} )
    except:
        log.error('获取穿梭框左边的数据失败', exc_info=True)
        log.info('执行sql错误:'+selsql)
    finally:
        cur.close()

    #获取右边的数据
    if reqest_body.get('data',None):  #修改数据
        selsql=sqlreplace(TranferCfg.right_sql, reqest_body['data'])
        cur = connection.cursor()
        try:
            cur.execute(selsql)
            datalist = cur.fetchall()
            for item in datalist:
                data['right_data'].append(item[0])
        except:
            log.error('获取穿梭框右边的数据失败', exc_info=True)
            log.info('执行sql错误:'+selsql)
        finally:
            cur.close()
    else: #新增数据,穿梭框右边的数据为空
        pass
    return data

#更新穿梭框的数据
def updatetransferdata(TranferCfg, reqest_body):
    log = public.logger
    data = {
        "respcode": "000000",
        "respmsg": "交易成功",
    }

    #删除穿梭框的数据
    delsql = sqlreplace(TranferCfg.delete_sql, reqest_body['datainfo'])
    cur = connection.cursor()
    try:
        # log.info('执行sql语句:'+delsql)
        cur.execute(delsql)
    except:
        log.error('清除指定穿梭框表中的数据失败', exc_info=True)
        log.info('执行sql错误:'+delsql)
    finally:
        cur.close()

    #插入新的右边数据
    insertsql=sqlreplace( TranferCfg.insert_sql, reqest_body['datainfo'])
    cur = connection.cursor()
    try:
        for item in reqest_body.get('transfer_data',None):
            print(item)
            inssql=insertsql.replace('${RIGHT_ID}', item)
            # log.info('执行sql语句:' + insertsql)
            cur.execute(inssql)
    except:
        log.error('插入指定穿梭框表中的数据失败', exc_info=True)
        log.info('执行sql错误:' + inssql)
    finally:
        cur.close()

    return data


#删除穿梭框的数据
def deltransferdata(TranferCfg, reqest_body):
    log = public.logger
    data = {
        "respcode": "000000",
        "respmsg": "交易成功",
    }

    #删除穿梭框的数据
    delsql = sqlreplace(TranferCfg.delete_sql, reqest_body['datainfo'])
    cur = connection.cursor()
    try:
        # log.info('执行sql语句:'+delsql)
        cur.execute(delsql)
    except:
        log.error('清除指定穿梭框表中的数据失败', exc_info=True)
        log.info('执行sql错误:'+delsql)
    finally:
        cur.close()

    return data

#使用替换的方式重新生成sql
def sqlreplace(sql, jsondata):
    newsql=sql
    for item in jsondata:
        restr='${THISDATA}.'+item
        # print(restr)
        newsql=newsql.replace(restr, str(jsondata[item]) )

    return newsql
