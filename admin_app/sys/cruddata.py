import sys
from django.shortcuts import HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
from admin_app import models #早晚我要删除它

#增删改查配置数据操作主流程
@transaction.atomic()
def Main_Proc( request ):
    public.respcode, public.respmsg = "999998", "交易开始处理!"
    log = public.logger
    sid = transaction.savepoint()
    func_name=public.tran_type+'(request)'
    if globals().get(public.tran_type):
        log.info('---[%s]-begin---' % (public.tran_type), extra={'ptlsh': public.req_seq})
        public.respinfo = eval(func_name)
        log.info('---[%s]-end----' % (public.tran_type), extra={'ptlsh': public.req_seq})
    else:
        public.respcode, public.respmsg = "100002", "trantype error!"
        public.respinfo = HttpResponse( public.setrespinfo() )
    if public.respcode=="000000":
        # 提交事务
        transaction.savepoint_commit(sid)
    # else:
    #     # 回滚事务
    #     transaction.savepoint_rollback(sid)
    return public.respinfo

#增删改查配置-获取数据库中的所有表名
def gettransferdata( request ):
    log = public.logger

    try:
        data = {
            "left_title": "左边标题",
            "left_data": [],
            "right_title": "右边标题",
            "right_data": []
        }

        left_sql = ''
        right_sql = ''

        cur = connection.cursor()  # 创建游标

        # 特殊处理，新增UITYPE='transfer'穿梭框,用于有些表的联表操作
        if str(public.menu_id) == '6':  # 用户权限配置
            data['left_title'] = '未分配功能菜单'
            data['right_title'] = '已分配功能菜单'
            left_sql = "select menu_id, menu_name from sys_menu where is_run_menu='Y' and is_enable='Y'"
            right_sql="select menu_id from irsadmin_role_purv where role_id in " \
                      "(select ROLE_ID from irsadmin_user_rule where user_id='%s' ) " % public.user_id
        elif str(public.menu_id) == '2':  # 用户角色配置
            data['left_title'] = '未分配用户角色'
            data['right_title'] = '已分配用户角色'
            left_sql = "select role_id,role_name from irsadmin_role "
            right_sql="select role_id,role_name from irsadmin_role where ROLE_ID in  " \
                      "(select ROLE_ID from irsadmin_user_rule where user_id = '%s') " % public.user_id
        else:
            sql = "select search_exts from sys_crud_cfg_body " \
                  "where app_id=(select app_id from sys_menu where menu_id='%s') and ui_type='transfer' " % public.menu_id
            log.info("查询穿梭框SQL配置:"+sql, extra={'ptlsh': public.req_seq})
            cur.execute(sql)
            row = cur.fetchone() #返回的json结构只能返回一个穿梭框
            if row:
                search_exts=row[0]
                sql = "select left_title, left_sql, right_title, right_sql from irsadmin_db_tranfer_cfg " \
                      "where id='%s' " % search_exts
                cur.execute(sql)
                row = cur.fetchone()  # 返回的json结构只能返回一个穿梭框
                data['left_title'] = row[0]
                data['right_title'] = row[2]

                # 使用替换的方式重新生成sql
                def sqlreplace(sql, jsondata):
                    newsql = sql
                    for item in jsondata:
                        restr = '${THISDATA}.' + item
                        # print(restr)
                        newsql = newsql.replace(restr, str(jsondata[item]))
                    return newsql

                left_sql = sqlreplace(row[1], public.req_body['data'])
                right_sql = sqlreplace(row[3], public.req_body['data'])

        if left_sql:
            # 左边的功能菜单, 全部的key-value
            log.info("左边的功能菜单, 全部的key-value: " + left_sql, extra={'ptlsh': public.req_seq})
            cur.execute(left_sql)
            rows = cur.fetchall()
            for item in rows:
                data['left_data'].append({"key": item[0], "label": item[1]})
        if right_sql:
            log.info("右边的功能菜单-已分配的key: " + right_sql, extra={'ptlsh': public.req_seq})
            # 右边的功能菜单-已分配的key
            cur.execute(right_sql)
            rows = cur.fetchall()
            for item in rows:
                data['right_data'].append( item[0] )

        cur.close()

    except Exception as ex:
        log.error("获取数据表信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100100", "获取数据表信息失败!"
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": data,
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#增删改查配置-单表添加数据
def addtabledata( request ):
    log = public.logger
    try:
        cur = connection.cursor()  # 创建游标

        # 查询增删改查配置HEAD信息
        sql = "select table_name from sys_crud_cfg_head where app_id = " \
              "(select app_id from sys_menu where menu_id='%s') " % public.menu_id
        # log.info("查询增删改查配置HEAD信息:"+sql % appid, extra={'ptlsh':public.req_seq})
        cur.execute(sql)
        crud_head_row = cur.fetchone()
        table_name = crud_head_row[0]

        # 上送字段等数据
        DataReq = public.req_body['datainfo']
        fieldlist = ''
        for item in DataReq.keys():
            # print(item)
            if fieldlist == '':
                fieldlist = item
            else:
                fieldlist = fieldlist + ',' + item

        valuelist = ''
        valuedata = ()
        for item in DataReq.values():
            # print(item)
            if valuelist == '':
                valuelist = '%s'
            else:
                valuelist = valuelist + ',' + '%s'
            if type(item) == type([]):
                tmpvalue = ""
                for tmpitem in item:
                    if tmpvalue == "":
                        tmpvalue = tmpitem
                    else:
                        tmpvalue = tmpvalue + ';' + tmpitem
                item = tmpvalue
            if item == "":
                item = None
            tmptuple = (item,)
            valuedata = valuedata + tmptuple
        # print('fieldlist=', fieldlist)
        # print('valuelist=',valuelist)
        # print('valuedata=', valuedata)

        if str(public.menu_id) == '2':  # 新增用户，主要解决传输框数据问题
            fieldlist_dict = fieldlist.split(',')
            # print('valuedata=',valuedata)

            i = 0
            data_dict = {}
            for item in fieldlist_dict:
                data_dict[item.lower()] = valuedata[i]
                i = i + 1
            if data_dict['user_id'] == None or data_dict['user_id'] == '':
                del data_dict['user_id']
            # print('IrsadminUser data_dict=', data_dict)
            IrsadminUser = models.IrsadminUser(**data_dict)
            IrsadminUser.save()
            # print('IrsadminUser=',IrsadminUser)

            # 传输框数据处理
            Transfer = public.req_body['transfer_data']
            # print(type(Transfer),Transfer)
            for item in Transfer:
                # print('item=',item)
                RolePurvTable = models.IrsadminUserRule(
                    user_id=IrsadminUser.user_id,
                    role_id=item
                )
                RolePurvTable.save(force_insert=True)
        else:  # 其它数据表的新增，走通用处理
            sql = 'insert into ' + table_name + '(' + fieldlist + ') values (' + valuelist + ')'
            log.info(sql % valuedata)
            cur = connection.cursor()
            cur.execute(sql, valuedata)
            cur.close()

        # 特殊处理，新增UITYPE='transfer'穿梭框,用于有些表的联表操作
        if str(public.menu_id) == '6':  # 新增角色
            Transfer = public.req_body['transfer_data']
            # print(type(Transfer),Transfer)
            for item in Transfer:
                # print('item=',item)
                RolePurvTable = models.IrsadminRolePurv(
                    role_id=DataReq['ROLE_ID'],
                    menu_id=item
                )
                RolePurvTable.save(force_insert=True)
                # texcfg.addrolepurv()

        #关闭游标
        cur.close()

    except Exception as ex:
        log.error("插入数据表信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100100", "插入数据表信息失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {},
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#增删改查配置-单表更新数据
def updtabledata( request ):
    log = public.logger

    try:

        cur = connection.cursor()  # 创建游标

        # 查询增删改查配置HEAD信息
        sql = "select table_name from sys_crud_cfg_head where app_id = " \
              "(select app_id from sys_menu where menu_id='%s') " % public.menu_id
        # log.info("查询增删改查配置HEAD信息:"+sql % appid, extra={'ptlsh':public.req_seq})
        cur.execute(sql)
        crud_head_row = cur.fetchone()
        table_name = crud_head_row[0]

        # 查询增删改查配置BODY信息
        sql ="select is_key, field_id, ui_type, search_exts " \
             "from sys_crud_cfg_body where  " \
             "  app_id=(select app_id from sys_menu where menu_id='%s') " % public.menu_id
        # log.info("查询增删改查配置HEAD信息:"+sql % appid, extra={'ptlsh':public.req_seq})
        cur.execute(sql)
        crud_body_row = cur.fetchall()

        keylist = []
        field_search_list = {}
        for item in crud_body_row:
            if item[0] == 'Y':  # 获取主键列表
                keylist.append(item[1])
            field_search_list[item[1]] = item[3]

        # print('keylist=',keylist)
        # print('field_search_list=', field_search_list)
        # 上送字段等数据
        DataReq = public.req_body['datainfo']
        # print(type(DataReq),DataReq)
        wheresql = ''
        updatesql = ''
        updatevalue = ()
        for item in DataReq:
            if item not in keylist:
                if DataReq[item] == '' or DataReq[item] == None \
                        or DataReq[item] == 'null' or DataReq[item] == 'NULL' \
                        or DataReq[item] == 'Null':
                    DataReq[item] = None
                if updatesql == '':
                    updatesql = item + '=%s'
                else:
                    updatesql = updatesql + ',' + str(item) + '=%s'

                # print(item,'=',type(DataReq[item]),DataReq[item])
                if type(DataReq[item]) == type([]):
                    tmpvalue = ""
                    for tmpitem in DataReq[item]:
                        # 上送的是图片不存在的图片，跳过不处理
                        # if 'irs_noimg_exists.png' in tmpitem:
                        #     continue

                        if tmpvalue == "":
                            tmpvalue = tmpitem
                        else:
                            tmpvalue = tmpvalue + ';' + tmpitem
                else:
                    tmpvalue = DataReq[item]

                # 去掉查询配置生成的解释说明
                if field_search_list[item]:
                    if '${THIS}' in (field_search_list[item]):
                        if DataReq[item]:
                            # log.info('item=' + str(item) + ',DataReq[item]=' + str(DataReq[item]))
                            tmpvalue = str(DataReq[item]).split(' - ')[0]

                tmptuple = (tmpvalue,)
                updatevalue = updatevalue + tmptuple
            else:
                if wheresql == '':
                    wheresql = item + '="' + str(DataReq[item]) + '"'
                else:
                    wheresql = wheresql + ' and ' + item + '="' + DataReq[item] + '"'

        if wheresql == '':
            public.respcode, public.respmsg = "320002", "更新数据必须上送主键做为更新条件!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
            return HttpResponse(s)

        # print('wheresql=',wheresql)
        sql = 'update ' + str(table_name) + ' set ' + str(updatesql) + ' where ' + str(wheresql)
        log.info(sql % updatevalue, extra={'ptlsh':public.req_seq})
        cur = connection.cursor()
        effect_row = cur.execute(sql, updatevalue)
        cur.close()
        # print(effect_row)
        if effect_row <= 0:
            public.respcode, public.respmsg = "310010", "更新数据失败，找不到记录!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo


        cur.close()

    except Exception as ex:
        log.error("更新数据表信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100100", "更新数据表信息失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {},
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#增删改查配置-单表删除数据
def deltabledata( request ):
    log = public.logger
    try:
        cur = connection.cursor()  # 创建游标

        # 查询增删改查配置HEAD信息
        sql = "select table_name from sys_crud_cfg_head where app_id = " \
              "(select app_id from sys_menu where menu_id='%s') " % public.menu_id
        # log.info("查询增删改查配置HEAD信息:"+sql % appid, extra={'ptlsh':public.req_seq})
        cur.execute(sql)
        crud_head_row = cur.fetchone()
        table_name = crud_head_row[0]

        # 查询增删改查配置BODY信息
        sql ="select field_id, ui_type, search_exts " \
             "from sys_crud_cfg_body where is_key='Y' " \
             " and app_id=(select app_id from sys_menu where menu_id='%s') " % public.menu_id
        # log.info("查询增删改查配置HEAD信息:"+sql % appid, extra={'ptlsh':public.req_seq})
        cur.execute(sql)
        crud_body_row = cur.fetchall()

        keylist = []
        for item in crud_body_row:
            # print(item['field_id'])
            keylist.append(item[0])

        # print('keylist=',keylist)
        # 上送字段等数据
        DataReqList = public.req_body['datainfo']
        # print(type(DataReqList),DataReqList)
        for DataReq in DataReqList:
            # print(type(DataReq), DataReq)
            wheresql = ''
            for item in DataReq:
                # print(item, '===', DataReq[item])
                if item not in keylist:
                    continue

                if wheresql == '':
                    wheresql = item + '="' + str(DataReq[item]) + '"'
                else:
                    wheresql = wheresql + ' and ' + str(item) + '="' + str(DataReq[item]) + '"'

            if wheresql == '':
                public.respcode, public.respmsg = "320003", "删除数据必须上送主键做为删除条件!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
                return HttpResponse(s)

            # print('wheresql=',wheresql)
            sql = 'delete from ' + table_name + ' where ' + wheresql
            log.info(sql)
            cur = connection.cursor()
            cur.execute(sql)

        cur.close()

    except Exception as ex:
        log.error("删除数据表信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100100", "删除数据表信息失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {},
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


#model
def funcmodel( request ):
    log = public.logger

    try:

        cur = connection.cursor()  # 创建游标

        cur.close()

    except Exception as ex:
        log.error("获取数据表信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100100", "获取数据表信息失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {},
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

