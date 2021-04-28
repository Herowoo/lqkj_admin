from django.shortcuts import render,redirect,HttpResponse
from django.db import connection, transaction
import json
from admin_app import public
from admin_app import models
import datetime

#新增菜单
def AddMenu(request):
    log=public.logger
    log.info('----------------------Admin-CrudCfg_AddMenu-begin---------------------------')

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    log.info(reqest_body)
    MenuReg = reqest_body['menuinfo']
    #print(MenuReg)
    #检查上送数据是否正确
    abovemenuid = MenuReg.get('ABOVE_MENU_ID', None)
    if abovemenuid==None:
        s = public.setrespinfo({"respcode": "300001", "respmsg": "上级菜单不可为空!"})
        return HttpResponse(s)
    abovemenuid=int(abovemenuid)
    isrunmenu = public.True2y(MenuReg.get('IS_RUN_MENU', "N"))
    menu_path = public.True2y(MenuReg.get('MENU_PATH', None))
    appid = MenuReg.get('APP_ID', None)
    if abovemenuid > 0:
        try:
            MenuTable=models.IrsadminMenu.objects.get(menu_id=abovemenuid)
        except models.IrsadminMenu.DoesNotExist:
            MenuTable = None
            s = public.setrespinfo({"respcode": "300002", "respmsg": "上级菜单不存在!"})
            return HttpResponse(s)
        if int(MenuTable.menu_deep) >= 2:
            s = public.setrespinfo({"respcode": "100004", "respmsg": "最多支持三级菜单!"})
            return HttpResponse(s)
        else:
            menudeep = int(MenuTable.menu_deep) + 1

        if MenuTable.is_run_menu=='Y':
            s = public.setrespinfo({"respcode": "100005", "respmsg": "功能菜单下不可以再添加子菜单!"})
            return HttpResponse(s)
    else:
        #添加的是零级菜单
        menudeep = 0
        isrunmenu='N'
        pass

    if menudeep==2 and isrunmenu!='Y':
        s = public.setrespinfo({"respcode": "100006", "respmsg": "三级菜单必须是功能菜单!"})
        return HttpResponse(s)

    if isrunmenu=='Y' and menu_path == 'cruddata':
        if appid==None or appid=='':
            s = public.setrespinfo({"respcode": "100007", "respmsg": "功能菜单对应的应用编号必填!"})
            return HttpResponse(s)
        try:
            TranRegTable=models.IrsadminDbTranReg.objects.get(app_id=appid)
        except models.IrsadminDbTranReg.DoesNotExist:
            TranRegTable = None
            s = public.setrespinfo({"respcode": "300003", "respmsg": "应用编号不存在!"})
            return HttpResponse(s)
    else:
        if appid == None or appid=='':
            appid=0
    #使用models插入数据库,增删改查配置注册表
    menuinfo = models.IrsadminMenu(
        #menu_id=MenuReg.get('MENU_ID',""), #改为自增，自动生成
        above_menu_id=abovemenuid,
        menu_deep=menudeep,
        menu_name=MenuReg.get('MENU_NAME', ""),
        menu_desc=MenuReg.get('MENU_DESC', ""),
        is_run_menu=isrunmenu,
        app_id=appid,
        tran_id=MenuReg.get('TRAN_ID', 0),
        is_enable=public.True2y(MenuReg.get('IS_ENABLE', "")),
        order_id=MenuReg.get('ORDER_ID', 9999),
        menu_path=MenuReg.get('MENU_PATH', ""),
        system_id=MenuReg.get('SYSTEM_ID', ""),
        snote=MenuReg.get('SNOTE',""),
        create_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    menuinfo.save()
    log.info('登记IrsadminMenu成功')

    resp={"respcode":"000000", "respmsg":"交易成功", "MENU_ID":menuinfo.menu_id}
    s = json.dumps(resp, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-CrudCfg_AddMenu-end---------------------------')
    return HttpResponse(s)

#更新菜单
def UpdMenu(request):
    log=public.logger
    log.info('----------------------Admin-CrudCfg_AddMenu-begin---------------------------')

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    log.info(reqest_body)
    MenuReg = reqest_body['menuinfo']
    menu_path = MenuReg.get('MENU_PATH', None)
    #print(MenuReg)
    #检查上送数据是否正确
    menuid = MenuReg.get('MENU_ID', None)
    if menuid==None:
        s = public.setrespinfo({"respcode": "300001", "respmsg": "菜单编号必输!"})
        return HttpResponse(s)
    try:
        MyMenuTable = models.IrsadminMenu.objects.get(menu_id=menuid)
    except models.IrsadminMenu.DoesNotExist:
        MyMenuTable = None
        s = public.setrespinfo({"respcode": "300002", "respmsg": "菜单编号不存在!"})
        return HttpResponse(s)

    abovemenuid = MenuReg.get('ABOVE_MENU_ID', None)
    if abovemenuid==None:
        s = public.setrespinfo({"respcode": "300002", "respmsg": "上级菜单不可为空!"})
        return HttpResponse(s)
    abovemenuid=int(abovemenuid)
    isrunmenu = public.True2y(MenuReg.get('IS_RUN_MENU', "N"))
    appid = MenuReg.get('APP_ID', None)
    if abovemenuid > 0:
        try:
            MenuTable=models.IrsadminMenu.objects.get(menu_id=abovemenuid)
        except models.IrsadminMenu.DoesNotExist:
            MenuTable = None
            s = public.setrespinfo({"respcode": "300002", "respmsg": "上级菜单不存在!"})
            return HttpResponse(s)
        if int(MenuTable.menu_deep) >= 2:
            s = public.setrespinfo({"respcode": "100004", "respmsg": "最多支持三级菜单!"})
            return HttpResponse(s)
        else:
            menudeep = int(MenuTable.menu_deep) + 1

        if MenuTable.is_run_menu=='Y':
            s = public.setrespinfo({"respcode": "100005", "respmsg": "功能菜单下不可以再添加子菜单!"})
            return HttpResponse(s)
    else:
        #添加的是零级菜单
        menudeep = 0
        isrunmenu='N'
        pass

    if menudeep==2 and isrunmenu!='Y':
        s = public.setrespinfo({"respcode": "100006", "respmsg": "三级菜单必须是功能菜单!"})
        return HttpResponse(s)

    if isrunmenu=='Y' and menu_path == 'cruddata':
        if not appid:
            s = public.setrespinfo({"respcode": "100007", "respmsg": "功能菜单对应的应用编号必填!"})
            return HttpResponse(s)
        if appid != '0':
            try:
                TranRegTable=models.IrsadminDbTranReg.objects.get(app_id=appid)
            except models.IrsadminDbTranReg.DoesNotExist:
                TranRegTable = None
                s = public.setrespinfo({"respcode": "300003", "respmsg": "应用编号不存在!"})
                return HttpResponse(s)
    else:
        if appid == None or appid == '':
            appid = 0
    #使用models插入数据库,增删改查配置注册表
    menuinfo = models.IrsadminMenu(
        menu_id=menuid, #更新时必输
        above_menu_id=abovemenuid,
        menu_deep=menudeep,
        menu_name=MenuReg.get('MENU_NAME', ""),
        menu_desc=MenuReg.get('MENU_DESC', ""),
        is_run_menu=isrunmenu,
        app_id=appid,
        tran_id=MenuReg.get('TRAN_ID', ""),
        is_enable=public.True2y(MenuReg.get('IS_ENABLE', "")),
        order_id=MenuReg.get('ORDER_ID', ""),
        menu_path=MenuReg.get('MENU_PATH', ""),
        system_id=MenuReg.get('SYSTEM_ID', ""),
        snote=MenuReg.get('SNOTE',""),
        create_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    menuinfo.save()
    log.info('更新IrsadminMenu成功')

    resp={"respcode":"000000", "respmsg":"交易成功", "MENU_ID":menuinfo.menu_id}
    s = json.dumps(resp, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-CrudCfg_AddMenu-end---------------------------')
    return HttpResponse(s)

#删除菜单
def DelMenu(request):
    log=public.logger
    log.info('----------------------Admin-CrudCfg_AddMenu-begin---------------------------')

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    log.info(reqest_body)
    MenuReg = reqest_body['menuinfo']
    #print(MenuReg)
    #检查上送数据是否正确
    menuid = MenuReg.get('MENU_ID', None)
    if menuid==None:
        s = public.setrespinfo({"respcode": "300001", "respmsg": "菜单编号必输!"})
        return HttpResponse(s)
    try:
        MyMenuTable = models.IrsadminMenu.objects.get(menu_id=menuid)
    except models.IrsadminMenu.DoesNotExist:
        MyMenuTable = None
        s = public.setrespinfo({"respcode": "300002", "respmsg": "菜单编号不存在!"})
        return HttpResponse(s)

    if MyMenuTable.system_id =='sys' or MyMenuTable.system_id =='SYS':
        s = public.setrespinfo({"respcode": "300012", "respmsg": "系统菜单不能直接删除!"})
        return HttpResponse(s)

    try:
        MenuTable=models.IrsadminMenu.objects.get(above_menu_id=menuid)
    except models.IrsadminMenu.DoesNotExist:
        MenuTable = None

    if MenuTable:
        s = public.setrespinfo({"respcode": "100009", "respmsg": "存在下级菜单,不可删除!"})
        return HttpResponse(s)

    #使用models插入数据库,增删改查配置注册表
    menuinfo = models.IrsadminMenu(
        menu_id=menuid
    )
    menuinfo.delete()
    log.info('删除IrsadminMenu成功')

    resp={"respcode":"000000", "respmsg":"删除成功"}
    s = json.dumps(resp, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-CrudCfg_AddMenu-end---------------------------')
    return HttpResponse(s)

#获取菜单列表信息--所有菜单信息，配置使用
def GetMenuCfg(request):
    log = public.logger
    log.info('----------------------Admin-GetMenuCfg-begin---------------------------')

    # 最多三级菜单，获取主菜单信息---
    data = { "respcode": "000000",
              "respmsg": "交易成功",
             'MENULIST': []}
    MenuTable0 = models.IrsadminMenu.objects.filter(menu_deep='0').order_by('order_id')
    for item0 in MenuTable0:
        sub0item = {}
        sub0item['MENU_ID'] = str(item0.menu_id)
        sub0item['MENU_NAME'] = item0.menu_name
        sub0item['MENU_DESC'] = item0.menu_desc
        sub0item['IS_RUN_MENU'] = False #主菜单只能是非功能菜单
        sub0item['MENU1'] = []
        # 二级菜单在这里赋值,--begin
        try:
            MenuTable1 = models.IrsadminMenu.objects.filter(above_menu_id=item0.menu_id).order_by('order_id')
        except models.IrsadminMenu.DoesNotExist:
            MenuTable1=None
        for item1 in MenuTable1:
            sub1item = {}
            # 二级菜单可能是功能菜单，也可能是子菜单
            #print(item1.menu_id, '--', item1.menu_name, '是主菜单')
            sub1item['MENU_ID'] = str(item1.menu_id)
            sub1item['MENU_NAME'] = item1.menu_name
            sub1item['MENU_DESC'] = item1.menu_desc
            if item1.is_run_menu == 'Y' or item1.is_run_menu == 'y':
                sub1item['IS_RUN_MENU'] = True
                sub1item['MENU_PATH'] = item1.menu_path
            else:
                sub1item['MENU2'] = []
                sub1item['IS_RUN_MENU'] = False

                # 功能菜单在这里赋值---begin, 传入参数above_menu_id
                try:
                    MenuTable2 = models.IrsadminMenu.objects.filter(above_menu_id=item1.menu_id).order_by('order_id')
                except models.IrsadminMenu.DoesNotExist:
                    MenuTable1 = None
                for item2 in MenuTable2:
                    sub2item = {}
                    sub2item['MENU_ID'] = str(item2.menu_id)
                    sub2item['MENU_NAME'] = item2.menu_name
                    sub2item['MENU_DESC'] = item2.menu_desc
                    sub2item['MENU_PATH'] = item2.menu_path
                    sub2item['IS_RUN_MENU'] = True
                    sub1item['MENU2'].append(sub2item)

            sub0item['MENU1'].append(sub1item)

        data['MENULIST'].append(sub0item)

    #print('所有菜单',data)

    s = json.dumps(data, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-GetMenuCfg-end---------------------------')
    return HttpResponse(s)


#获取菜单列表信息
def GetMenuList(request):
    log = public.logger
    log.info('----------------------Admin-CrudCfg_GetMenuList-begin---------------------------')

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    userid = reqest_body.get('uid',None)
    if userid == None or userid=='':
        s = public.setrespinfo({"respcode": "110001", "respmsg": "用户号必输!"})
        return HttpResponse(s)

    try:
        UserTable=models.IrsadminUser.objects.get(user_id=userid)
    except models.IrsadminUser.DoesNotExist:
        s = public.setrespinfo({"respcode": "110002", "respmsg": "用户不存在!"})
        return HttpResponse(s)

    if UserTable.status not in ['0','1','2']:
        s = public.setrespinfo({"respcode": "110003", "respmsg": "用户状态异常!"})
        return HttpResponse(s)

    #获取用户所能看到的所有菜单：
    try:
        cur=connection.cursor()
        fieldlist="MENU_ID,ABOVE_MENU_ID,MENU_DEEP,MENU_NAME,MENU_DESC,IS_RUN_MENU,APP_ID,TRAN_ID,IS_ENABLE,ORDER_ID,MENU_PATH,SYSTEM_ID,SNOTE,CREATE_TIME"
        sql =" select distinct "+fieldlist+" from IRSADMIN_MENU where IS_ENABLE='Y' and menu_id in "
        sql=sql+" (select distinct b.MENU_ID from IRSADMIN_USER_RULE a, IRSADMIN_ROLE_PURV b "
        sql = sql + "where a.ROLE_ID=b.ROLE_ID and a.USER_ID=%s)"
        # print(sql, userid)
        cur.execute(sql, userid)
        rows = cur.fetchall()

        menuabovelist=[]
        menulist=[]
        for item in rows:
            menuabovelist.append( str(item[1]) )
            menulist.append(str(item[0]))

            loopid = 0
            # for subitem in item:
            #     if subitem == None or len(str(subitem)) == 0:
            #         dataitem[fieldlist[loopid]] = ""
            #     else:
            #         dataitem[fieldlist[loopid]] = subitem
            #     loopid = loopid + 1
            # data['menulist'].append(dataitem)
        cur.close()
        #print('用户所拥有的所有功能菜单列表:',menulist)
        #print('用户所拥有的所有主菜单列表:', menuabovelist)
    except :
        log.warning("系统异常", exc_info = True)
        cur.close()
        s = public.setrespinfo({"respcode": "390001", "respmsg": "系统异常!"})
        return HttpResponse(s)

    # 最多三级菜单，获取主菜单信息---
    data = {"respcode": "000000",
            "respmsg": "交易成功",
            'MENULIST': []}
    MenuTable0 = models.IrsadminMenu.objects.filter(menu_deep='0', is_enable='Y').order_by('order_id')
    for item0 in MenuTable0:
        sub0item = {}
        sub0item['MENU_ID'] = str(item0.menu_id)
        sub0item['MENU_NAME'] = item0.menu_name
        sub0item['IS_RUN_MENU'] = False #主菜单只能是非功能菜单
        sub0item['MENU1'] = []
        # 二级菜单在这里赋值,--begin
        try:
            MenuTable1 = models.IrsadminMenu.objects.filter(above_menu_id=item0.menu_id, is_enable='Y').order_by('order_id')
        except models.IrsadminMenu.DoesNotExist:
            MenuTable1=None
        for item1 in MenuTable1:
            sub1item = {}
            #print(item1.menu_id, '--', item1.menu_name)
            # 二级菜单可能是功能菜单，也可能是子菜单
            if str(item1.menu_id) in menuabovelist or str(item1.menu_id) in menulist:
                #print(item1.menu_id, '--', item1.menu_name, '是主菜单')
                sub1item['MENU_ID'] = str(item1.menu_id)
                sub1item['MENU_NAME'] = item1.menu_name
                if item1.is_run_menu == 'Y' or item1.is_run_menu == 'y':
                    sub1item['IS_RUN_MENU'] = True
                    sub1item['MENU_PATH'] = item1.menu_path
                else:
                    sub1item['MENU2'] = []
                    sub1item['IS_RUN_MENU'] = False

                    # 功能菜单在这里赋值---begin, 传入参数above_menu_id
                    try:
                        MenuTable2 = models.IrsadminMenu.objects.filter(above_menu_id=item1.menu_id, is_enable='Y').order_by('order_id')
                    except models.IrsadminMenu.DoesNotExist:
                        MenuTable1 = None
                    for item2 in MenuTable2:
                        sub2item = {}
                        #print(item2.menu_id, '--', item2.menu_name)
                        if str(item2.menu_id) in menulist:
                            sub2item['MENU_ID'] = str(item2.menu_id)
                            sub2item['MENU_NAME'] = item2.menu_name
                            sub2item['MENU_PATH'] = item2.menu_path
                            sub2item['IS_RUN_MENU'] = True
                            sub1item['MENU2'].append(sub2item)
                        else:
                            continue
                            # 功能菜单在这里赋值---end, 传入参数above_menu_id

                sub0item['MENU1'].append(sub1item)

            else:
                continue
            # 二级菜单在这里赋值,--end

        if len(sub0item['MENU1']) > 0:
            data['MENULIST'].append(sub0item)

    #print('返回菜单',data)

    s = json.dumps(data, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-CrudCfg_GetMenuList-end---------------------------')
    return HttpResponse(s)

#获取菜单详细信息
def GetMenuInfo(request):
    log = public.logger
    log.info('----------------------Admin-CrudCfg_GetMenuInfo-begin---------------------------')

    # 请求body转为json
    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)
    userid = reqest_body.get('uid',None)
    if userid == None or userid=='':
        s = public.setrespinfo({"respcode": "110001", "respmsg": "用户号必输!"})
        return HttpResponse(s)

    try:
        UserTable=models.IrsadminUser.objects.get(user_id=userid)
    except models.IrsadminUser.DoesNotExist:
        s = public.setrespinfo({"respcode": "110002", "respmsg": "用户不存在!"})
        return HttpResponse(s)

    if UserTable.status not in ['0','1','2']:
        s = public.setrespinfo({"respcode": "110003", "respmsg": "用户状态异常!"})
        return HttpResponse(s)

    menuid = reqest_body.get('MENU_ID', None)
    if menuid == None:
        s = public.setrespinfo({"respcode": "300001", "respmsg": "菜单ID必输!"})
        return HttpResponse(s)

    data = {"respcode": "000000",
            "respmsg": "交易成功",
            "trantype": "getmenuinfo",
            "menuinfo": []}
    #获取用户所能看到的所有菜单：
    try:
        cur=connection.cursor()
        fieldlist="MENU_ID,ABOVE_MENU_ID,MENU_DEEP,MENU_NAME,MENU_DESC,IS_RUN_MENU,APP_ID,TRAN_ID,IS_ENABLE,ORDER_ID,MENU_PATH,SYSTEM_ID,SNOTE,CREATE_TIME"
        sql =" select "+fieldlist+" from IRSADMIN_MENU where MENU_ID=%s"
        #print(sql, menuid)
        cur.execute(sql, menuid)
        rows = cur.fetchall()
        # print(type(rows),rows)
        fieldlist=fieldlist.split(',')
        for item in rows:
            dataitem={}
            loopid = 0
            for subitem in item:
                if subitem == None or len(str(subitem)) == 0:
                    dataitem[fieldlist[loopid]] = ""
                else:
                    dataitem[fieldlist[loopid]] = subitem

                #个性化处理，将Y变为True
                if fieldlist[loopid] in ['IS_RUN_MENU','IS_ENABLE']:
                    if subitem=='Y':
                        dataitem[fieldlist[loopid]] = True
                    else:
                        dataitem[fieldlist[loopid]] = False

                loopid = loopid + 1
            data['menuinfo'].append(dataitem)
        cur.close()
    except :
        log.warning("系统异常", exc_info = True)
        cur.close()
        s = public.setrespinfo({"respcode": "390001", "respmsg": "系统异常!"})
        return HttpResponse(s)

    s = json.dumps(data, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-CrudCfg_GetMenuInfo-end---------------------------')
    return HttpResponse(s)


