import sys
from django.shortcuts import HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime

###########################################################################################################
#用户信息、角色信息、角色菜单权限、角色字段权限、用户菜单权限、用户字段权限、实际机构信息、虚拟机构信息、用户机构关系
#获取用户权限、校验用户权限
#add by litz, 20200411
#
###########################################################################################################

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

#用户权限管理-新增或修改角色
def role_cfg_save( request ):
    log = public.logger
    body=public.req_body
    form_var=body.get('form_var')
    role_id = form_var.get('role_id')
    role_name = form_var.get('role_name')
    role_above_id = form_var.get('role_above_id')
    role_desc = form_var.get('role_desc')
    selectedKeys = form_var.get('selectedKeys')
    # log.info('role_id='+str(role_id), extra={'ptlsh':public.req_seq})
    if not role_id:
        public.respcode, public.respmsg = "100221", "角色ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not role_above_id:
        public.respcode, public.respmsg = "100221", "上级角色不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not role_name:
        public.respcode, public.respmsg = "100221", "角色名称不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    # if body.get('ROLE_ABOVE_ID'):
    #     public.respcode, public.respmsg = "100221", "所属角色不可为空!"
    #     public.respinfo = HttpResponse(public.setrespinfo())
    #     return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标

        # 查询上级角色信息是否存在
        sql = "select role_name from sys_role where role_id=%s "
        cur.execute(sql, (role_above_id) )
        row = cur.fetchone()
        if not row:
            public.respcode, public.respmsg = "100221", "上级角色不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        #查询角色信息是否自己创建
        sql="select role_name from sys_role where role_id=%s"
        cur.execute(sql, (role_id) )
        row=cur.fetchone()
        if row:
            # 更新角色信息表
            sql = "update sys_role set role_name=%s, role_state=%s, snote=%s where role_id=%s "
            log.info(sql % (role_name, '1', role_desc, role_id), extra={'ptlsh': public.req_seq})
            cur.execute(sql, (role_name, '1', role_desc, role_id) )
        else:
            # 插入角色信息表
            sql="insert into sys_role(role_id,role_name,role_above_id,role_state,operate_userid, snote) " \
                "values(%s, %s, %s, %s, %s, %s)"
            log.info(sql % ( role_id, role_name, role_above_id, '1', public.user_id,  role_desc) , extra={'ptlsh':public.req_seq})
            cur.execute(sql, ( role_id, role_name, role_above_id, '1', public.user_id,  role_desc) )

        #清空原表数据
        sql="delete from sys_role_purv_head where role_id=%s"
        cur.execute(sql, (role_id) )

        #登记角色权限明细信息
        if selectedKeys:
            for item in selectedKeys:
                if '-' in str(item):
                    menu_id = int(str(item).split('-')[0])
                    submenu_id = int(str(item).split('-')[1])
                else:
                    menu_id = int(item)
                    submenu_id = 0
                log.info('menuid=%s,submenuid=%s' % (menu_id, submenu_id), extra={'ptlsh':public.req_seq})
                # 获取菜单类型和APPID
                sql = "select menu_path, app_id from sys_menu where menu_id= %s "
                log.info( sql % menu_id , extra={'ptlsh': public.req_seq})
                cur.execute(sql, menu_id)
                row = cur.fetchone()
                if not row:  # 菜单不存在？？不可能
                    continue
                menu_path = row[0]
                app_id = row[1]

                if menu_path in ['cruddata','cruddata2'] and str(submenu_id) != '0':
                    auth_flag='Y' #是否有字段权限配置。
                else:
                    auth_flag='N'
                # 菜单交易，登记角色权限表
                sql = "insert into sys_role_purv_head( role_id, menu_id, app_id, auth_type, auth_flag ) values( %s, %s, %s, %s, %s)"
                log.info(sql % (role_id, menu_id, app_id, submenu_id,auth_flag), extra={'ptlsh': public.req_seq})
                cur.execute(sql,(role_id, menu_id, app_id, submenu_id,auth_flag))

        cur.close()

    except Exception as ex:
        log.error("插入数据表信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        if  'Duplicate' in  str(ex) and 'PRIMARY' in str(ex):
            public.respcode, public.respmsg = "100200", "角色信息已存在!"
        else:
            public.respcode, public.respmsg = "100200", "登记角色权限表失败!" + str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "角色添加成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body,
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


#用户权限管理-新增或修改角色
def role_cfg_create( request ):
    log = public.logger
    body=public.req_body
    form_var=body.get('form_var')
    role_id = form_var.get('role_id')
    role_name = form_var.get('role_name')
    role_above_id = form_var.get('role_above_id')
    role_desc = form_var.get('role_desc')
    selectedKeys = form_var.get('selectedKeys')
    # log.info('role_id='+str(role_id), extra={'ptlsh':public.req_seq})
    if not role_id:
        public.respcode, public.respmsg = "100221", "角色ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not role_above_id:
        public.respcode, public.respmsg = "100221", "上级角色不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not role_name:
        public.respcode, public.respmsg = "100221", "角色名称不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    # if body.get('ROLE_ABOVE_ID'):
    #     public.respcode, public.respmsg = "100221", "所属角色不可为空!"
    #     public.respinfo = HttpResponse(public.setrespinfo())
    #     return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标

        # 查询上级角色信息是否存在
        sql = "select role_name from sys_role where role_id=%s "
        cur.execute(sql, (role_above_id) )
        row = cur.fetchone()
        if not row:
            public.respcode, public.respmsg = "100221", "上级角色不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        #查询角色信息是否自己创建
        sql="select role_name from sys_role where role_id=%s"
        cur.execute(sql, (role_id) )
        row=cur.fetchone()
        if row:
            # 更新角色信息表
            sql = "update sys_role set role_name=%s, role_state=%s, snote=%s where role_id=%s "
            log.info(sql % (role_name, '1', role_desc, role_id), extra={'ptlsh': public.req_seq})
            cur.execute(sql, (role_name, '1', role_desc, role_id) )
        else:
            # 插入角色信息表
            sql="insert into sys_role(role_id,role_name,role_above_id,role_state,operate_userid, snote) " \
                "values(%s, %s, %s, %s, %s, %s)"
            log.info(sql % ( role_id, role_name, role_above_id, '1', public.user_id,  role_desc) , extra={'ptlsh':public.req_seq})
            cur.execute(sql, ( role_id, role_name, role_above_id, '1', public.user_id,  role_desc) )

        #清空原表数据
        sql="delete from sys_role_purv_head where role_id=%s"
        cur.execute(sql, (role_id) )

        #登记角色权限明细信息
        if selectedKeys:
            for item in selectedKeys:
                if '-' in str(item):
                    menu_id = int(str(item).split('-')[0])
                    submenu_id = int(str(item).split('-')[1])
                else:
                    menu_id = int(item)
                    submenu_id = 0
                log.info('menuid=%s,submenuid=%s' % (menu_id, submenu_id), extra={'ptlsh':public.req_seq})
                # 获取菜单类型和APPID
                sql = "select menu_path, app_id from sys_menu where menu_id= %s "
                log.info( sql % menu_id , extra={'ptlsh': public.req_seq})
                cur.execute(sql, menu_id)
                row = cur.fetchone()
                if not row:  # 菜单不存在？？不可能
                    continue
                menu_path = row[0]
                app_id = row[1]

                if menu_path in ['cruddata','cruddata2'] and str(submenu_id) != '0':
                    auth_flag='Y' #是否有字段权限配置。
                else:
                    auth_flag='N'
                # 菜单交易，登记角色权限表
                sql = "insert into sys_role_purv_head( role_id, menu_id, app_id, auth_type, auth_flag ) values( %s, %s, %s, %s, %s)"
                log.info(sql % (role_id, menu_id, app_id, submenu_id,auth_flag), extra={'ptlsh': public.req_seq})
                cur.execute(sql,(role_id, menu_id, app_id, submenu_id,auth_flag))

        cur.close()

    except Exception as ex:
        log.error("插入数据表信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        if  'Duplicate' in  str(ex) and 'PRIMARY' in str(ex):
            public.respcode, public.respmsg = "100200", "角色信息已存在!"
        else:
            public.respcode, public.respmsg = "100200", "登记角色权限表失败!" + str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "角色添加成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body,
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


#用户权限管理-角色字段权限登记
def role_fieldcfg_create( request ):
    log = public.logger
    body=public.req_body
    role_id = body.get('role_id')
    cfg_id = body.get('cfg_id')
    app_id = body.get('app_id')
    form_id = body.get('form_id')
    field_power = body.get('cfg_data')

    if '-' in str(cfg_id):
        menu_id = int(str(cfg_id).split('-')[0])
        submenu_id = int(str(cfg_id).split('-')[1])
    else:
        menu_id = int(cfg_id)
        submenu_id = 0

    if not role_id:
        public.respcode, public.respmsg = "100223", "角色ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not menu_id:
        public.respcode, public.respmsg = "100224", "菜单不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not form_id:
        form_id = '0'

    def fieldpower_2_authflag(power):
        if "显示" in itm['power']:
            show_able = 'Y'
        else:
            show_able = 'N'
        if "置灰" in itm['power']:
            dis_able = 'Y'
        else:
            dis_able = 'N'
        return show_able, dis_able
    try:
        cur = connection.cursor()  # 创建游标
        sql="select app_id, menu_path from sys_menu where menu_id=%s "
        cur.execute(sql, menu_id)
        row = cur.fetchone()
        if not row:  # 菜单不存在？？不可能
            cur.close()
            public.respcode, public.respmsg = "100225", "菜单不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        menu_path = row[0]
        # app_id = row[1]
        # 清空原表数据
        sql = "delete from sys_role_purv_body where role_id=%s and menu_id=%s and app_id=%s and form_id=%s "
        insert_tuple = (role_id, menu_id, app_id, form_id)
        log.info(sql % insert_tuple, extra={'ptlsh': public.req_seq})
        cur.execute(sql, insert_tuple)

        for itm in field_power:
            # 插入角色字段权限表
            field_id=itm['name']
            field_name = itm['label']
            show_able, dis_able = fieldpower_2_authflag(itm['power'])
            sql = "insert into sys_role_purv_body(role_id, menu_id, app_id, form_id, field_id, field_name, show_able, dis_able) " \
                  " values( %s, %s, %s, %s, %s, %s, %s, %s )"
            insert_tuple=(role_id, menu_id, app_id, form_id, field_id, field_name, show_able, dis_able)
            log.info(sql % insert_tuple, extra={'ptlsh':public.req_seq})
            cur.execute(sql, insert_tuple)

        cur.close()

    except Exception as ex:
        log.error("插入角色字段权限登记表失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        if  'Duplicate' in  str(ex) and 'PRIMARY' in str(ex):
            public.respcode, public.respmsg = "100200", "违反唯一约束!"
        else:
            public.respcode, public.respmsg = "100200", "登记角色字段权限登记表失败!" + str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "角色字段权限维护成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body,
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#用户权限管理-用户角色字段权限登记
def role_fieldcfg_select( request ):
    log = public.logger
    body=public.req_body
    role_id = body.get('role_id')
    role_above_id = body.get('role_above_id')
    cfg_id = body.get('cfg_id')

    app_id = body.get('app_id')
    form_id = body.get('form_id') #一般都是空的

    if '-' in str(cfg_id):
        menu_id = int(str(cfg_id).split('-')[0])
        submenu_id = int(str(cfg_id).split('-')[1])
    else:
        menu_id = int(cfg_id)
        submenu_id = 0

    if not role_id:
        public.respcode, public.respmsg = "100223", "角色ID不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not menu_id:
        public.respcode, public.respmsg = "100224", "菜单不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    def authflag_2_fieldpower(show_flag, dis_flag):
        power=[]
        if show_flag == 'Y':
            power.append('显示')
        if dis_flag == 'Y':
            power.append('置灰')
        return power

    #获取超级用户的所有权限
    def get_field_name_byroot( formid,appid):
        if formid:
            sql="select field_id,IFNULL(field_name,'表格数据'),show_able,dis_able from sys_form_cfg_fieldlist " \
                "where form_id=%s and FIELD_ID!=''"
            cur.execute(sql, formid)
            rows = cur.fetchall()
            return rows
        elif appid:
            sql="select field_id, field_name, state, case edit_able when 'N' then 'Y' else 'N' end 'dis_able' " \
                "from sys_crud_cfg_body where app_id=%s "
            cur.execute(sql, appid)
            rows = cur.fetchall()
            return rows
        else:
            return None

    try:
        cur = connection.cursor()  # 创建游标

        if not app_id:  # appID为空,根据menuid去查
            sql = "select app_id,menu_type,menu_path from sys_menu where menu_id='%s'" % menu_id
            cur.execute( sql )
            row = cur.fetchone()
            if not row:
                cur.close()
                public.respcode, public.respmsg = "100234", "菜单配置不完整!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            if row[2] == 'displaypage': #表单
                app_id = row[0]
                form_id = row[0]
            else: #'cruddata', 'cruddata2'  暂不支持此配置
                cur.close()
                public.respcode, public.respmsg = "100244", "暂不支持此配置!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

        if role_id=='root': #超级角色？？
            rows = get_field_name_byroot( form_id,app_id)
        else:
            #查询本角色的权限字段配置
            sql = "select field_id, field_name, show_able, dis_able from sys_role_purv_body " \
                  "where role_id=%s and menu_id=%s and app_id=%s and form_id=%s "
            insert_tuple = (role_id, menu_id, app_id, form_id)
            log.info(sql % insert_tuple, extra={'ptlsh': public.req_seq})
            cur.execute(sql, insert_tuple)
            rows=cur.fetchall()

        if not rows: #没配置过，查上一级的角色权限
            if role_above_id == 'root' or role_above_id=='':  # 超级角色？？
                rows = get_field_name_byroot(form_id, app_id)
            else:
                sql = "select field_id, field_name, show_able, dis_able from sys_role_purv_body " \
                     "where role_id=%s and menu_id=%s and app_id=%s and form_id=%s "
                insert_tuple = (role_above_id, menu_id, app_id, form_id)
                log.info(sql % insert_tuple, extra={'ptlsh': public.req_seq})
                cur.execute(sql, insert_tuple)
                rows = cur.fetchall()

        field_power = []
        for item in rows:
            field_power.append({"name":item[0], "label": item[1], "power": authflag_2_fieldpower(item[2], item[3]) })
        cur.close()

    except Exception as ex:
        log.error("查询角色字段权限表失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "查询角色字段权限表失败!" + str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "查询角色字段权限成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "role_id": role_id,
            "cfg_id": menu_id,
            "field_power": field_power
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#用户权限管理-上级角色信息查询
def aboverole_cfg_select( request ):
    log = public.logger
    body=public.req_body
    form_var = body['form_var']
    role_above_id = form_var.get('role_above_id')
    role_id = form_var.get('role_id')

    # 获取菜单角色列表,所有权限
    def GetMenuTreeData_ByRoot(menuid):
        log = public.logger
        MenuTreeData = []

        sql = "select a.menu_id, a.menu_name, a.is_run_menu, a.app_id, menu_path " \
              "from sys_menu a  where a.above_menu_id ='%s' order by a.order_id asc" % (menuid)
        # log.info("获取菜单角色列表:" + sql, extra={'ptlsh': public.req_seq})

        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            menuinfo = {}
            menu_id = item[0]
            menu_name = item[1]
            is_run_menu = item[2]
            menuinfo['id'] = str(menu_id)
            menuinfo['label'] = str(menu_id) + '-' + str(menu_name)
            if is_run_menu != 'Y':  # 非功能菜单，就是目录菜单
                menuinfo['menu_type'] = 'CONTENTS'
                menuinfo['field_power'] = False
                menuinfo['children'] = GetMenuTreeData_ByRoot(menu_id)
            else:  # 功能菜单,获取功能操作权限和字段权限
                menuinfo['menu_type'] = 'RUN_MENU'  # 功能菜单
                authlist = []
                app_id = item[3]
                menu_path = item[4]
                if menu_path == 'cruddata':
                    # 一代增删改查配置
                    sql = "select insert_able,delete_able,update_able,import_able,export_able from irsadmin_db_tran_reg " \
                          "where app_id='%s'" % app_id
                    cur.execute(sql)
                    crud_head = cur.fetchone()
                    if crud_head:
                        if crud_head[0] == 'Y':
                            authlist.append(
                                {"id": str(menu_id) + '-1', "label": str(menu_id) + '-1 ' + "添加数据", "app_id": app_id,
                                 "form_id": "", "field_power": True})
                        if crud_head[1] == 'Y':
                            authlist.append(
                                {"id": str(menu_id) + '-2', "label": str(menu_id) + '-2 ' + "删除数据", "app_id": app_id,
                                 "form_id": "", "field_power": True})
                        if crud_head[2] == 'Y':
                            authlist.append(
                                {"id": str(menu_id) + '-3', "label": str(menu_id) + '-3 ' + "更新数据", "app_id": app_id,
                                 "form_id": "", "field_power": True})
                        if crud_head[3] == 'Y':
                            authlist.append(
                                {"id": str(menu_id) + '-4', "label": str(menu_id) + '-4 ' + "导入数据", "app_id": app_id,
                                 "form_id": "", "field_power": False})
                        if crud_head[4] == 'Y':
                            authlist.append(
                                {"id": str(menu_id) + '-5', "label": str(menu_id) + '-5 ' + "导出数据", "app_id": app_id,
                                 "form_id": "", "field_power": False})

                    sql = "select field_id, FIELD_NAME, STATE, EDIT_ABLE from irsadmin_db_tran_list  " \
                          "where app_id='%s' order by order_id asc" % app_id
                    cur.execute(sql)
                    crud_body = cur.fetchone()
                    menuinfo['children'] = authlist
                    if crud_body:
                        menuinfo['field_power'] = True
                    else:
                        menuinfo['field_power'] = False
                elif menu_path == 'cruddata2':
                    # 二代增删改查配置
                    sql = "select insert_formid,delete_formid,update_formid,import_formid,export_formid from sys_crud_cfg_head " \
                          "where app_id='%s'" % app_id
                    # log.info("二代增删改查配置:" + sql, extra={'ptlsh': public.req_seq})
                    cur.execute(sql)
                    crud2_head = cur.fetchone()
                    if crud2_head:
                        if crud2_head[0]:
                            authlist.append(
                                {"id": str(menu_id) + '-1', "label": str(menu_id) + '-1 ' + "添加数据", "app_id": app_id,
                                 "form_id": crud2_head[0], "children": [], "field_power": True})
                        if crud2_head[1]:
                            authlist.append(
                                {"id": str(menu_id) + '-2', "label": str(menu_id) + '-2 ' + "删除数据", "app_id": app_id,
                                 "form_id": crud2_head[1], "children": [], "field_power": True})
                        if crud2_head[2]:
                            authlist.append(
                                {"id": str(menu_id) + '-3', "label": str(menu_id) + '-3 ' + "修改数据", "app_id": app_id,
                                 "form_id": crud2_head[2], "children": [], "field_power": True})
                        if crud2_head[3]:
                            authlist.append(
                                {"id": str(menu_id) + '-4', "label": str(menu_id) + '-4 ' + "导入数据", "app_id": app_id,
                                 "form_id": crud2_head[3], "children": [], "field_power": True})
                        if crud2_head[4]:
                            authlist.append(
                                {"id": str(menu_id) + '-5', "label": str(menu_id) + '-5 ' + "导出数据", "app_id": app_id,
                                 "form_id": crud2_head[4], "children": [], "field_power": True})
                    menuinfo['children'] = authlist
                else:
                    # 暂无配置功能，不返回具体权限
                    menuinfo["field_power"] = False
            MenuTreeData.append(menuinfo)

        # 返回结果
        return MenuTreeData

    # 获取菜单角色列表,所有权限
    def GetMenuTreeData_ByRole(roleid, menuid):
        log = public.logger
        MenuTreeData = []

        # 根据菜单子码获取子码标签
        def submenu2value(submenuid):
            if submenuid == 0:
                return "查询数据"
            elif submenuid == 1:
                return "添加数据"
            elif submenuid == 2:
                return "删除数据"
            elif submenuid == 3:
                return "更新数据"
            elif submenuid == 4:
                return "导入数据"
            elif submenuid == 5:
                return "导出数据"
            else:
                return ''

        # 根据菜单APPID获取FormID
        # def GetFormId_ByMenuApp(menuid,appid):
        #     if '-' in str(menuid):
        #         menu_id = int(str(menuid).split('-')[0])
        #         submenu_id = int(str(menuid).split('-')[1])
        #     else:
        #         menu_id = int(menuid)
        #         submenu_id = 0

        sql = "select a.menu_id, a.menu_name, a.is_run_menu, a.app_id, menu_path " \
              "from sys_menu a  where a.above_menu_id ='%s' " % (menuid)
        log.info("获取菜单角色列表:" + sql, extra={'ptlsh': public.req_seq})

        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            menuinfo = {}
            menu_id = item[0]
            menu_name = item[1]
            is_run_menu = item[2]
            menuinfo['id'] = str(menu_id)
            menuinfo['label'] = str(menu_id) + '-' + str(menu_name)
            if is_run_menu != 'Y':  # 非功能菜单，就是目录菜单
                menuinfo['menu_type'] = 'CONTENTS'
                menuinfo['field_power'] = False
                menuinfo['children'] = GetMenuTreeData_ByRole(roleid, menu_id)
                if len(menuinfo['children']) == 0:  # 空节点不再管它
                    continue
            else:  # 功能菜单,获取功能操作权限和字段权限
                menuinfo['menu_type'] = 'RUN_MENU'  # 功能菜单
                authlist = []
                app_id = item[3]
                menu_path = item[4]

                sql = "select menu_id,app_id,auth_type,auth_flag from sys_role_purv_head " \
                      "where role_id='%s' and menu_id like '%s-%%'" % (roleid, menu_id)
                cur.execute(sql)
                crud_head = cur.fetchall()
                for crud_item in crud_head:
                    if '-' in str(crud_item[0]):
                        menu_id = int(str(crud_item[0]).split('-')[0])
                        submenu_id = int(str(crud_item[0]).split('-')[1])
                    else:
                        menu_id = int(crud_item[0])
                        submenu_id = 0
                    authlist.append({"id": str(crud_item[0]), "label": str(crud_item[0]) + submenu2value(submenu_id),
                                     "app_id": str(app_id), "form_id": "", "field_power": public.Y2True(crud_item[3])})
            MenuTreeData.append(menuinfo)

        # 返回结果
        return MenuTreeData

    try:
        cur = connection.cursor()  # 创建游标
        sql="select ROLE_ID,ROLE_NAME,ROLE_ABOVE_ID,ROLE_STATE,OPERATE_USERID,OPERATE_DATETIME,SNOTE from sys_role where role_id=%s"
        if role_above_id:
            log.info("查询超级角色权限:"+sql % (role_above_id), extra={'ptlsh': public.req_seq})
            cur.execute(sql, (role_above_id))
        else:
            public.respcode, public.respmsg = "200311", "查询条件不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            cur.close()
            return public.respinfo

        row=cur.fetchone()
        if not row:
            public.respcode, public.respmsg = "200312", "角色信息不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if role_above_id == 'root':
            tree_data = GetMenuTreeData_ByRoot('root')
        else:
            tree_data = GetMenuTreeData_ByRole(role_above_id, 'root')

        cur.close()

    except Exception as ex:
        log.error("查询数据表信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "查询数据表信息失败!" + str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "角色查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":body.get('form_id'),
            "form_var":{
                "role_id": form_var.get('role_id'),
                "role_name": form_var.get('role_name'),
                "role_above_id": form_var.get('role_above_id'),
                "snote": form_var.get('snote'),
                "root_role_option": form_var.get('root_role_option'),
                "tree_data": tree_data
            },
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#用户权限管理-当前角色信息查询
def role_cfg_select( request ):
    log = public.logger
    body=public.req_body
    form_var = body['form_var']
    role_id = form_var.get('role_id')
    above_role_id = form_var.get('role_above_id')

    # 获取菜单角色列表,所有权限
    def GetMenuTreeData_ByRoot(menuid):
        log = public.logger
        MenuTreeData = []

        sql = "select a.menu_id, a.menu_name, a.is_run_menu, a.app_id, menu_path " \
              "from sys_menu a  where a.above_menu_id ='%s' order by a.order_id asc" % (menuid)
        # log.info("获取菜单角色列表:" + sql, extra={'ptlsh': public.req_seq})

        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            menuinfo = {}
            menu_id = item[0]
            menu_name = item[1]
            is_run_menu = item[2]
            menuinfo['id'] = str(menu_id)
            menuinfo['label'] = str(menu_id) + '-' + str(menu_name)
            if is_run_menu != 'Y':  # 非功能菜单，就是目录菜单
                menuinfo['menu_type'] = 'CONTENTS'
                menuinfo['field_power'] = False
                menuinfo['children'] = GetMenuTreeData_ByRoot(menu_id)
            else:  # 功能菜单,获取功能操作权限和字段权限
                menuinfo['menu_type'] = 'RUN_MENU'  # 功能菜单
                authlist = []
                app_id = item[3]
                menu_path = item[4]
                if menu_path == 'cruddata':
                    # 一代增删改查配置
                    sql = "select insert_able,delete_able,update_able,import_able,export_able from irsadmin_db_tran_reg " \
                          "where app_id='%s'" % app_id
                    cur.execute(sql)
                    crud_head = cur.fetchone()
                    if crud_head:
                        if crud_head[0] == 'Y':
                            authlist.append(
                                {"id": str(menu_id) + '-1', "label": str(menu_id) + '-1 ' + "添加数据", "app_id": app_id,
                                 "form_id": "", "field_power": True})
                        if crud_head[1] == 'Y':
                            authlist.append(
                                {"id": str(menu_id) + '-2', "label": str(menu_id) + '-2 ' + "删除数据", "app_id": app_id,
                                 "form_id": "", "field_power": True})
                        if crud_head[2] == 'Y':
                            authlist.append(
                                {"id": str(menu_id) + '-3', "label": str(menu_id) + '-3 ' + "更新数据", "app_id": app_id,
                                 "form_id": "", "field_power": True})
                        if crud_head[3] == 'Y':
                            authlist.append(
                                {"id": str(menu_id) + '-4', "label": str(menu_id) + '-4 ' + "导入数据", "app_id": app_id,
                                 "form_id": "", "field_power": False})
                        if crud_head[4] == 'Y':
                            authlist.append(
                                {"id": str(menu_id) + '-5', "label": str(menu_id) + '-5 ' + "导出数据", "app_id": app_id,
                                 "form_id": "", "field_power": False})

                    sql = "select field_id, FIELD_NAME, STATE, EDIT_ABLE from irsadmin_db_tran_list  " \
                          "where app_id='%s' order by order_id asc" % app_id
                    cur.execute(sql)
                    crud_body = cur.fetchone()
                    menuinfo['children'] = authlist
                    if crud_body:
                        menuinfo['field_power'] = True
                    else:
                        menuinfo['field_power'] = False
                elif menu_path == 'cruddata2':
                    # 二代增删改查配置
                    sql = "select insert_formid,delete_formid,update_formid,import_formid,export_formid from sys_crud_cfg_head " \
                          "where app_id='%s'" % app_id
                    # log.info("二代增删改查配置:" + sql, extra={'ptlsh': public.req_seq})
                    cur.execute(sql)
                    crud2_head = cur.fetchone()
                    if crud2_head:
                        if crud2_head[0]:
                            authlist.append(
                                {"id": str(menu_id) + '-1', "label": str(menu_id) + '-1 ' + "添加数据", "app_id": app_id,
                                 "form_id": crud2_head[0], "children": [], "field_power": True})
                        if crud2_head[1]:
                            authlist.append(
                                {"id": str(menu_id) + '-2', "label": str(menu_id) + '-2 ' + "删除数据", "app_id": app_id,
                                 "form_id": crud2_head[1], "children": [], "field_power": True})
                        if crud2_head[2]:
                            authlist.append(
                                {"id": str(menu_id) + '-3', "label": str(menu_id) + '-3 ' + "修改数据", "app_id": app_id,
                                 "form_id": crud2_head[2], "children": [], "field_power": True})
                        if crud2_head[3]:
                            authlist.append(
                                {"id": str(menu_id) + '-4', "label": str(menu_id) + '-4 ' + "导入数据", "app_id": app_id,
                                 "form_id": crud2_head[3], "children": [], "field_power": True})
                        if crud2_head[4]:
                            authlist.append(
                                {"id": str(menu_id) + '-5', "label": str(menu_id) + '-5 ' + "导出数据", "app_id": app_id,
                                 "form_id": crud2_head[4], "children": [], "field_power": True})
                    menuinfo['children'] = authlist
                elif menu_path == 'displaypage':
                    #表单配置细字段属性返回
                    menuinfo["field_power"] = True
                else:
                    # 暂无配置功能，不返回具体权限
                    menuinfo["field_power"] = False
            MenuTreeData.append(menuinfo)

        # 返回结果
        return MenuTreeData

    # 获取菜单角色列表,所有权限
    def GetMenuTreeData_ByRole(roleid, menuid):
        log = public.logger
        MenuTreeData = []

        # 根据菜单子码获取子码标签
        def submenu2value(submenuid):
            if submenuid == 0:
                return "查询数据"
            elif submenuid == 1:
                return "添加数据"
            elif submenuid == 2:
                return "删除数据"
            elif submenuid == 3:
                return "更新数据"
            elif submenuid == 4:
                return "导入数据"
            elif submenuid == 5:
                return "导出数据"
            else:
                return ''

        # 根据菜单APPID获取FormID
        # def GetFormId_ByMenuApp(menuid,appid):
        #     if '-' in str(menuid):
        #         menu_id = int(str(menuid).split('-')[0])
        #         submenu_id = int(str(menuid).split('-')[1])
        #     else:
        #         menu_id = int(menuid)
        #         submenu_id = 0

        sql = "select a.menu_id, a.menu_name, a.is_run_menu, a.app_id, menu_path " \
              "from sys_menu a  where a.above_menu_id ='%s' " % (menuid)
        log.info("获取菜单角色列表:" + sql, extra={'ptlsh': public.req_seq})

        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            menuinfo = {}
            menu_id = item[0]
            menu_name = item[1]
            is_run_menu = item[2]
            menuinfo['id'] = str(menu_id)
            menuinfo['label'] = str(menu_id) + '-' + str(menu_name)
            if is_run_menu != 'Y':  # 非功能菜单，就是目录菜单
                menuinfo['menu_type'] = 'CONTENTS'
                menuinfo['field_power'] = False
                menuinfo['children'] = GetMenuTreeData_ByRole(roleid, menu_id)
                if len(menuinfo['children']) == 0:  # 空节点不再管它
                    continue
            else:  # 功能菜单,获取功能操作权限和字段权限
                menuinfo['menu_type'] = 'RUN_MENU'  # 功能菜单
                authlist = []
                app_id = item[3]
                menu_path = item[4]

                sql = "select menu_id,app_id,auth_type,auth_flag from sys_role_purv_head " \
                      "where role_id='%s' and menu_id like '%s-%%'" % (roleid, menu_id)
                cur.execute(sql)
                crud_head = cur.fetchall()
                for crud_item in crud_head:
                    if '-' in str(crud_item[0]):
                        menu_id = int(str(crud_item[0]).split('-')[0])
                        submenu_id = int(str(crud_item[0]).split('-')[1])
                    else:
                        menu_id = int(crud_item[0])
                        submenu_id = 0
                    authlist.append({"id": str(crud_item[0]), "label": str(crud_item[0]) + submenu2value(submenu_id),
                                     "app_id": str(app_id), "form_id": "", "field_power": public.Y2True(crud_item[3])})
            MenuTreeData.append(menuinfo)

        # 返回结果
        return MenuTreeData

    try:
        if role_id == 'root':
            public.respcode, public.respmsg = "200301", "超级角色不需要配置菜单权限!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标
        sql="select ROLE_ID,ROLE_NAME,ROLE_ABOVE_ID,ROLE_STATE,OPERATE_USERID,OPERATE_DATETIME,SNOTE from sys_role where role_id=%s"
        if above_role_id:
            log.info("查询超级角色权限:"+sql % (above_role_id), extra={'ptlsh': public.req_seq})
            cur.execute(sql, (above_role_id))
        else:
            public.respcode, public.respmsg = "200211", "查询条件不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            cur.close()
            return public.respinfo

        row=cur.fetchone()
        if not row:
            public.respcode, public.respmsg = "200212", "角色信息不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        if above_role_id == 'root':
            tree_data = GetMenuTreeData_ByRoot('root')
        else:
            tree_data = GetMenuTreeData_ByRole(above_role_id, 'root')

        if role_id: #查询这个role所有的权限
            sql="select menu_id, auth_type from sys_role_purv_head where role_id=%s "
            cur.execute(sql, (role_id))
            rows = cur.fetchall()
            selectedKeys=[]
            for item in rows:
                if str(item[1])=='0':
                    selectedKeys.append( str(item[0]) )
                else:
                    selectedKeys.append( str(item[0])+'-'+str(item[1]) )
        cur.close()

    except Exception as ex:
        log.error("查询数据表信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "查询数据表信息失败!" + str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "角色查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":body.get('form_id'),
            "form_var":{
                "role_id": form_var.get('role_id'),
                "role_name": form_var.get('role_name'),
                "role_above_id": form_var.get('role_above_id'),
                "snote": form_var.get('snote'),
                "root_role_option": form_var.get('root_role_option'),
                "tree_data": tree_data,
                "selectedKeys":selectedKeys,
            },

        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#用户权限管理-角色删除 --暂时不用，走的是增删改查的通用删除流程
def role_cfg_delete( request ):
    log = public.logger
    body=public.req_body
    try:
        cur = connection.cursor()  # 创建游标
        sql="delete from sys_role where role_id=%s "
        cur.execute(sql, ( body.get('ROLE_ID') ) )
        cur.close()

    except Exception as ex:
        log.error("删除角色信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "删除角色信息失败!" + str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "删除角色成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {},
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#获取机构列表-配置时使用
def get_org_cfglist( request ):
    log = public.logger

    # 获取菜单角色列表,--菜单配置时使用
    def GetCfgOrgTreeData( above_org_id ):
        log = public.logger
        OrgTreeData = []

        sql = "select org_id, org_name from sys_org where above_org_id='%s' and org_state='1' "  % ( above_org_id )
        # log.info("获取机构信息列表:" + sql, extra={'ptlsh': public.req_seq})
        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            orginfo = {}
            org_id = str(item[0])
            orginfo['org_id'] = org_id
            orginfo['org_name'] = item[1]

            tempchild = GetCfgOrgTreeData(org_id)
            if len(tempchild) > 0:
                orginfo['children'] = tempchild

            OrgTreeData.append(orginfo)

        log.info("OrgTreeData" + str(OrgTreeData))
        # 返回结果
        return OrgTreeData

    try:
        cur = connection.cursor()
        orglist = GetCfgOrgTreeData( 'root' )

        #查询机构简称数据字典
        sql = "select dict_code, CONCAT(dict_code,'-',dict_target) from sys_ywty_dict where dict_name='ORG_SPELL'"
        cur.execute(sql)
        rows = cur.fetchall()
        org_spell_list=[]
        for item in rows:
            org_spell_list.append({"key":item[0], "value":item[1]})
        cur.close()

        log.info("orglist=" + str(orglist))
    except Exception as ex:
        log.error("交易失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "交易失败!" + str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "orglist":orglist,
            "org_spell_list": org_spell_list,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#获取机构详情-配置时使用
def get_org_cfginfo( request ):
    log = public.logger
    body=public.req_body
    orgid=body.get('org_id')
    if not orgid:
        public.respcode, public.respmsg = "100122", "org_id不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()

        sql = "select org_id,org_name,above_org_id,org_type,org_level,org_addr,org_leader,org_spell, org_state, snote " \
              "from sys_org where org_id='%s'" % orgid
        cur.execute(sql)
        row = cur.fetchone()
        orginfo = {}
        if row:
            orginfo['org_id'] = row[0]
            orginfo['org_name'] = row[1]
            orginfo['above_org_id'] = row[2]
            orginfo['org_type'] = row[3]
            orginfo['org_level'] = row[4]
            orginfo['org_addr'] = row[5]
            orginfo['org_leader'] = row[6]
            orginfo['org_spell'] = row[7]
            orginfo['org_state'] = row[8]
            orginfo['snote'] = row[9]

        cur.close()
        # orginfo['option_org_type'] = [{"depart":"部门"}, {"project":"项目组"}, {"company":"公司"} ]
        # orginfo['option_org_state'] = [{"0":"停用"}, {"1":"正常"}]

    except Exception as ex:
        log.error("交易失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "交易失败!" + str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "orginfo":orginfo,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#用户权限管理-新增机构或修改机构信息
def org_cfg_save(request):
    log = public.logger
    body = public.req_body
    orginfo = body.get('orginfo')
    orgid = orginfo.get('org_id')

    try:
        cur = connection.cursor()  # 创建游标
        if orgid:  # 新增机构
            #先删除原机构数据
            sql = "delete from sys_org where org_id='%s'" % orgid
            cur.execute(sql)

            #新增数据
            sql = "insert into sys_org(org_id,org_name,above_org_id,org_type,org_level,org_addr,org_leader,org_spell,org_state, snote, operate_userid) " \
                  "values(%s,%s,%s,%s,%s,%s,  %s,%s,%s,%s,%s)"
            cur.execute(sql, (orgid, orginfo.get('org_name'), orginfo.get('above_org_id'), orginfo.get('org_type'), orginfo.get('org_level'),
                              orginfo.get('org_addr'), orginfo.get('org_leader'), orginfo.get('org_spell'), orginfo.get('org_state'), orginfo.get('snote'), public.user_id) )
        else: # 新增机构
            # 新增数据
            sql = "insert into sys_org(org_name,above_org_id,org_type,org_level,org_addr,org_leader,org_spell,org_state, snote, operate_userid) " \
                  "values(%s,%s,%s,%s,%s,  %s,%s,%s,%s,%s)"
            cur.execute(sql, (orginfo.get('org_name'), orginfo.get('above_org_id'), orginfo.get('org_type'),
                              orginfo.get('org_level'),
                              orginfo.get('org_addr'), orginfo.get('org_leader'),orginfo.get('org_spell'), orginfo.get('org_state'),
                              orginfo.get('snote'), public.user_id))
            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                org_id = row[0]
                orginfo['org_id'] = row[0]
                log.info('org_id生成，自增字段ID:%s' % str(org_id), extra={'ptlsh': public.req_seq})
            cur.close()  # 关闭游标
        cur.close()

    except Exception as ex:
        log.error("保存机构信息失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "保存机构信息失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "机构保存成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "orginfo":orginfo
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#用户权限管理-机构删除
def org_cfg_delete( request ):
    log = public.logger
    body=public.req_body
    orginfo = body.get('orginfo')
    orgid = orginfo.get('org_id')
    if not orgid:
        public.respcode, public.respmsg = "100122", "org_id不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        sql = "delete from sys_org where org_id='%s'" % orgid
        cur.execute(sql)
        cur.close()

    except Exception as ex:
        log.error("删除数据表信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "删除数据表信息失败!" + str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "机构删除成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {},
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo
