import sys
from django.shortcuts import render,redirect,HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime
import re

#配置操作主流程
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

# 根据formcfg获取字段明细,并插入字段明细表
def FormcfgFieldListIns(formid,formcfg):
    # log = public.logger
    # 递归获取表单所有组件
    def GetCompFormLayout(formcfg):
        comp_list = []
        for comp_item in formcfg:
            # print(comp_item)
            itemdict = {}
            if comp_item.get('children'):
                comp_list = comp_list + GetCompFormLayout(comp_item['children'])
                continue
            elif comp_item['type'] == 'null':
                continue
            elif comp_item['type'] == 'button': #按钮的话，取trantype做为field_id
                itemdict['field_id'] = comp_item['attrs']['tran_type']
            else:
                itemdict['field_id'] = comp_item['attrs']['variable']

            if '显示' in comp_item['attrs']['power']:
                itemdict['show_able'] = 'Y'
            else:
                itemdict['show_able'] = 'N'
            if '置灰' in comp_item['attrs']['power']:
                itemdict['dis_able'] = 'Y'
            else:
                itemdict['dis_able'] = 'N'
            itemdict['comp_id'] = comp_item['id']
            itemdict['comp_type'] = comp_item['type']
            itemdict['field_name'] = comp_item['attrs'].get('label')
            comp_list.append(itemdict)
        return comp_list

    comp_list = GetCompFormLayout(formcfg)
    cur = connection.cursor()  # 创建游标
    sql = "delete from sys_form_cfg_fieldlist where form_id=%s"
    cur.execute(sql, formid)
    for itm in comp_list:
        sql = "insert into sys_form_cfg_fieldlist(form_id, comp_id, comp_type, field_id, field_name, show_able, dis_able) " \
              "values(%s, %s, %s, %s, %s, %s, %s )"
        # log.info(sql % (formid, itm.get('comp_id'), itm.get('comp_type'), itm.get('field_id'),
        #                 itm.get('field_name'), itm.get('show_able','N'), itm.get('dis_able','N') )
        #          , extra={'ptlsh': public.req_seq})
        cur.execute(sql, (formid, itm.get('comp_id'), itm.get('comp_type'), itm.get('field_id'),
                          itm.get('field_name'), itm.get('show_able','N'), itm.get('dis_able','N') ) )
    cur.close()

#表单配置新增，主要是获取form_id
def form_cfg_create( request ):
    log = public.logger
    body = public.req_body  # 请求报文体
    form_id = body.get('form_id')
    form_name = body.get('form_name')
    form_show_tran_type = body.get('form_show_tran_type')
    form_show_api = body.get('form_show_api')
    form_cfg = body.get('form_cfg')
    # form_var = body.get('form_var')
    form_var = "{}" #创建获取ID，变量内容不需要

    # 递归获取表单按钮组件的SQL
    def GetFormButtonSql(Layout_list):
        comp_list = {}
        for comp_item in Layout_list:
            if comp_item.get('children'):
                # comp_list = comp_list + GetFormButtonSql(comp_item['children'])
                comp_list.update(GetFormButtonSql(comp_item['children']))
                continue
            elif comp_item['type'] == 'button':
                # button_key=comp_item['attrs']['tran_type']+'_'+comp_item['id']
                tran_append_sql = comp_item['attrs'].get('tran_append_sql')
                comp_list[comp_item['id']]=tran_append_sql
            else:
                continue
        return comp_list

    try:
        form_cfg_json = json.loads(body.get('form_cfg'))
        form_sql = GetFormButtonSql( form_cfg_json )
        if form_sql:
            form_sql = json.dumps(form_sql)
        # log.info('form_sql:'+str(form_sql), extra={'ptlsh': public.req_seq})
        cur = connection.cursor()  # 创建游标
        if form_id:
            sql = "select CONCAT(form_name,'_copy'), form_cfg, form_var, form_sql, form_show_tran_type, form_show_api " \
                  "from sys_form_cfg_info where form_id=%s"
            cur.execute(sql,form_id)
            row = cur.fetchone()
            if not row:
                public.respcode, public.respmsg = "100010", "表单信息不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if not form_name:
                form_name=row[0]
            form_cfg = row[1]
            form_var = row[2]
            form_sql = row[3]
            form_show_tran_type = row[4]
            form_show_api = row[5]
        else:
            form_show_tran_type = 'form_cfg_show'
            form_show_api = '/interface/sys/formcfg'
            form_cfg = "[]"
            form_var = "{}"

        if form_sql:
            sql="insert into sys_form_cfg_info(form_name, form_show_tran_type, form_show_api, user_id, form_cfg, form_var, form_sql) " \
                "values(%s, %s, %s, %s, %s, %s, %s)"
            cur.execute(sql, ( form_name,form_show_tran_type,form_show_api, public.user_id, form_cfg, form_var, form_sql) )
        else:
            sql="insert into sys_form_cfg_info(form_name, form_show_tran_type, form_show_api,  user_id, form_cfg, form_var ) " \
                "values(%s, %s, %s, %s, %s, %s)"
            cur.execute(sql, ( form_name, form_show_tran_type,form_show_api, public.user_id, form_cfg, form_var ) )
        #查询刚刚插入的ID
        cur.execute("SELECT LAST_INSERT_ID()") #获取自增字段刚刚插入的ID
        row=cur.fetchone()
        if row:
            form_id=row[0]
            log.info('FormID生成，自增字段ID:%s' % str(form_id), extra={'ptlsh': public.req_seq})
        cur.close() #关闭游标

        #登记FORM字段属性表
        FormcfgFieldListIns(form_id, form_cfg_json)

    except Exception as ex:
        log.error("登记配置信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "登记配置信息失败!"
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "新增配置成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#表单配置修改
def form_cfg_update( request ):
    log = public.logger
    body = public.req_body  # 请求报文体
    form_id = body.get('form_id')
    form_cfg = body.get('form_cfg')
    form_var = body.get('form_var')
    form_show_tran_type = body.get('form_show_tran_type')
    form_show_api = body.get('form_show_api')

    # 递归获取表单按钮组件的SQL
    def GetFormButtonSql(Layout_list):
        comp_list = {}
        for comp_item in Layout_list:
            if comp_item.get('children'):
                # comp_list = comp_list + GetFormButtonSql(comp_item['children'])
                comp_list.update( GetFormButtonSql(comp_item['children']))
                continue
            elif comp_item['type'] == 'button':
                # button_key=comp_item['attrs']['tran_type']+'_'+comp_item['id']
                tran_append_sql = comp_item['attrs'].get('tran_append_sql')
                comp_list[comp_item['id']]=tran_append_sql
            else:
                continue
        return comp_list

    if not form_id:
        public.respcode, public.respmsg = "100021", "form_id不可为空!"
        public.respinfo =  HttpResponse( public.setrespinfo() )
        return public.respinfo

    try:
        if form_cfg:
            form_cfg_json = json.loads(form_cfg)
            form_sql = GetFormButtonSql( form_cfg_json )
        else:
            form_cfg_json = ''
            form_sql = {}
        form_sql = json.dumps(form_sql)

        cur = connection.cursor()  # 创建游标
        if body.get('form_var'):
            sql="update sys_form_cfg_info set form_var=%s, update_user=%s,update_date=%s where form_id=%s"
            cur.execute(sql, ( form_var, public.user_id, datetime.datetime.now(), form_id) )
        elif body.get('form_cfg'):
            sql = "update sys_form_cfg_info set form_name=%s, form_show_tran_type=%s, form_show_api=%s,  " \
                  "form_cfg=%s, form_sql=%s, update_user=%s,update_date=%s where form_id=%s"
            cur.execute(sql, ( body.get('form_name'), form_show_tran_type, form_show_api, form_cfg, form_sql,
                               public.user_id, datetime.datetime.now(), form_id) )
        else:
            sql = "update sys_form_cfg_info set form_name=%s, form_show_tran_type=%s, form_show_api=%s, " \
                  "form_cfg=%s, form_var=%s, form_sql=%s, update_user=%s,update_date=%s where form_id=%s"
            cur.execute(sql, ( body.get('form_name'), form_show_tran_type, form_show_api, form_cfg, form_var, form_sql,
                               public.user_id, datetime.datetime.now(), form_id))
        cur.close() #关闭游标

        if form_cfg_json:
            # 登记FORM字段属性表
            FormcfgFieldListIns(form_id, form_cfg_json)

    except Exception as ex:
        log.error("更新配置信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100011", "更新配置信息失败!"
        public.respinfo =  HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "更新配置成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#表单配置信息查询
def form_cfg_select( request ):
    log = public.logger
    body = public.req_body
    form_id = body.get('form_id', '')
    editor = body.get('editor', None)

    #删除非编辑模式下的SQL语句返回
    def DelSqlFormLayout(Layout_list):
        new_Layout_list=[]
        for comp_item in Layout_list:
            if comp_item.get( 'children'):
                comp_item['children'] = DelSqlFormLayout(comp_item['children'])
            elif comp_item['type'] == 'null':
                pass
            else:
                # log.info("comp_item" + str(comp_item))
                # 非编辑模式，隐藏SQL
                if comp_item['attrs'].get('tran_append_sql'):
                    comp_item['attrs']['tran_append_sql'] = ''  # 按钮中的交易附加SQL
                if comp_item['attrs'].get('render') and 'GetValueFromSQL' in comp_item['attrs'].get('render'):
                    comp_item['attrs']['render'] = ''  # 组件中的渲染规则
                if comp_item['attrs'].get('options_render') and 'GetValueFromSQL' in comp_item['attrs'].get('options_render'):
                    comp_item['attrs']['options_render'] = ''  # 组件中的选项渲染规则
                if comp_item['attrs'].get('table_render'):
                    comp_item['attrs']['table_render'] = ''  # 表格组件中的获取数据sql
                if comp_item['attrs'].get('data_sql'):
                    comp_item['attrs']['data_sql'] = ''  # 表格组件中的获取数据sql
                if comp_item['attrs'].get('delete_append_sql'):
                    comp_item['attrs']['delete_append_sql'] = ''  # 表格组件中的删除数据sql
            new_Layout_list.append(comp_item)
        # log.info("new_Layout_list" + str(new_Layout_list))
        return  new_Layout_list

    try:
        cur = connection.cursor()  # 创建游标

        if not form_id: #没有formid ,是菜单直接进入的交易。根据menuid取formid
            sql = "select app_id from sys_menu where menu_id=%s "
            log.info(sql % public.menu_id)
            cur.execute(sql, (public.menu_id))
            row = cur.fetchone()
            if not row:
                cur.close()
                log.info("对应的APPID不存在!", extra={'ptlsh': public.req_seq})
                public.respcode, public.respmsg = "100111", "对应的APPID不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

            form_id=row[0]

        sql="select form_name,form_show_tran_type, form_show_api, form_cfg,form_var from sys_form_cfg_info where form_id=%s"
        log.info(sql % form_id)
        cur.execute(sql, (form_id) )
        row=cur.fetchone()
        if row:
            form_name = row[0]
            form_show_tran_type = row[1]
            form_show_api = row[2]
            form_cfg = row[3]
            form_cfg = json.loads(form_cfg, encoding='utf-8')
            form_var = row[4]
            form_var = json.loads(form_var, encoding='utf-8')
        else:
            form_name = ''
            form_show_tran_type = 'form_cfg_show'
            form_show_api = '/interface/sys/formcfg'
            form_cfg = []
            form_var = {}

        if not editor: #非编辑模式，返回菜单字段权限
            # 获取表单字段权限
            role_purv_body = []
            sql = "select distinct upper(a.field_id), a.show_able, a.dis_able from sys_role_purv_body a, sys_user_role b " \
                  "where a.ROLE_ID=b.ROLE_ID and a.form_id='%s' and b.USER_ID='%s' " % (form_id, public.user_id)
            cur.execute(sql)
            rows = cur.fetchall()
            for item in rows:
                if item[0] in ['','FORMTRAN_EXESQL']:
                    continue
                role_purv_body.append(item[0] + '-show_able-' + item[1])
                role_purv_body.append(item[0] + '-dis_able-' + item[2])

            log.info('role_purv_body='+str(role_purv_body), extra={'ptlsh':public.req_seq})
            if len(role_purv_body) > 0:

                #判断字段是否显示
                def DueCompFormLayout(Layout_list, role_purv_body):
                    new_Layout_list = []
                    for comp_item in Layout_list:
                        if comp_item.get('children'):
                            comp_item['children'] = DueCompFormLayout(comp_item['children'], role_purv_body)
                        elif comp_item['type'] == 'null':
                            pass
                        else:
                            if comp_item['type'] == 'button':  # 按钮的话，取trantype做为field_id
                                field_id = comp_item['attrs']['tran_type']
                            else:
                                field_id = comp_item['attrs'].get('variable')
                            if field_id:
                                field_id=field_id.upper()
                                log.info('role_purv_body2=' + field_id+'-show_able-Y', extra={'ptlsh': public.req_seq})
                            power=[]
                            if field_id+'-show_able-Y' in role_purv_body:
                                power.append("显示")
                            if field_id+'-dis_able-N' not in role_purv_body:
                                power.append("置灰")
                            comp_item['attrs']['power'] = power
                        new_Layout_list.append(comp_item)
                    return new_Layout_list

                form_cfg = DueCompFormLayout(form_cfg, role_purv_body)  # 组件列表


            if form_cfg:
                form_cfg= DelSqlFormLayout(form_cfg) #删除SQL语句，避免数据库暴露

        #最终返回数据需要转为字符串
        if form_cfg:
            form_cfg = json.dumps(form_cfg )  # 将配置转换为字符串
        else:
            form_cfg = "[]"
        if form_var:
            form_var = json.dumps(form_var )  # 将配置转换为字符串
        else:
            form_var = "{}"

        cur.close() #关闭游标
    except Exception as ex:
        log.error("表单配置信息查询失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
        public.respcode, public.respmsg = "100110", "表单配置信息查询失败!"
        public.respinfo =  HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            "form_name":form_name,
            "form_show_tran_type": form_show_tran_type,
            "form_show_api": form_show_api,
            "form_cfg":form_cfg,
            "form_var":form_var,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


#表单渲染显示
def form_cfg_show( request ):
    log = public.logger
    body = public.req_body
    form_id = body.get('form_id', '')
    form_data = body.get('form_data', '') #可能为空
    if not form_data:
        form_data= {}
    try:
        cur = connection.cursor()  # 创建游标
        if not form_id: #没有formid ,是菜单直接进入的交易。根据menuid取formid
            sql = "select app_id from sys_menu where menu_id=%s "
            cur.execute(sql, (public.menu_id))
            row = cur.fetchone()
            if not row:
                cur.close()
                log.info("对应的APPID不存在!", extra={'ptlsh': public.req_seq})
                public.respcode, public.respmsg = "100111", "对应的APPID不存在!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

            form_id=row[0]

        sql="select form_cfg, form_var from sys_form_cfg_info where form_id=%s"
        log.info("查询表单配置信息:" + sql % form_id, extra={'ptlsh': public.req_seq})
        cur.execute(sql, (form_id) )
        row=cur.fetchone()
        if row:
            form_cfg = row[0]
            form_var = row[1]
        else:
            cur.close()
            log.info("对应的FORMID不存在!", extra={'ptlsh': public.req_seq})
            public.respcode, public.respmsg = "100111", "对应的FORMID不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur.close()

    except Exception as ex:
        log.error("表单配置信息查询失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100110", "表单配置信息查询失败!"
        public.respinfo =  HttpResponse( public.setrespinfo() )
        return public.respinfo

    #对关键字进行处理
    def keywords( keyword ):
        new_value=keyword
        if keyword == '${USER_ID}':
            new_value=public.user_id
        elif keyword == '${USER_NAME}':
            sql="select user_name from sys_user where user_id='%s'" % public.user_id
            cur.execute(sql)
            row=cur.fetchone()
            new_value=row[0]
        elif keyword == '${ORG_SPELL}':
            sql="select a.ORG_SPELL from sys_org a, sys_user_org b where a.org_id=b.org_id and b.user_id='%s' " \
                "order by b.OPERATE_DATETIME desc"  % public.user_id
            cur.execute(sql)
            row=cur.fetchone()
            new_value=row[0]
        elif keyword == '${TRAN_DATE}':
            new_value = datetime.datetime.now().strftime('%Y-%m-%d')
        elif keyword == '${TRAN_TIME}':
            new_value = datetime.datetime.now().strftime('%H:%M:%S')
        elif keyword == '${TRAN_DATETIME}':
            new_value = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elif keyword == '${YYYY}':  #当前年份
            new_value = datetime.datetime.now().strftime('%Y')
        elif keyword == '${YYYY-MM}':  # 当前年份
            new_value = datetime.datetime.now().strftime('%Y-%m')
        elif keyword == '${YYYYMM}':  # 当前年份
            new_value = datetime.datetime.now().strftime('%Y%m')
        elif keyword == '${WEEK}':  #当年第几周
            new_value = datetime.datetime.now().strftime('%W')
        # log.info('keyword=' + str(keyword), extra={'ptlsh': public.req_seq})
        # log.info('new_value='+str(new_value), extra={'ptlsh':public.req_seq})
        return new_value

    # 递归获取表单所有组件
    def GetCompFormLayout(Layout_list):
        comp_list = []
        for comp_item in Layout_list:
            if comp_item.get('children'):
                comp_list = comp_list + GetCompFormLayout(comp_item['children'])
                continue
            elif comp_item['type'] == 'null':
                continue
            else:
                comp_list.append(comp_item)
        return comp_list

    #处理配置的sql变量
    def GetValueFromSQL( render, render_type ):
        # log.info('render='+str(render), extra={'ptlsh':public.req_seq})
        pattern = re.compile("GetValueFromSQL{(.*)}")
        log.info('render=' + str(render), extra={'ptlsh': public.req_seq})
        sql = pattern.findall(render)[0]
        log.info('render sql=' + str(sql), extra={'ptlsh': public.req_seq})
        pattern = re.compile("\$\[(.*?)\]")
        sqlvar = pattern.findall(sql)
        for sqlitm in sqlvar:
            old = "$[" + sqlitm + "]"
            if sqlitm in form_data.keys():
                new = "'" + str(form_data.get(sqlitm)) + "'"
            else:
                new = "''"
            sql = sql.replace(old, new)
        log.info('real sql=' + str(sql), extra={'ptlsh': public.req_seq})
        sql = public.SqlKeywordConver(sql, form_var_dict)
        log.info('finally sql=' + str(sql), extra={'ptlsh': public.req_seq})
        cur.execute(sql)
        if render_type == 'options_render': #列表
            reslist = []
            rows = cur.fetchall()
            for resitm in rows:
                if len(resitm) == 2:
                    kv={}
                    kv['key'] = resitm[0]
                    kv['value'] = resitm[1]
                    reslist.append(kv)
                else:
                    reslist.append(resitm)
            return reslist
        elif render_type == 'table_render':
            reslist = []
            rows = cur.fetchall()
            for resitm in rows:
                kv = {}
                i = 0
                for tabitem in compitem['attrs'].get('head'):
                    kv[tabitem.get('name')] = resitm[i]
                    i = i+1
                reslist.append(kv)
            return reslist
        elif render_type == 'render': #数据
            reslist = ""
            rows = cur.fetchone()
            if rows: #查到数据了。
                reslist = rows[0]
            return reslist
        else:
            return ""

    #开始渲染表单
    try:
        cur = connection.cursor()  # 创建游标

        form_cfg = json.loads(form_cfg)
        form_var = json.loads(form_var)
        comp_list = GetCompFormLayout(form_cfg)  # 组件列表
        form_var_dict={}
        for compitem in comp_list:
            comptype=compitem.get('type')
            if comptype in ('button'):
                continue

            options_render = compitem['attrs'].get('options_render')
            options = compitem['attrs'].get('options')
            variable = compitem['attrs'].get('variable')
            if '.' in variable or  '[' in variable or  ']' in variable:  #前端解析多级结构
                continue

            #关键字段值转换
            if form_var_dict.get(variable):
                form_var_dict[variable] = keywords( form_var_dict[variable] )

            render = compitem['attrs'].get('render')
            # log.info( "compitem="+str(compitem), extra={'ptlsh': public.req_seq})
            if comptype in ['select','checkbox','radio']:  #下拉、选项字段的下拉内容渲染
                if options_render: #选项渲染, 用来放SQL语句
                    if 'GetValueFromSQL' in options_render:
                        try:
                            form_var_dict[options] = GetValueFromSQL(options_render, 'options_render')
                        except Exception as ex:
                            log.error('表单配置SQL错误:' + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
                            public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
                            public.respcode, public.respmsg = "100021", "表单配置项[%s]SQL错误!" % compitem['attrs'].get('label')
                            public.respinfo = HttpResponse(public.setrespinfo())
                            return public.respinfo
                    else:
                        form_var_dict[options] = options_render
                else: #没有SQL语句，直接取options的变量值
                    if options:
                        form_var_dict[options] =  form_var.get(options)

                if variable: #对绑定变量初始化
                    if form_data.get(variable):
                        form_var_dict[variable] = form_data.get(variable)
                    else:
                        form_var_dict[variable] = render
            elif comptype in ['table']:  # 表格内容渲染
                # tablehead = compitem['attrs']['head'][0]
                # print(type(tablehead), tablehead.keys())
                # if 'table' in tablehead.keys(): #增删改查配置的表格
                #     print('istable==', tablehead.get('table'))
                # el
                if render:  # 选项渲染, 用来放SQL语句
                    if 'GetValueFromSQL' in render:
                        try:
                            form_var_dict[variable] = GetValueFromSQL(render, 'table_render')
                        except Exception as ex:
                            log.error('表单配置SQL错误:' + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
                            public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
                            public.respcode, public.respmsg = "100021", "表单配置项[%s]SQL错误!" % compitem['attrs'].get('variable')
                            public.respinfo = HttpResponse(public.setrespinfo())
                            return public.respinfo
                    else:
                        form_var_dict[variable] = render
                else:  # 没有SQL语句，直接取options的变量值
                    if variable:
                        form_var_dict[variable] = form_var.get(variable)
            elif comptype in ['transfer']: #穿梭框
                if render and 'FUNC{' in render:  # 调用指定函数
                    from admin_app.tranapp import transfer
                    func_name = "transfer."+render[5:-1]+"( request )"
                    log.info("开始执行穿梭框自定义函数："+str(func_name), extra={'ptlsh': public.req_seq})
                    dataVariable = compitem['attrs'].get('dataVariable')
                    form_var_dict[variable], form_var_dict[dataVariable] = eval(func_name)
                else:
                    form_var_dict[variable] = ''
            elif comptype in ['tree']: #树结构
                if render and 'FUNC{' in render:  # 调用指定函数
                    from admin_app.tranapp import tree
                    func_name = "tree."+render[5:-1]+"( request )"
                    log.info("开始执行树结构自定义函数："+str(func_name), extra={'ptlsh': public.req_seq})
                    selectedVariable = compitem['attrs'].get('selectedVariable')
                    form_var_dict[variable], form_var_dict[selectedVariable] = eval(func_name)
                else:
                    form_var_dict[variable] = ''
            elif comptype in ['json_editor']: #JSON报文编辑框
                if form_data and form_data.get(variable):
                    form_var_dict[variable] = form_data.get(variable)
                elif render:  #值渲染
                    if 'GetValueFromSQL' in render:
                        try:
                            form_var_dict[variable] = GetValueFromSQL(render, 'render')
                        except Exception as ex:
                            log.error('表单配置SQL错误:' + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
                            public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
                            public.respcode, public.respmsg = "100021", "表单配置项[%s]SQL错误!" % compitem['attrs'].get('label')
                            public.respinfo = HttpResponse(public.setrespinfo())
                            return public.respinfo
                    else:
                        if variable:
                            if form_data.get(variable):
                                form_var_dict[variable] = form_data.get(variable)
                            else:
                                form_var_dict[variable] = render
                else:
                    form_var_dict[variable] = ''
            elif comptype in ['date', 'datetime', 'input']:  # 日期时间，使用eval也不会转换错
                if form_data and form_data.get(variable):
                    form_var_dict[variable] = form_data.get(variable)
                elif render:  #值渲染
                    if 'GetValueFromSQL' in render:
                        try:
                            form_var_dict[variable] = GetValueFromSQL(render, 'render')
                        except Exception as ex:
                            log.error('表单配置SQL错误:' + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
                            public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
                            public.respcode, public.respmsg = "100021", "表单配置项[%s]SQL错误!" % compitem['attrs'].get('label')
                            public.respinfo = HttpResponse(public.setrespinfo())
                            return public.respinfo
                    else:
                        if variable:
                            if form_data.get(variable):
                                form_var_dict[variable] = form_data.get(variable)
                            else:
                                form_var_dict[variable] = render
                else:
                    form_var_dict[variable] = ''
            else: #其它组件的变量初始化
                if render:  #值渲染
                    if 'GetValueFromSQL' in render:
                        try:
                            form_var_dict[variable] = GetValueFromSQL(render, 'render')
                        except Exception as ex:
                            log.error('表单配置SQL错误:' + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
                            public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
                            public.respcode, public.respmsg = "100021", "表单配置项[%s]SQL错误!" % compitem['attrs'].get('label')
                            public.respinfo = HttpResponse(public.setrespinfo())
                            return public.respinfo
                    else:
                        if variable:
                            if form_data.get(variable):
                                try:
                                    form_var_dict[variable] = eval( form_data.get(variable) )
                                except:
                                    form_var_dict[variable] = form_data.get(variable)
                            else:
                                form_var_dict[variable] = render
                else:
                    if variable:
                        if comptype in [ 'file_upload', 'img_upload' ]:  # 文件、图片上传。返回list
                            if form_data and form_data.get(variable):
                                try:
                                    form_var_dict[variable] = eval( form_data.get(variable) )
                                except:
                                    form_var_dict[variable] = form_data.get(variable)
                            else:
                                form_var_dict[variable] = ''
                        else:
                            # log.info('variable--:'+str(variable))
                            if form_data and form_data.get(variable):
                                try:
                                    form_var_dict[variable] = eval( form_data.get(variable) )
                                except:
                                    form_var_dict[variable] = form_data.get(variable)
                            else:
                                form_var_dict[variable] = form_var.get(variable)
                            # log.info('variable--b - e :' + str(type(form_data.get(variable))) +'---'  + str(type(form_var_dict.get(variable))) )

            #关键字段值转换
            if form_var_dict.get(variable):
                form_var_dict[variable] = keywords( form_var_dict[variable] )
        #把form_var中独有的变量，也加入到返回列表中。
        for item in form_var:
            if not form_var_dict.get(item):
                form_var_dict[item]=form_var[item]

        #把form_data中独有的变量，也加入到返回列表中。
        for item in form_data:
            if not form_var_dict.get(item):
                form_var_dict[item]=form_data[item]

        # del form_var_dict['selected[0].name']
        # del form_var_dict['selected[0].sex']
        # del form_var_dict['selected[0].age']

        cur.close()

    except Exception as ex:
        log.error("表单配置[%s]渲染失败!" % variable + str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100011", "表单配置渲染失败!"+str(variable)
        public.respinfo =  HttpResponse( public.setrespinfo() )
        return public.respinfo

    cur.close()  # 关闭游标
    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            # "form_cfg":form_cfg,
            "form_var":form_var_dict,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#表单配置查询，主要是获取form_id列表
def form_cfg_list( request ):
    log = public.logger
    body = public.req_body
    form_id = body.get('form_id', '')
    try:
        cur = connection.cursor()  # 创建游标
        sql = "select form_id, form_name, update_date from sys_form_cfg_info order by update_date desc, form_id desc"
        cur.execute(sql)
        rows = cur.fetchall()
        form_list=[]
        for item in rows:
            form_list.append({"label":str(item[0])+'  '+str(item[1])+'  修改时间：'+str(item[2]), "value":str(item[0])} )

        cur.close()  # 关闭游标
    except Exception as ex:
        log.error("表单配置信息查询失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "表单配置信息查询失败!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_list": form_list,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#表单中表格数据初始化,增加初始化表格数据的操作
def form_table_show( request ):
    log = public.logger
    body = public.req_body
    form_id = body.get('form_id')
    table_id = body.get('table_id')
    pageSize = body.get('pageSize', '9999')
    currentPage = body.get('currentPage', 1)
    search = body.get('search')
    form_var = body.get('form_var')
    if not form_id:
        public.respcode, public.respmsg = "100210", "表单ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not table_id:
        public.respcode, public.respmsg = "100211", "表格ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    try:
        cur = connection.cursor()  # 创建游标
        sql = "select form_cfg from sys_form_cfg_info where form_id = %s"
        log.info(sql % form_id, extra={'ptlsh': public.req_seq})
        cur.execute(sql, form_id)
        row = cur.fetchone()
        if not row:
            cur.close()  # 关闭游标
            public.respcode, public.respmsg = "100212", "表单配置不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        Layout_list = json.loads(row[0])

        def GetRealSQL(sql):
            pattern = re.compile("\$\[(.*?)\]")
            sqlvar = pattern.findall(sql)
            for sqlitm in sqlvar:
                old = "$[" + sqlitm + "]"
                if sqlitm in form_var.keys():
                    new = "'" + str(form_var.get(sqlitm)) + "'"
                else:
                    new = "''"
                sql = sql.replace(old, new)
            log.info('real sql=' + str(sql), extra={'ptlsh': public.req_seq})
            sql = public.SqlKeywordConver(sql, None)
            sql = sql.replace('data_seq_no', '1 as data_sql_no') #add by liltz,20201006, 'data_seq_no'关键字，按顺序排序
            log.info('finally sql=' + str(sql), extra={'ptlsh': public.req_seq})
            return sql

        # 递归获取表单中指定的表格组件
        def GetCompFormLayout(Layout_list, table_id):
            comp_cfg = {}
            for comp_item in Layout_list:
                if comp_item.get('children'):
                    comp_cfg = GetCompFormLayout(comp_item['children'], table_id)
                    if not comp_cfg:
                        continue
                    else:
                        return comp_cfg
                elif comp_item['type'] == 'null':
                    continue
                elif  comp_item['id']==table_id:
                    comp_cfg = comp_item
                    return comp_cfg
            return comp_cfg #没找到

        comp_cfg = GetCompFormLayout(Layout_list, table_id)
        log.info('comp_cfg='+str(comp_cfg), extra={'ptlsh': public.req_seq})
        if not comp_cfg:
            cur.close()  # 关闭游标
            public.respcode, public.respmsg = "100212", "表格配置信息不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        sqlselect = comp_cfg['attrs']['data_sql']
        sqlorder = comp_cfg['attrs']['orderby_manage']
        sqlwhere= comp_cfg['attrs']['where_manage']
        if not sqlwhere and "where" not in sqlselect.lower():
            sqlwhere=" where 1=1 "
        if search:
            for searchitem in search:
                if searchitem.get('a') and searchitem.get('to') and searchitem.get('b'):
                    if searchitem.get('to') == 'like': #补两个百分号
                        sqlwhere=sqlwhere+" and %s %s '%%%s%%' " % (searchitem['a'], searchitem['to'],searchitem['b'])
                    else:
                        sqlwhere = sqlwhere + " and %s %s '%s' " % (searchitem['a'], searchitem['to'], searchitem['b'])

        position_start = (currentPage-1) * pageSize
        position_end = currentPage * pageSize
        sqllimit = " limit %s, %s" % (position_start, pageSize)

        #获取记录总数
        sql = "%s %s" % (sqlselect, sqlwhere)
        sql = GetRealSQL(sql)
        sql = sql.lower()
        fieldlist = sql.split('select')[1].split('from')[0]
        sql = sql.replace(fieldlist, ' count(1) ')
        log.info('通用表格记录数查询sql:' + sql, extra={'ptlsh': public.req_seq})
        cur.execute(sql)
        row = cur.fetchone()
        body['table_total'] = row[0]

        #获取记录明细:
        sql = "%s %s %s %s" % (sqlselect, sqlwhere, sqlorder, sqllimit)
        selsql = GetRealSQL(sql)
        log.info('通用表格查询sql:' + selsql, extra={'ptlsh': public.req_seq})
        cur.execute(selsql)
        rows = cur.fetchall()
        table_data=[]
        data_seq_no= body['table_total']-(currentPage-1) * pageSize          #增加当前数据的序号（倒序)

        for item in rows:
            data_item={}
            i=0
            for fielditem in comp_cfg['attrs']['head']:
                # log.info('fielditem='+str(fielditem), extra={'ptlsh': public.req_seq})
                if fielditem.get('comp') == 'button': #按钮不赋值
                    continue
                if fielditem.get('name') == 'data_seq_no': #序号列，为虚列不控制
                    data_item['data_seq_no'] = data_seq_no
                    data_seq_no = data_seq_no - 1
                    i = i + 1
                    continue
                try:
                    data_item[ fielditem['name'] ]=item[i]
                    i=i+1
                except Exception as ex:
                    log.info( str(ex) )
                    break; #HEAD字段数量和SQL查询的字段不一致时，后边的不管了。

            table_data.append(data_item)

        dict_data={}
        if len(table_data) > 0: #有数据，先把表头字段对应的数据字典查出来
            for fielditem in comp_cfg['attrs']['head']:
                # log.info('fielditem='+str(fielditem), extra={'ptlsh': public.req_seq})
                morecfg=fielditem.get('moreConfig')
                if morecfg and morecfg.get('data_dict'):  # 按钮不赋值
                    try:
                        data_item=[]
                        dictsql=morecfg.get('data_dict')
                        cur.execute( dictsql )
                        dictrows=cur.fetchall()
                        for dictitem in dictrows:
                            data_item.append( {"key":dictitem[0], "value":dictitem[1]} )

                        dict_data[fielditem['name']] = data_item
                    except Exception as ex:
                        log.info(str(ex))
                        pass
        body['dict_data'] = []
        body['dict_data'].append(dict_data)

        #数据字典转换一下
        for dataitm in table_data:
            for subdictitm in dataitm:
                # print('subdictitm=',subdictitm, dictitm[subdictitm])
                if subdictitm in dict_data.keys():
                    tmpvalue = dataitm[subdictitm]
                    # print('tmpkey=', subdictitm, 'tmpvalue=', tmpvalue)
                    for subtmp in dict_data.get(subdictitm):
                        # print('subtmp=', subtmp)
                        if tmpvalue == subtmp.get('key'):
                            res = '%s-%s' % (tmpvalue, subtmp.get('value'))
                            dataitm[subdictitm] = res
                            # print('is ok', 'tmpkey=', subdictitm, 'tmpvalue=', res)
                            break;
        # print(table_data)
        body['table_data'] = table_data

        cur.close()  # 关闭游标

    except Exception as ex:
        log.error("表单配置信息查询失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
        public.respcode, public.respmsg = "100010", "表单配置信息查询失败!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


#表单中配置时, 返回公共数据字典列表
def form_table_dict_list( request ):
    log = public.logger
    body = public.req_body

    try:
        cur = connection.cursor()  # 创建游标
        sql = "select distinct DICT_NAME, DICT_SNOTE from sys_ywty_dict where dict_public_flag='Y'"
        cur.execute( sql )
        rows = cur.fetchall()

        dict_list=[]
        for item in rows:
            data_item={
                "key": item[0],
                "value": item[1],
            }
            dict_list.append(data_item)
        body['dict_list'] = dict_list
        cur.close()  # 关闭游标

    except Exception as ex:
        log.error("表单配置信息查询失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
        public.respcode, public.respmsg = "100010", "表单配置信息查询失败!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#表单中配置时, 返回数据字典键值
def form_table_dict_info( request ):
    log = public.logger
    body = public.req_body
    dict_name = body.get('dict_name')
    if not dict_name:
        public.respcode, public.respmsg = "100281", "字典名称不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        sql = "select dict_code,dict_target from sys_ywty_dict where dict_name=%s"
        cur.execute( sql, dict_name )
        rows = cur.fetchall()

        dict_info = []
        for item in rows:
            data_item = {
                "key": item[0],
                "value": item[1],
            }
            dict_info.append(data_item)
        body['dict_info'] = dict_info
        cur.close()  # 关闭游标

    except Exception as ex:
        log.error("表单配置信息查询失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
        public.respcode, public.respmsg = "100010", "表单配置信息查询失败!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


def button_table_show( request ):
    log = public.logger
    body = public.req_body
    form_id = body.get('form_id')
    form_var = body.get('form_var')
    table_id = form_var.get('tabledata')
    pageSize = body.get('pageSize', '9999')
    currentPage = body.get('currentPage', 1)
    search = body.get('search')
    form_var = body.get('form_var')
    if not form_id:
        public.respcode, public.respmsg = "100210", "表单ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not table_id:
        public.respcode, public.respmsg = "100211", "表格ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    try:
        cur = connection.cursor()  # 创建游标
        sql = "select form_cfg from sys_form_cfg_info where form_id = %s"
        log.info(sql % form_id, extra={'ptlsh': public.req_seq})
        cur.execute(sql, form_id)
        row = cur.fetchone()
        if not row:
            cur.close()  # 关闭游标
            public.respcode, public.respmsg = "100212", "表单配置不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        Layout_list = json.loads(row[0])

        def GetRealSQL(sql):
            pattern = re.compile("\$\[(.*?)\]")
            sqlvar = pattern.findall(sql)
            for sqlitm in sqlvar:
                old = "$[" + sqlitm + "]"
                if sqlitm in form_var.keys():
                    new = "'" + str(form_var.get(sqlitm)) + "'"
                else:
                    new = "''"
                sql = sql.replace(old, new)
            log.info('real sql=' + str(sql), extra={'ptlsh': public.req_seq})
            sql = public.SqlKeywordConver(sql, None)
            sql = sql.replace('data_seq_no', '1 as data_sql_no') #add by liltz,20201006, 'data_seq_no'关键字，按顺序排序
            log.info('finally sql=' + str(sql), extra={'ptlsh': public.req_seq})
            return sql

        # 递归获取表单中指定的表格组件
        def GetCompFormLayout(Layout_list, table_id):
            comp_cfg = {}
            for comp_item in Layout_list:
                if comp_item.get('children'):
                    comp_cfg = GetCompFormLayout(comp_item['children'], table_id)
                    if not comp_cfg:
                        continue
                    else:
                        return comp_cfg
                elif comp_item['type'] == 'null':
                    continue
                elif  comp_item['id']==table_id:
                    comp_cfg = comp_item
                    return comp_cfg
            return comp_cfg #没找到

        comp_cfg = GetCompFormLayout(Layout_list, table_id)
        log.info('comp_cfg='+str(comp_cfg), extra={'ptlsh': public.req_seq})
        if not comp_cfg:
            cur.close()  # 关闭游标
            public.respcode, public.respmsg = "100212", "表格配置信息不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        sqlselect = comp_cfg['attrs']['data_sql']
        sqlorder = comp_cfg['attrs']['orderby_manage']
        sqlwhere= comp_cfg['attrs']['where_manage']
        if not sqlwhere and "where" not in sqlselect.lower():
            sqlwhere=" where 1=1 "
        if search:
            for searchitem in search:
                if searchitem.get('a') and searchitem.get('to') and searchitem.get('b'):
                    if searchitem.get('to') == 'like': #补两个百分号
                        sqlwhere=sqlwhere+" and %s %s '%%%s%%' " % (searchitem['a'], searchitem['to'],searchitem['b'])
                    else:
                        sqlwhere = sqlwhere + " and %s %s '%s' " % (searchitem['a'], searchitem['to'], searchitem['b'])

        position_start = (currentPage-1) * pageSize
        position_end = currentPage * pageSize
        sqllimit = " limit %s, %s" % (position_start, pageSize)

        #获取记录总数
        sql = "%s %s" % (sqlselect, sqlwhere)
        sql = GetRealSQL(sql)
        sql = sql.lower()
        fieldlist = sql.split('select')[1].split('from')[0]
        sql = sql.replace(fieldlist, ' count(1) ')
        log.info('通用表格记录数查询sql:' + sql, extra={'ptlsh': public.req_seq})
        cur.execute(sql)
        row = cur.fetchone()
        body['table_total'] = row[0]

        #获取记录明细:
        sql = "%s %s %s %s" % (sqlselect, sqlwhere, sqlorder, sqllimit)
        selsql = GetRealSQL(sql)
        log.info('通用表格查询sql:' + selsql, extra={'ptlsh': public.req_seq})
        cur.execute(selsql)
        rows = cur.fetchall()
        table_data=[]
        data_seq_no= body['table_total']-(currentPage-1) * pageSize          #增加当前数据的序号（倒序)

        for item in rows:
            data_item={}
            i=0
            for fielditem in comp_cfg['attrs']['head']:
                # log.info('fielditem='+str(fielditem), extra={'ptlsh': public.req_seq})
                if fielditem.get('comp') == 'button': #按钮不赋值
                    continue
                if fielditem.get('name') == 'data_seq_no': #序号列，为虚列不控制
                    data_item['data_seq_no'] = data_seq_no
                    data_seq_no = data_seq_no - 1
                    i = i + 1
                    continue
                try:
                    data_item[ fielditem['name'] ]=item[i]
                    i=i+1
                except Exception as ex:
                    log.info( str(ex) )
                    break; #HEAD字段数量和SQL查询的字段不一致时，后边的不管了。

            table_data.append(data_item)

        dict_data={}
        if len(table_data) > 0: #有数据，先把表头字段对应的数据字典查出来
            for fielditem in comp_cfg['attrs']['head']:
                # log.info('fielditem='+str(fielditem), extra={'ptlsh': public.req_seq})
                morecfg=fielditem.get('moreConfig')
                if morecfg and morecfg.get('data_dict'):  # 按钮不赋值
                    try:
                        data_item=[]
                        dictsql=morecfg.get('data_dict')
                        cur.execute( dictsql )
                        dictrows=cur.fetchall()
                        for dictitem in dictrows:
                            data_item.append( {"key":dictitem[0], "value":dictitem[1]} )

                        dict_data[fielditem['name']] = data_item
                    except Exception as ex:
                        log.info(str(ex))
                        pass
        body['dict_data'] = []
        body['dict_data'].append(dict_data)

        #数据字典转换一下
        for dataitm in table_data:
            for subdictitm in dataitm:
                # print('subdictitm=',subdictitm, dictitm[subdictitm])
                if subdictitm in dict_data.keys():
                    tmpvalue = dataitm[subdictitm]
                    # print('tmpkey=', subdictitm, 'tmpvalue=', tmpvalue)
                    for subtmp in dict_data.get(subdictitm):
                        # print('subtmp=', subtmp)
                        if tmpvalue == subtmp.get('key'):
                            res = '%s-%s' % (tmpvalue, subtmp.get('value'))
                            dataitm[subdictitm] = res
                            # print('is ok', 'tmpkey=', subdictitm, 'tmpvalue=', res)
                            break;
        # print(table_data)
        body['table_data'] = table_data

        cur.close()  # 关闭游标

    except Exception as ex:
        log.error("表单配置信息查询失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        cur.close()  # 关闭游标
        public.respcode, public.respmsg = "100010", "表单配置信息查询失败!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo
