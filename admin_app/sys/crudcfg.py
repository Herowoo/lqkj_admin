import sys
from django.shortcuts import HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime

#增删改查配置配置操作主流程
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
def get_table_list( request ):
    log = public.logger
    try:
        cur = connection.cursor()  # 创建游标
        sql="select table_name, table_comment from information_schema.tables " \
            "where table_schema not in ('sys', 'mysql','performance_schema','information_schema') " \
            "order by table_name asc"
        cur.execute(sql)
        rows = cur.fetchall()
        table_list=[]
        for item in rows:
            tableitem={}
            tableitem["value"] = item[0]
            tableitem["lable"] = item[0]+'  '+item[1]
            table_list.append(tableitem)
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
        "BODY": {
            "table_list":table_list
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#增删改查配置-获取表的字段信息
def get_table_info( request ):
    log = public.logger
    body = public.req_body  # 请求报文体
    tablename = body.get('tablename')
    if not tablename:
        public.respcode, public.respmsg = "100101", "表名必输!"
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    cur = connection.cursor()
    # 根据表名获取表信息
    tablename=tablename.upper()
    try:
        sql = "SELECT LOWER(column_name), column_comment FROM information_schema.columns " \
              "WHERE UPPER(table_name) = UPPER(%s) order by ordinal_position asc"
        # log.info(sql % tablename)
        cur.execute(sql, tablename)
        rows = cur.fetchall()

        table_field = []

        loopid = 0
        for item in rows:
            tableitem = {}
            loopid = loopid + 1
            tableitem["field_id"] = item[0]
            tableitem["field_name"] = item[1]
            table_field.append(tableitem)
        cur.close()
    except Exception as ex:
        log.error("获取数据表信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100102", "获取数据表信息失败!"
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "table_field": table_field
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#增删改查配置-获取配置列表
def get_crud_list( request ):
    log = public.logger
    try:
        cur = connection.cursor()  # 创建游标
        sql="select app_id, app_name from sys_crud_cfg_head order by upd_time desc"
        cur.execute(sql)
        rows = cur.fetchall()
        crud_list=[]
        for item in rows:
            tableitem={}
            tableitem["value"] = str(item[0])
            tableitem["lable"] = str(item[0])+'  '+str(item[1])
            crud_list.append(tableitem)
        cur.close()
    except Exception as ex:
        log.error("获取增删改查配置信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100103", "获取增删改查配置信息失败!"
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "crud_list":crud_list
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#增删改查配置-获取增删改查配置的字段信息
def get_crud_info( request ):
    log = public.logger
    body = public.req_body  # 请求报文体
    appid = body.get('app_id')
    tablename = body.get('table_name')
    if (tablename == None or tablename=='') and (appid == None or appid==''):
        public.respcode, public.respmsg = "100101", "配置应用ID或者表名必输!"
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    cur = connection.cursor()
    if tablename:  # 根据表名获取表信息
        tablename=tablename.upper()
        try:
            sql = "SELECT column_name, column_comment, data_type, is_nullable,  " \
                  "column_key, column_default, character_maximum_length,  numeric_precision, " \
                  "extra "
            sql = sql + "FROM information_schema.columns WHERE UPPER(table_name) = UPPER(%s) "
            sql = sql + "order by ordinal_position"
            # log.info(sql % tablename)
            cur.execute(sql, tablename)
            rows = cur.fetchall()
            table_info = {}
            table_field = []

            table_info["APP_ID"] = "" #获取表信息时还没有appid
            table_info["TRAN_ID"] = ""
            table_info["APP_NAME"] = ""
            table_info["WHERE_CTRL"] = ""
            table_info["ORDER_CTRL"] = ""
            table_info["TABLE_NAME"] = tablename
            table_info["DATA_SOURCE"] = ""
            table_info["MAIN_CONTROL"] = ""
            table_info["SELECT_ABLE"] = True
            table_info["INSERT_ABLE"] = False
            table_info["UPDATE_ABLE"] = False
            table_info["DELETE_ABLE"] = False
            table_info["EXPORT_ABLE"] = False
            table_info["IMPORT_ABLE"] = False
            table_info["INSERT_FORMID"] = ""
            table_info["UPDATE_FORMID"] = ""
            table_info["DELETE_FORMID"] = ""
            table_info["EXPORT_FORMID"] = ""
            table_info["IMPORT_FORMID"] = ""
            table_info["SNOTE"] = "SNOTE"

            loopid = 0
            for item in rows:
                tableitem = {}
                loopid = loopid + 1
                tableitem["APP_ID"] = ""
                tableitem["TRAN_ID"] = ""
                tableitem["FIELD_ID"] = item[0]
                tableitem["FIELD_NAME"] = item[1]
                tableitem["STATE"] = True
                tableitem["DATA_TYPE"] = item[2]
                tableitem["UI_TYPE"] = "text"  # 先默认是文本
                if item[3] == "YES" or item[3] == "yes":
                    tableitem["ALLOW_BLANK"] = True
                else:
                    tableitem["ALLOW_BLANK"] = False
                if item[4] == "PRI":
                    tableitem["IS_KEY"] = True
                else:
                    tableitem["IS_KEY"] = False
                tableitem["SEARCH_TYPE"] = ""
                tableitem["SEARCH_EXTS"] = ""
                tableitem["EDIT_ABLE"] = False
                tableitem["DEF_VALUE"] = item[5]
                tableitem["ORDER_ID"] = str(loopid)
                tableitem["SNOTE"] = ""

                if item[6] and len(str(item[6])) > 0:
                    maxlength = item[6]
                else:
                    maxlength = item[7]
                if maxlength == None or maxlength == '':
                    if tableitem["DATA_TYPE"] in ['date', 'DATE']:
                        maxlength = 10
                        tableitem["UI_TYPE"] = 'date'
                    elif tableitem["DATA_TYPE"] in ['time', 'TIME']:
                        maxlength = 8
                        tableitem["UI_TYPE"] = 'time'
                    elif tableitem["DATA_TYPE"] in ['datetime', 'DATETIME']:
                        maxlength = 19
                        tableitem["UI_TYPE"] = 'datetime'
                    elif tableitem["DATA_TYPE"] in ['timestamp', 'TIMESTAMP']:
                        maxlength = 23
                        tableitem["UI_TYPE"] = 'datetime'
                    else:
                        maxlength = 23

                showlength = None
                if item[8] == 'auto_increment':  # 自增变量
                    tableitem["UI_TYPE"] = 'auto_increment'
                    showlength = 4

                # 显示长度初始值
                if showlength == 0 or showlength == None:
                    showlength = len(tableitem["FIELD_NAME"])
                if showlength == 0:
                    showlength = 8
                # print('maxlength=',maxlength)
                maxlength = int(maxlength)
                if maxlength > 30:
                    tableitem["FIELD_LENGTH"] = 30
                elif maxlength < 4:
                    tableitem["FIELD_LENGTH"] = 4
                else:
                    tableitem["FIELD_LENGTH"] = showlength
                tableitem["MAX_LENGTH"] = maxlength

                table_field.append(tableitem)
            cur.close()
        except Exception as ex:
            log.error("获取数据表信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
            public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
            public.respcode, public.respmsg = "100102", "获取数据表信息失败!"
            public.respinfo = HttpResponse( public.setrespinfo() )
            return public.respinfo
    else: #根据配置应用ID获取配置信息
        try:

            sql = "select app_id, app_name,tran_id,where_ctrl,order_ctrl,table_name,data_source, " \
                  " main_control,select_able,insert_able,update_able,delete_able,export_able,import_able,snote," \
                  "insert_formid,update_formid,delete_formid,export_formid,import_formid" \
                  " from sys_crud_cfg_head where app_id=%s "
            # log.info(sql % appid)
            cur.execute(sql, appid)
            row = cur.fetchone()
            table_info = {}
            table_field = []

            table_info["APP_ID"] = row[0]
            table_info["APP_NAME"] = row[1]
            table_info["TRAN_ID"] = row[2]
            table_info["WHERE_CTRL"] = row[3]
            table_info["ORDER_CTRL"] = row[4]
            table_info["TABLE_NAME"] = row[5]
            table_info["DATA_SOURCE"] = row[6]
            table_info["MAIN_CONTROL"] = row[7]
            table_info["SELECT_ABLE"] = public.Y2True(row[8])
            table_info["INSERT_ABLE"] = public.Y2True(row[9])
            table_info["UPDATE_ABLE"] = public.Y2True(row[10])
            table_info["DELETE_ABLE"] = public.Y2True(row[11])
            table_info["EXPORT_ABLE"] = public.Y2True(row[12])
            table_info["IMPORT_ABLE"] = public.Y2True(row[13])
            table_info["SNOTE"] = row[14]
            table_info["INSERT_FORMID"] = row[15]
            table_info["UPDATE_FORMID"] = row[16]
            table_info["DELETE_FORMID"] = row[17]
            table_info["EXPORT_FORMID"] = row[18]
            table_info["IMPORT_FORMID"] = row[19]

            sql = "select app_id, tran_id, field_id, field_name, state, data_type, ui_type," \
                  " allow_blank, is_key, search_type, search_exts, edit_able, def_value, order_id, snote, field_length," \
                  " max_length" \
                  " from sys_crud_cfg_body where app_id=%s order by order_id asc "
            log.info(sql % appid)
            cur.execute(sql, appid)
            rows = cur.fetchall()
            loopid = 0
            for item in rows:
                tableitem = {}
                loopid = loopid + 1
                tableitem["APP_ID"] = item[0]
                tableitem["TRAN_ID"] = item[1]
                tableitem["FIELD_ID"] = item[2]
                tableitem["FIELD_NAME"] = item[3]
                tableitem["STATE"] = public.Y2True(item[4])
                tableitem["DATA_TYPE"] = item[5]
                tableitem["UI_TYPE"] = item[6]
                tableitem["ALLOW_BLANK"] = public.Y2True(item[7])
                tableitem["IS_KEY"] = public.Y2True(item[8])
                tableitem["SEARCH_TYPE"] = item[9]
                tableitem["SEARCH_EXTS"] = item[10]
                tableitem["EDIT_ABLE"] = public.Y2True(item[11])
                tableitem["DEF_VALUE"] = item[12]
                tableitem["ORDER_ID"] = item[13]
                tableitem["SNOTE"] = item[14]
                tableitem["FIELD_LENGTH"] = item[15]
                tableitem["MAX_LENGTH"] = item[16]
                table_field.append(tableitem)
            cur.close()
        except Exception as ex:
            log.error("获取数据表信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
            public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
            public.respcode, public.respmsg = "100102", "获取数据表信息失败!"
            public.respinfo = HttpResponse( public.setrespinfo() )
            return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "crud_info":table_info,
            "crud_field": table_field
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#增删改查配置-增删改查配置创建
def crud_cfg_create( request ):
    log = public.logger
    body = public.req_body  # 请求报文体
    crud_info = body.get('crud_info')
    crud_field = body.get('crud_field')

    if not crud_info or not crud_field:
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100103", "配置交易上送信息有误!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    appid=crud_info.get('APP_ID')
    try:
        cur = connection.cursor()  # 创建游标
        if appid: #先把原来的配置删除掉
            appid=int(appid)
            sql = "delete from sys_crud_cfg_head where app_id=%s"
            cur.execute(sql, appid)
            sql = "delete from sys_crud_cfg_body where app_id=%s"
            cur.execute(sql, appid)
        else:
            appid=None

        #登记增删改查配置HEAD表
        sql = "insert into sys_crud_cfg_head(app_id, app_name,tran_id,where_ctrl,order_ctrl,table_name,data_source," \
              "main_control,select_able,insert_able,update_able,delete_able,export_able,import_able, snote," \
              "insert_formid,update_formid,delete_formid,export_formid,import_formid ) " \
              "values(%s,%s,%s,%s,%s,  %s,%s,%s,%s,%s,   %s,%s,%s,%s,%s,   %s,%s,%s,%s,%s )"
        log.info(sql % (appid,crud_info.get('APP_NAME'),crud_info.get('TRAN_ID'),crud_info.get('WHERE_CTRL'),
                         crud_info.get('ORDER_CTRL'), crud_info.get('TABLE_NAME'),crud_info.get('DATA_SOURCE'),
                         crud_info.get('MAIN_CONTROL'),public.True2y(crud_info.get('SELECT_ABLE')),public.True2y(crud_info.get('INSERT_ABLE')),
                         public.True2y(crud_info.get('UPDATE_ABLE')),public.True2y(crud_info.get('DELETE_ABLE')),
                         public.True2y(crud_info.get('EXPORT_ABLE')), public.True2y(crud_info.get('IMPORT_ABLE')),crud_info.get('SNOTE'),
                         crud_info.get('INSERT_FORMID'),crud_info.get('UPDATE_FORMID'),crud_info.get('DELETE_FORMID'),
                         crud_info.get('EXPORT_FORMID'),crud_info.get('IMPORT_FORMID') ),
                 extra={'ptlsh': public.req_seq})

        sql = "insert into sys_crud_cfg_head(app_id, app_name,tran_id,where_ctrl,order_ctrl,table_name,data_source," \
              "main_control,select_able,insert_able,update_able,delete_able,export_able,import_able, snote," \
              "insert_formid,update_formid,delete_formid,export_formid,import_formid ) " \
              "values(%s,%s,%s,%s,%s,  %s,%s,%s,%s,%s,   %s,%s,%s,%s,%s,   %s,%s,%s,%s,%s )"
        cur.execute(sql,(appid,crud_info.get('APP_NAME'),crud_info.get('TRAN_ID'),crud_info.get('WHERE_CTRL'),
                         crud_info.get('ORDER_CTRL'), crud_info.get('TABLE_NAME'),crud_info.get('DATA_SOURCE'),
                         crud_info.get('MAIN_CONTROL'),public.True2y(crud_info.get('SELECT_ABLE')),public.True2y(crud_info.get('INSERT_ABLE')),
                         public.True2y(crud_info.get('UPDATE_ABLE')),public.True2y(crud_info.get('DELETE_ABLE')),
                         public.True2y(crud_info.get('EXPORT_ABLE')), public.True2y(crud_info.get('IMPORT_ABLE')),crud_info.get('SNOTE'),
                         crud_info.get('INSERT_FORMID'),crud_info.get('UPDATE_FORMID'),crud_info.get('DELETE_FORMID'),
                         crud_info.get('EXPORT_FORMID'),crud_info.get('IMPORT_FORMID') ) )
        if not appid:#如果没有appid,获取本线程最后插入的appid
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                appid = row[0]
                log.info('APP_ID生成，自增字段ID:%s' % str(appid), extra={'ptlsh': public.req_seq})
            else:
                public.respcode, public.respmsg = "100104", "登记配置信息表异常!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
        for item in crud_field:
            # 登记增删改查配置BODY表
            sql = "insert into sys_crud_cfg_body(app_id, tran_id, field_id, field_name, state, data_type, ui_type," \
                  "allow_blank, is_key, search_type, search_exts, edit_able, def_value, order_id, snote, field_length, max_length) " \
                  "values( %s,%s,%s,%s,%s, %s,%s,%s,%s,%s ,%s,%s,%s,%s,%s, %s,%s)"
            cur.execute(sql, (appid,item.get('TRAN_ID'),item.get('FIELD_ID').lower(),
                              item.get('FIELD_NAME'),public.True2y(item.get('STATE')),item.get('DATA_TYPE'),
                              item.get('UI_TYPE'),public.True2y(item.get('ALLOW_BLANK')),public.True2y(item.get('IS_KEY')),
                              item.get('SEARCH_TYPE'),item.get('SEARCH_EXTS'),public.True2y(item.get('EDIT_ABLE')),
                              item.get('DEF_VALUE'),item.get('ORDER_ID'),item.get('SNOTE'),item.get('FIELD_LENGTH'),
                              item.get('MAX_LENGTH')  ) )
            # log.info('登记增删改查配置BODY表成功', extra={'ptlsh': public.req_seq})
        cur.close()
    except Exception as ex:
        log.error("登记配置信息表失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100103", "登记配置信息表失败!"
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "app_id":appid
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#增删改查配置-增删改查配置页面渲染
def crud_cfg_show( request ):
    log = public.logger
    body = public.req_body  # 请求报文体

    if not public.menu_id:
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100103", "配置交易上送信息有误!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    #获取用户对应的增删改查权限
    def get_data_able( insert_able, delete_able, update_able, import_able, export_able ):

        #如果是超级用户，返回所有权限
        sql = "select 1 from sys_user_role where role_id = 'root' and user_id='%s' " % (public.user_id)
        cur.execute(sql)
        row= cur.fetchall()
        if row:
            return public.Y2True(insert_able), public.Y2True(delete_able), public.Y2True(update_able), public.Y2True(import_able), public.Y2True(export_able)

        # 0 - "查询数据"
        # 1 - "添加数据"
        # 2 - "删除数据"
        # 3 - "更新数据"
        # 4 - "导入数据"
        # 5 - "导出数据"
        insert_flag = False
        update_flag = False
        delete_flag = False
        export_flag = False
        import_flag = False

        sql="select a.auth_type from sys_role_purv_head a, sys_user_role b  " \
            "where a.role_id=b.role_id and a.menu_id='%s' and b.user_id='%s' " % ( public.menu_id, public.user_id )
        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            if item[0] == '1' and insert_able == 'Y':
                insert_flag=True
            elif item[0] == '2' and delete_able == 'Y':
                delete_flag=True
            elif item[0] == '3' and update_able == 'Y':
                update_flag=True
            elif item[0] == '4' and import_able == 'Y':
                import_flag=True
            elif item[0] == '5' and export_able == 'Y':
                export_flag=True

        return insert_flag, delete_flag, update_flag, import_flag, export_flag
    try:
        cur = connection.cursor()  # 创建游标
        #根据menuid获取增删改查配置的appid
        sql = "select app_id from sys_menu where menu_id='%s' " % (public.menu_id)
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            appid = row[0]
        else:
            public.respcode, public.respmsg = "100105", "查询菜单对应的APPID异常!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not appid:
            public.respcode, public.respmsg = "100105", "查询菜单对应的APPID异常!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        # 获取字段权限
        role_purv_body = []
        sql = "select distinct upper(a.field_id), a.show_able, a.dis_able from sys_role_purv_body a, sys_user_role b " \
              "where a.ROLE_ID=b.ROLE_ID and a.app_id='%s' and b.USER_ID='%s' " % (appid, public.user_id)
        log.info("获取字段权限SQL:" + sql, extra={'ptlsh': public.req_seq})
        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            if item[0] in ['', 'FORMTRAN_EXESQL']:
                continue
            role_purv_body.append(item[0] + '-show_able-' + item[1])
            role_purv_body.append(item[0] + '-dis_able-' + item[2])
        log.info("获取字段权限结果:" + str(role_purv_body), extra={'ptlsh': public.req_seq})

        #查询增删改查配置HEAD信息
        sql = "select app_id, app_name,tran_id,where_ctrl,order_ctrl,table_name,data_source," \
              "main_control,select_able,insert_able,update_able,delete_able,export_able,import_able, snote," \
              "insert_formid,update_formid,delete_formid,export_formid,import_formid " \
              " from sys_crud_cfg_head where app_id='%s' " % appid
        # log.info("查询增删改查配置HEAD信息:"+sql, extra={'ptlsh':public.req_seq})
        cur.execute(sql)
        crud_head_row = cur.fetchone()
        tran_id = crud_head_row[2]
        table_name = crud_head_row[5]

        insert_able = crud_head_row[9]
        update_able = crud_head_row[10]
        delete_able = crud_head_row[11]
        export_able = crud_head_row[12]
        import_able = crud_head_row[13]

        #同步判断角色权限
        insert_able, delete_able, update_able, import_able, export_able = get_data_able(insert_able, delete_able, update_able, import_able, export_able)

        insert_formid = crud_head_row[15]
        update_formid = crud_head_row[16]
        delete_formid = crud_head_row[17]
        export_formid = crud_head_row[18]
        import_formid = crud_head_row[19]

        #查询增删改查配置BODY信息
        sql = "select distinct a.field_id, a.field_name, a.field_length, a.search_type, a.ui_type, " \
              "a.max_length, upper(a.edit_able), upper(a.allow_blank), upper(a.is_key), a.data_type, " \
              "a.def_value, a.search_exts " \
              "from sys_crud_cfg_body a  where a.state='Y' and a.app_id='%s' order by a.order_id asc " % appid
        log.info("查询增删改查配置BODY信息:"+sql, extra={'ptlsh':public.req_seq})
        cur.execute(sql)
        crud_body_rows = cur.fetchall()

        data = {
            "tableHead": [],
            "ButtonInfo": [],
            "searchinfo": [{
                "SearchInfo": {
                    "selectoptions": [],
                    "selecttypes": [],
                    "selectoption": {
                        "label": '',
                        "value": '',
                        "uitype": ''
                    },
                    "selecttype": "",
                    "selectvalue": "",
                }
            }],
            "tableAble": {
                "INSERT_ABLE": insert_able ,
                "UPDATE_ABLE": update_able,
                "DELETE_ABLE": delete_able,
                "EXPORT_ABLE": export_able,
                "IMPORT_ABLE": import_able,
            },
            "form_cfg": {
                "INSERT_FORMID": insert_formid,
                "UPDATE_FORMID": update_formid,
                "DELETE_FORMID": delete_formid,
                "EXPORT_FORMID": export_formid,
                "IMPORT_FORMID": import_formid,
            },
            "listinfo":{},#下接列表的配置

        }

        data['searchinfo'][0]['SearchInfo']['selecttypes'] = public.selecttypes
        tableHead = []
        selectoptions = []
        for item in crud_body_rows:
            # print(item)
            tableitem = {}
            tableitem["label"] = item[1]
            tableitem["property"] = item[0] #字段ID

            # log.info(str(tableitem["property"].upper() + '-show_able-Y'))
            if len(role_purv_body) > 0 and tableitem["property"].upper() + '-show_able-Y' not in role_purv_body:
                continue  #此字段权限配置中不显示给此用户

            # 页面显示的列宽度width
            fieldlength = item[2]
            # print(type(fieldlength), fieldlength)
            if fieldlength == None or not fieldlength:
                fieldlength = len(item[1])

            fieldlength = int(fieldlength)
            if fieldlength > 30:
                tableitem["width"] = 30 * 14
            elif fieldlength <= len(item[1]):
                tableitem["width"] = len(item[1]) * 14
            else:
                tableitem["width"] = fieldlength * 14

            tableitem["width"] = fieldlength * 14
            tableitem["uitype"] = item[4]
            tableitem["MAX_LENGTH"] = item[5]

            if item[6] == 'Y':
                log.info( tableitem["property"].upper() + '-dis_able-N' )
                if len(role_purv_body)>0 and tableitem["property"].upper() + '-dis_able-N' in role_purv_body:
                    tableitem["EDIT_ABLE"] = True
                elif len(role_purv_body)>0:
                    tableitem["EDIT_ABLE"] = False
                else:
                    tableitem["EDIT_ABLE"] = True
            else:
                tableitem["EDIT_ABLE"] = False

            # 是否为空属性
            if item[7] == 'Y' or item[7] == 'y':
                tableitem["ALLOW_BLANK"] = True
            else:
                tableitem["ALLOW_BLANK"] = False
            # 主键不允许为空
            if item[8] == 'Y' or item[8] == 'y':
                tableitem["ALLOW_BLANK"] = False

            # 数据类型
            tableitem["DATA_TYPE"] = item[9]

            tableitem["DEF_VALUE"] = item[10]  # 默认值

            tableHead.append(tableitem)

            # 查询条件配置
            if item[3] == None or item[3] == "":
                pass
            else:
                searchitem = {}
                searchitem["label"] = item[1]
                searchitem["value"] = item[0]
                searchitem["uitype"] = item[4]
                selectoptions.append(searchitem)

            #获取下拉列表
            search_exts = item[11] #下拉查询类型
            if tableitem["uitype"] in ['list']:
                # 自定义配置
                if search_exts:
                    sql = search_exts
                    if '${ORGID}' in sql:
                        orgidsql = "(SELECT org_id FROM irsadmin_user_org WHERE user_id='%s')" % request.session.get(
                            'user_id', None)
                        sql = sql.replace('${ORGID}', orgidsql)
                    log.info('自定义下拉数据：' + sql)
                    cur.execute(sql)
                    rows = cur.fetchall()
                    listinfo = []
                    for item in rows:
                        listtemp = {}
                        listtemp['value'] = str(item[0])
                        listtemp['label'] = str(item[1])
                        listinfo.append(listtemp)
                    data["listinfo"][tableitem["property"]] = listinfo
                else:  # 默认配置
                    listkey = table_name + "." + tableitem["property"]
                    sql="select dict_code,dict_target from irs_ywty_dict where dict_name='%s' " % listkey
                    cur.execute(sql)
                    rows = cur.fetchall()
                    listinfo = []
                    for item in rows:
                        listtemp = {}
                        listtemp['value'] = item[0]
                        listtemp['label'] = item[1]
                        listinfo.append(listtemp)
                    data["listinfo"][tableitem["property"]] = listinfo

        data['tableHead'] = tableHead
        if selectoptions.__len__() > 0:
            data['searchinfo'][0]['SearchInfo']['selectoptions'] = selectoptions
        else:
            # 没有查询条件
            data.pop('searchinfo')

        if len(tran_id) > 0 and str(tran_id) != '0':
            # 获取按钮配置信息
            sql="select id,button_name,button_type,button_color,button_trantype,button_length " \
                "from irsadmin_tran_cfg where id in %s" % str( tuple( str(tran_id).split(',') ) )
            log.info("获取按钮配置信息:"+sql)
            cur.execute(sql)
            rows = cur.fetchall()
            if rows:
                buttonlength = 30
                for item in rows:
                    buttonitem = {}
                    buttonitem['BUTTON_NAME'] = item[1]
                    buttonitem['BUTTON_TYPE'] = item[2]
                    buttonitem['BUTTON_COLOR'] = item[3]
                    buttonitem['BUTTON_TRANTYPE'] = item[4]
                    data['ButtonInfo'].append(buttonitem)
                    buttonlength = buttonlength + 30 + item[5]
                data['ButtonLength'] = buttonlength

        # 关闭游标
        cur.close()
        
    except Exception as ex:
        log.error("配置信息转换失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "100103", "配置信息转换失败!"
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

#增删改查配置-获取数据
def get_crud_data( request ):
    log = public.logger
    body=public.req_body

    if not public.menu_id:
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100103", "配置交易上送信息有误!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    #开始处理
    try:
        # 翻页查询请求
        pagesize = int(body.get('pagesize', "10"))
        pagenum = int(body.get('pagenum', "1"))

        cur = connection.cursor()  # 创建游标
        # 根据menuid获取增删改查配置的appid
        sql = "select app_id from sys_menu where menu_id='%s' " % (public.menu_id)
        cur.execute(sql)
        row = cur.fetchone()
        if row:
            appid = row[0]
        else:
            public.respcode, public.respmsg = "100105", "查询菜单对应的APPID异常!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if not appid:
            public.respcode, public.respmsg = "100105", "查询菜单对应的APPID异常!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        # 查询增删改查配置HEAD信息
        sql = "select where_ctrl, order_ctrl, table_name" \
              " from sys_crud_cfg_head where app_id=%s "
        # log.info("查询增删改查配置HEAD信息:"+sql % appid, extra={'ptlsh':public.req_seq})
        cur.execute(sql, appid)
        crud_head_row = cur.fetchone()
        if crud_head_row:
            where_ctrl = crud_head_row[0]
            order_ctrl = crud_head_row[1]
            table_name = crud_head_row[2]
        else:
            public.respcode, public.respmsg = "100115", "查询APPID异常,数据不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        searchinfo = body.get('searchinfo', None)
        whereinfo = ""
        # print( type(searchinfo), searchinfo )
        if searchinfo:
            # 有查询条件
            for item in searchinfo:
                selectid = item.get('selectid', None)
                selecttype = item.get('selecttype', None)
                selectvalue = item.get('selectvalue', None)

                if selectid == None or selectid == "":
                    continue
                if selecttype == None or selecttype == "":
                    continue

                # if item['uitype'] == 'datetime' and selectvalue:
                #     selectvalue = datetime.datetime.strptime(selectvalue, "%Y-%m-%d %H:%M:%S")
                if selecttype == 'like' and selectvalue:
                    selectvalue = "%" + selectvalue + "%"
                wheretemp = " and " + selectid + " " + selecttype + " '" + selectvalue + "'"
                # print(wheretemp)
                if whereinfo == "":
                    whereinfo = wheretemp
                else:
                    whereinfo = whereinfo + ' ' + wheretemp

        if where_ctrl == None:
            where_ctrl = ""
        if order_ctrl == None:
            order_ctrl = ""

        cur = connection.cursor()
        # sql = "select field_id,ui_type,search_exts from sys_crud_cfg_body " \
        #       "where state='y' and app_id=%s order by order_id asc"
        #为了使隐藏ID的也好用，所以状态不再做为条件。。
        sql = "select field_id,ui_type,search_exts from sys_crud_cfg_body " \
              "where  app_id=%s order by order_id asc"
        log.info(sql % appid, extra={'ptlsh':public.req_seq})
        cur.execute(sql, appid)
        rows = cur.fetchall()
        fieldlist = ""
        field_uitype_list = []
        field_search_list = []  # 查询配置，用于枚举转换
        for item in rows:
            if fieldlist.__len__() == 0:
                fieldlist = item[0]
            else:
                fieldlist = fieldlist + ',' + item[0]
            # 获取uitype,对multipleimage要使用list返回结果
            field_uitype_list.append(item[1])
            field_search_list.append(item[2])
            # 根据查询配置获取反回结果
        fieldlist = fieldlist.replace('data_seq_no', '1 as data_sql_no')

        if where_ctrl == None or where_ctrl == "":
            if whereinfo.__len__() > 0:
                where_ctrl = "where 1=1"
        else:
            if 'WHERE' not in where_ctrl.upper():
                where_ctrl = 'where ' + where_ctrl
            if '${USER_ID}' in where_ctrl:
                where_ctrl = where_ctrl.replace('${USER_ID}', str(public.user_id))
            if '${ORGID}' in where_ctrl:
                orgidsql = "(SELECT org_id FROM sys_user_org WHERE user_id='%s')" % public.user_id
                where_ctrl = where_ctrl.replace('${ORGID}', orgidsql)
            if '${ORG_ID}' in where_ctrl:
                orgidsql = "(SELECT org_id FROM sys_user_org WHERE user_id='%s')" % public.user_id
                where_ctrl = where_ctrl.replace('${ORG_ID}', orgidsql)

        # 获取总笔数,分页使用
        selsql = "select count(1) from " + table_name + " " + where_ctrl + " " + whereinfo + " " + order_ctrl
        log.info(selsql, extra={'ptlsh':public.req_seq})
        cur.execute(selsql)
        row = cur.fetchone()
        totalnum = row[0]

        # 分页查询
        if pagesize == 0 or not pagesize:
            pagesize = 10
        if pagenum == 0 or not pagenum:
            pagenum = 1
        startno = (pagenum - 1) * pagesize
        # endno = (pagenum) * pagesize

        selsql = "select " + fieldlist + " from " + table_name + " " + where_ctrl + " " + whereinfo + " " + order_ctrl
        selsql = selsql + " limit %s, %s" % (startno, pagesize)
        log.info(selsql, extra={'ptlsh':public.req_seq})
        cur.execute(selsql)
        rows = cur.fetchall()

        fieldlist = fieldlist.split(',')
        # print("查询时获取的表头字段:",fieldlist)
        data = {
            "totalnum": "0",
            "tabledata": []
        }

        data_seq_no = totalnum - (pagenum - 1) * pagesize  # 增加当前数据的序号（倒序)
        for item in rows:
            dataitem = {}
            loopid = 0
            for subitem in item:
                if subitem == None or len(str(subitem)) == 0:
                    subitem = ""
                # log.info('=mytest=='+str(fieldlist[loopid])+'-----'+str(data_seq_no)  )
                #增加一个data_sql_no序号, add by litz, 2020-10-30
                if fieldlist[loopid] == '1 as data_sql_no': #序号列，为虚列不控制
                    dataitem['data_seq_no'] = data_seq_no
                    data_seq_no = data_seq_no - 1
                    loopid = loopid + 1
                    continue

                dataitem[fieldlist[loopid]] = subitem

                if field_search_list[loopid] and field_uitype_list[loopid] != 'transfer':
                    if '${THIS}' in (field_search_list[loopid]):  # 有查询配置，获取值对应的描述信息
                        if len(str(subitem)) > 0:
                            descsql = field_search_list[loopid].replace('${THIS}', '%s')
                            desccur = connection.cursor()
                            # log.info(descsql % str(subitem))
                            desccur.execute(descsql % str(subitem))
                            descrow = desccur.fetchone()
                            if descrow != None:
                                dataitem[fieldlist[loopid]] = str(subitem) + ' - ' + str(descrow[0])
                            desccur.close()

                # log.info('fieldname='+fieldlist[loopid]+',uitype='+field_uitype_list[loopid]+',value='+str(subitem) )
                if field_uitype_list[loopid] == 'multipleimage':
                    dataitem[fieldlist[loopid]] = []
                    for itemlist in str(subitem).split(';'):
                        if len(itemlist) > 0:
                            dataitem[fieldlist[loopid]].append(itemlist)
                            # 图片不存在时，显示图片不存在的默认图片
                            # if len(dataitem[fieldlist[loopid]])==0:
                            #     dataitem[fieldlist[loopid]].append(public.localurl+'static/images/irs_noimg_exists.png')

                # 循环数+1
                loopid = loopid + 1

            data['tabledata'].append(dataitem)
        cur.close()
        data['totalnum'] = totalnum
        cur.close()

    except Exception as ex:
        log.error("获取增删改查配置信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()
        public.respcode, public.respmsg = "100103", "数据查询失败!"
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": data
    }

    log.info("json_data:"+str(json_data), extra={'ptlsh': public.req_seq})

    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo
