import sys
from django.shortcuts import HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime

###########################################################################################################
#菜单信息、菜单权限、字段权限、
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

#获取菜单列表-用户登陆时使用
def get_menu_list( request ):
    log = public.logger

    # 获取菜单角色列表,--用户登陆时使用
    def GetMenuTreeData_ByUser(role_list, userid, menuid):
        log = public.logger
        MenuTreeData = []

        sql = "select a.menu_id, a.menu_name, a.is_run_menu, a.menu_desc, a.order_id, a.app_id, a.menu_type, a.menu_path, " \
              "a.menu_icon, a.is_enable, a.above_menu_id " \
              "from sys_menu a  where a.above_menu_id ='%s' order by order_id asc" % (menuid)
        # log.info("获取菜单角色列表:" + sql, extra={'ptlsh': public.req_seq})

        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            menuinfo = {}
            menu_id = str(item[0])
            menu_name = item[1]
            is_run_menu = item[2]
            menuinfo['menu_id'] = menu_id
            menuinfo['menu_name'] = menu_name
            # menuinfo['menu_desc'] = item[3]
            # menuinfo['menu_seq'] = item[4]
            menuinfo['menu_appid'] = item[5]
            menuinfo['menu_type'] = item[6]  # 菜单类型 目录，自定义等。。
            menuinfo['menu_path'] = item[7]  # 菜单路径(自定义路径)
            menuinfo['menu_icon'] = item[8]  # 菜单图标
            is_enable = item[9]  #是否激活
            menuinfo['above_menu_id'] = item[10] #上级机构
            if is_enable !='Y':
                continue

            if is_run_menu != 'Y':  # 非功能菜单，就是目录菜单
                menuinfo['children'] = GetMenuTreeData_ByUser(role_list, userid, menu_id)
                if len(menuinfo['children']) == 0:  # 空节点不再管它
                    continue
                else:
                    MenuTreeData.append(menuinfo)
            else:  # 功能菜单,获取功能操作权限和字段权限
                if 'root' in role_list:
                    MenuTreeData.append(menuinfo)
                else:
                    # 获取用户是否拥用此菜单的权限
                    sql = "select distinct a.menu_id from sys_role_purv_head a, sys_user_role b " \
                          "where a.role_id=b.role_id and a.menu_id='%s' and b.user_id='%s'" % (menu_id, userid)
                    # log.info("获取用户是否拥用此菜单的权限:" + str(sql))
                    cur.execute(sql)
                    row = cur.fetchone()
                    if row:
                        MenuTreeData.append(menuinfo)
                    else:
                        continue

        # log.info("MenuTreeData" + str(MenuTreeData))
        # 返回结果
        return MenuTreeData

    try:
        cur = connection.cursor()

        sql = "select role_id from sys_user_role where user_id='%s'" % public.user_id
        cur.execute(sql)
        rows = cur.fetchall()
        role_list=[]
        for item in rows:
            role_list.append(item[0])

        if len(role_list) > 0:
            menulist = GetMenuTreeData_ByUser(role_list, public.user_id, 'root')
        else:
            menulist = []
            # log.info( "menulist="+str(menulist) )
        cur.close()
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
            "menulist":menulist,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#获取菜单列表-配置时使用
def get_menu_cfglist( request ):
    log = public.logger

    # 获取菜单角色列表,--菜单配置时使用
    def GetCfgMenuTreeData( menuid ):
        log = public.logger
        MenuTreeData = []

        sql = "select a.menu_id, a.menu_name, a.is_run_menu, a.menu_desc, a.order_id, a.app_id, a.menu_type, a.menu_path, " \
              "a.menu_icon, a.is_enable, a.above_menu_id " \
              "from sys_menu a  where a.above_menu_id ='%s' order by a.order_id asc" % (menuid)
        # log.info("获取菜单角色列表:" + sql, extra={'ptlsh': public.req_seq})

        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            menuinfo = {}
            menu_id = str(item[0])
            menu_name = item[1]
            is_run_menu = item[2]
            menuinfo['menu_id'] = menu_id
            menuinfo['menu_name'] = menu_name
            # menuinfo['menu_desc'] = item[3]
            # menuinfo['menu_seq'] = item[4]
            menuinfo['menu_appid'] = item[5]
            menuinfo['menu_type'] = item[6]  # 菜单类型 目录，自定义等。。
            menuinfo['menu_path'] = item[7]  # 菜单路径(自定义路径)
            menuinfo['menu_icon'] = item[8]  # 菜单图标
            # menuinfo['is_active'] = public.Y2True( item[9] )
            is_enable = item[9]  #是否激活
            menuinfo['above_menu_id'] = item[10] #上级机构

            if is_run_menu != 'Y':  # 非功能菜单，就是目录菜单
                TempChild = GetCfgMenuTreeData( menu_id )
                if len(TempChild) > 0:
                    menuinfo['children'] = TempChild
                MenuTreeData.append(menuinfo)
            else:  # 功能菜单
                MenuTreeData.append(menuinfo)

        # log.info("MenuTreeData" + str(MenuTreeData))
        # 返回结果
        return MenuTreeData

    try:
        cur = connection.cursor() #创建游标
        menulist = GetCfgMenuTreeData( 'root' )
        cur.close()
        # log.info( "menulist="+str(menulist) )

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
            "menulist":menulist,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 菜单详情查询
def get_menu_info( request ):
    log = public.logger
    body=public.req_body
    menuid=body.get('menu_id')
    if not menuid:
        public.respcode, public.respmsg = "100112", "menu_id不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        sql = "select a.menu_id, a.menu_name, a.is_run_menu, a.menu_desc, a.order_id, a.app_id, a.menu_type, a.menu_path, " \
              "a.menu_icon, a.is_enable, a.above_menu_id " \
              "from sys_menu a  where a.menu_id =%s "
        log.info("查询菜单详情:" +sql % menuid, extra={'ptlsh': public.req_seq})
        cur.execute( sql, (menuid) )
        row=cur.fetchone()
        if not row:
            cur.close()
            log.info("对应的MENUID不存在!", extra={'ptlsh': public.req_seq})
            public.respcode, public.respmsg = "100111", "对应的MENUID不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        menuinfo = {}
        menuinfo['menu_id'] = str(row[0])
        menuinfo['menu_name'] = row[1]
        menuinfo['menu_desc'] = row[3]
        menuinfo['menu_seq'] = row[4]   #排序号
        menuinfo['menu_appid'] = row[5]
        menuinfo['menu_type'] = row[6]  #菜单类型 目录，自定义等。。
        menuinfo['menu_path'] = row[7]  # 菜单路径(自定义路径)
        menuinfo['menu_icon'] = row[8]  # 菜单图标
        menuinfo['is_active'] = public.Y2True(row[9])
        menuinfo['above_menu_id'] = row[10]  # 上级菜单ID

        cur.close()

    except Exception as ex:
        log.error("菜单信息查询失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "菜单信息查询失败!" + str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "menuinfo":menuinfo,
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 保存菜单配置
def save_menu_info( request ):
    log = public.logger
    body=public.req_body
    menuinfo=body.get('menuinfo')
    try:

        if not menuinfo.get('above_menu_id'):
            public.respcode, public.respmsg = "100114", "上级菜单ID不可为空"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        cur = connection.cursor()  # 创建游标
        #获取父级菜单的信息
        if menuinfo.get('above_menu_id')==-1:
            menuinfo['above_menu_id']="root"
        if menuinfo.get('above_menu_id')=="root":
            menuinfo['menu_deep']=0
        else:
            sql = "select menu_deep from sys_menu where menu_id=%s "
            cur.execute(sql, menuinfo.get('above_menu_id'))
            row = cur.fetchone()
            if not row:
                cur.close()
                public.respcode, public.respmsg = "100115", "父级菜单不存在"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            else:
                menuinfo['menu_deep'] = int(row[0])+1

        if menuinfo['menu_type'] == 'CONTENTS':
            menuinfo['is_run_menu'] = 'N'
        else:
            menuinfo['is_run_menu'] = 'Y'

        if not menuinfo.get('menu_appid'):
            menuinfo['menu_appid']=None
        if not menuinfo.get('menu_tranid'):
            menuinfo['menu_tranid']=None
        if not menuinfo.get('menu_seq'):
            menuinfo['menu_seq']=None

        if not menuinfo.get('menu_id'):  # 没有menuid,是新增菜单
            sql="insert into sys_menu(above_menu_id,menu_deep,menu_name,menu_desc,is_run_menu, " \
                "app_id,tran_id,is_enable,order_id, menu_type,  menu_path,menu_icon, snote) " \
                "values(%s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s)"
            log.info("新增菜单:"+sql % ( menuinfo.get('above_menu_id'),menuinfo.get('menu_deep'), menuinfo.get('menu_name'),
                               menuinfo.get('menu_desc'), menuinfo.get('is_run_menu'),menuinfo.get('menu_appid'),
                               menuinfo.get('menu_tranid'), menuinfo.get('is_enable'), menuinfo.get('menu_seq'),
                               menuinfo.get('menu_type'),menuinfo.get('menu_path'),menuinfo.get('menu_icon'),
                               menuinfo.get('snote') ) , extra={'ptlsh':public.req_seq})
            cur.execute(sql, ( menuinfo.get('above_menu_id'),menuinfo.get('menu_deep'), menuinfo.get('menu_name'),
                               menuinfo.get('menu_desc'), menuinfo.get('is_run_menu'),menuinfo.get('menu_appid'),
                               menuinfo.get('menu_tranid'), public.True2y(menuinfo.get('is_active') ), menuinfo.get('menu_seq'),
                               menuinfo.get('menu_type'),menuinfo.get('menu_path'),menuinfo.get('menu_icon'),
                               menuinfo.get('snote') ) )
            # 查询刚刚插入的ID
            cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
            row = cur.fetchone()
            if row:
                menu_id = row[0]
                menuinfo['menu_id'] = row[0]
                log.info('menu_id生成，自增字段ID:%s' % str(menu_id), extra={'ptlsh': public.req_seq})

            cur.close()  # 关闭游标

        else:
            #修改菜单信息
            sql = "update sys_menu set above_menu_id=%s,menu_deep=%s,menu_name=%s,menu_desc=%s,is_run_menu=%s," \
                  "app_id=%s,tran_id=%s,is_enable=%s,order_id=%s, menu_type=%s, menu_path=%s,menu_icon=%s, snote=%s " \
                  "where menu_id=%s"
            log.info( "修改菜单:" +(sql % (menuinfo.get('above_menu_id'), menuinfo.get('menu_deep'), menuinfo.get('menu_name'),
                                  menuinfo.get('menu_desc'), menuinfo.get('is_run_menu'), menuinfo.get('menu_appid'),
                                  menuinfo.get('menu_tranid'), public.True2y(menuinfo.get('is_active') ), menuinfo.get('menu_seq'),
                                  menuinfo.get('menu_type'), menuinfo.get('menu_path'), menuinfo.get('menu_icon'),
                                  menuinfo.get('snote'),menuinfo.get('menu_id') ) ), extra={'ptlsh': public.req_seq})
            cur.execute(sql, (menuinfo.get('above_menu_id'), menuinfo.get('menu_deep'), menuinfo.get('menu_name'),
                              menuinfo.get('menu_desc'), menuinfo.get('is_run_menu'), menuinfo.get('menu_appid'),
                              menuinfo.get('menu_tranid'), public.True2y(menuinfo.get('is_active') ), menuinfo.get('menu_seq'),
                              menuinfo.get('menu_type'), menuinfo.get('menu_path'), menuinfo.get('menu_icon'),
                              menuinfo.get('snote'),menuinfo.get('menu_id') ))

        cur.close()

    except Exception as ex:
        log.error("插入数据表信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100200", "插入数据表信息失败!" + str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "菜单添加成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "menuinfo":menuinfo
        },
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


# 删除菜单
def delete_menu_info( request ):
    log = public.logger
    body=public.req_body
    menuid=body.get('menu_id')
    if not menuid:
        public.respcode, public.respmsg = "100312", "menu_id不可为空!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    try:
        cur = connection.cursor()  # 创建游标
        sql = "select menu_id,menu_name from sys_menu where above_menu_id = %s " #查看是否有下级菜单
        log.info("查看是否有下级菜单:" +sql % menuid, extra={'ptlsh': public.req_seq})
        cur.execute( sql, (menuid) )
        row=cur.fetchone()
        if row:
            cur.close()
            public.respcode, public.respmsg = "100316", "请先删除下级菜单!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo

        sql = "delete from sys_menu where menu_id=%s "  # 查看是否有下级菜单
        log.info("删除菜单:" + sql % menuid, extra={'ptlsh': public.req_seq})
        cur.execute(sql, (menuid))

        cur.close()

    except Exception as ex:
        log.error("菜单信息删除失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100300", "菜单信息删除失败!" + str(ex)
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

