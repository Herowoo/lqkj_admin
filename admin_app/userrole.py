from django.shortcuts import render,redirect,HttpResponse
from django.db import connection, transaction
import json
from admin_app import public
from admin_app import models
import datetime

#获取用户角色信息
def GetUserRole(request):
    log = public.logger
    log.info('----------------------Admin-CrudCfg_GetUserRole-begin---------------------------')

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    userid = reqest_body.get('USER_ID',"litz")
    if userid == None or userid=='':
        s = public.setrespinfo({"respcode": "110001", "respmsg": "用户号必输!"})
        return HttpResponse(s)

    try:
        UserTable=models.IrsadminUser.objects.get(user_id=userid)
    except models.IrsadminUser.DoesNotExist:
        UserTable=None
        s = public.setrespinfo({"respcode": "110002", "respmsg": "用户不存在!"})
        return HttpResponse(s)

    data = {"respcode": "000000",
            "respmsg": "交易成功",
            "trantype": "getuserrole",
            "userrolelist": []}

    #获取用户所能看到的所有菜单：
    try:
        cur=connection.cursor()
        fieldlist="ROLE_ID,ROLE_NAME"
        fieldlist2="b.ROLE_ID,b.ROLE_NAME"
        sql =" select "+fieldlist2+" from irsadmin_user_rule a, irsadmin_role b"
        sql = sql + " where a.ROLE_ID=b.ROLE_ID and a.USER_ID=%s"
        # print(sql, userid)
        cur.execute(sql, userid)
        rows = cur.fetchall()

        print(type(rows),rows)
        fieldlist=fieldlist.split(',')
        for item in rows:
            dataitem={}
            loopid = 0
            for subitem in item:
                if subitem == None or len(str(subitem)) == 0:
                    dataitem[fieldlist[loopid]] = ""
                else:
                    dataitem[fieldlist[loopid]] = subitem
                loopid = loopid + 1
            data['userrolelist'].append(dataitem)
        cur.close()
    except :
        log.warning("系统异常", exc_info = True)
        cur.close()
        s = public.setrespinfo({"respcode": "390001", "respmsg": "系统异常!"})
        return HttpResponse(s)

    s = json.dumps(data, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-CrudCfg_GetUserRole-end---------------------------')
    return HttpResponse(s)

#获取角色权限信息,角色可以使用的菜单
def GetRolePurv(request):
    log = public.logger
    log.info('----------------------Admin-CrudCfg_GetRolePurv-begin---------------------------')
    checkauth('123', '123')
    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    roleid = reqest_body.get('ROLE_ID', "")
    if roleid == None or roleid == '':
        s = public.setrespinfo({"respcode": "110011", "respmsg": "角色ID必输!"})
        return HttpResponse(s)

    try:
        RoleTable = models.IrsadminRole.objects.get(role_id=roleid)
    except models.IrsadminRole.DoesNotExist:
        s = public.setrespinfo({"respcode": "110012", "respmsg": "角色不存在!"})
        return HttpResponse(s)

    data = {"respcode": "000000",
            "respmsg": "交易成功",
            "trantype": "getrolepurv",
            "rolemenulist": []}

    # 获取用户所能看到的所有菜单：
    try:
        cur = connection.cursor()
        fieldlist = "MENU_ID,MENU_NAME,MENU_DESC"
        fieldlist2 = "b.MENU_ID,b.MENU_NAME,b.MENU_DESC"
        sql = " select " + fieldlist2 + " from irsadmin_role_purv a, irsadmin_menu b"
        sql = sql + " where a.MENU_ID=b.MENU_ID  and b.IS_RUN_MENU='Y' and a.ROLE_ID=%s"
        # print(sql, roleid)
        cur.execute(sql, roleid)
        rows = cur.fetchall()

        print(type(rows), rows)
        fieldlist = fieldlist.split(',')
        for item in rows:
            dataitem = {}
            loopid = 0
            for subitem in item:
                if subitem == None or len(str(subitem)) == 0:
                    dataitem[fieldlist[loopid]] = ""
                else:
                    dataitem[fieldlist[loopid]] = subitem
                loopid = loopid + 1
            data['rolemenulist'].append(dataitem)
        cur.close()
    except:
        log.warning("系统异常", exc_info=True)
        cur.close()
        s = public.setrespinfo({"respcode": "390001", "respmsg": "系统异常!"})
        return HttpResponse(s)

    s = json.dumps(data, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-CrudCfg_GetRolePurv-end---------------------------')
    return HttpResponse(s)

#校验用户是否有操作权限
def checkauth(user_id, menu_id):
    log = public.logger

    # 获取权限和菜单是否存在：
    try:
        cur = connection.cursor()
        sql = "SELECT count(1) FROM irsadmin_user_rule a, irsadmin_role_purv b  " \
              "WHERE a.role_id=b.role_id AND a.USER_ID = %s AND b.MENU_ID = %s"
        # log.info('判断用户权限SQL='+sql %  (str(user_id), str(menu_id)))
        cur.execute(sql, (user_id, menu_id) )
        rows = cur.fetchone()
        isok= int(rows[0])
        if isok<=0:
            sql="select count(1) from sys_user_role a, sys_role_purv_head b  " \
                "where a.ROLE_ID=b.ROLE_ID  and a.USER_ID=%s and b.menu_id=%s "
            cur.execute(sql, (user_id, menu_id))
            rows = cur.fetchone()
            isok = int(rows[0])
        cur.close()

        if isok>0:
            log.info('用户菜单权限正常')
            return True
        else:
            return False
    except:
        log.warning("系统异常", exc_info=True)
        cur.close()
        return False



