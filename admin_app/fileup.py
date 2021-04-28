from django.shortcuts import HttpResponse
import json
import datetime
from admin_app import public
from admin_app import models
from django.db import connection, transaction
# import subprocess  # 这个库是能够直接运行脚本的关键
import hashlib
import math

### 联桥科技评审单接口
def main(request):
    if request.method == "POST":
        log = public.logger
        #请求body转为json
        tmp =request.body
        tmp = tmp.decode(encoding='utf-8')
        reqest_body = json.loads(tmp)

        trantype = reqest_body['trantype']
        log.info('trantype=[%s]' % trantype)
        if trantype == 'files_upload': ## 上传文件
            resp = files_upload(request,reqest_body)
        elif trantype == 'getmenulist': ## 获取菜单列表
            resp = getmenulist(request,reqest_body)
        elif trantype == 'getmenutable': ## 菜单配置信息
            resp = getmenutable(request,reqest_body)
        elif trantype == 'getdegree':  ## 文件处理进度
            resp = getdegree(request, reqest_body)
        elif trantype == 'filedeal':  ## 文件处理请求
            resp = filedeal(request, reqest_body)
        else:
            s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
            resp = HttpResponse(s)
    elif request.method == "GET":
        s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
        resp = HttpResponse(s)

    return resp


#文件资源上传，反回md5值的url服务器路径
def files_upload(request, reqest_body):
    log = public.logger
    log.info('----------------------fileup-files_upload-begin---------------------------')
    filename=reqest_body.get('filename',None)
    if filename==None or len(filename)<2:
        s = public.setrespinfo({"respcode": "323311", "respmsg": "上送文件名错误"})
        return s
    uid=reqest_body.get('uid',None)

    file = reqest_body.get('file', None)
    if file==None:
        s = public.setrespinfo({"respcode": "323312", "respmsg": "上送文件内容错误"})
        return s

    # 保存文件到本地文件上传目录
    filepath=public.localhome+'fileup/'
    file_name = open(filepath+filename, 'wb') #有重名的会覆盖
    # mylen = len(reqest_body['file'])
    # log.info('mylen=' + str(mylen))
    file_name.write(file.encode('raw_unicode_escape')) #前端在json报文中，把二进制当字符串上送了，可以这样转换
    file_name.close()

    data = {
        "respcode": "000000",
        "respmsg": "上传成功",
        "trantype": reqest_body.get('trantype', None),
        'filename':filename
    }

    s = json.dumps(data, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info('----------------------fileup-files_upload-end---------------------------')
    return HttpResponse(s)


#获取菜单列表信息
def getmenulist(request,reqest_body):
    log = public.logger
    log.info('----------------------fileup_GetMenuList-begin---------------------------')

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
        sql =" select distinct "+fieldlist+" from IRSADMIN_MENU where MENU_PATH='cruddata' or MENU_PATH='' and IS_ENABLE='Y' and menu_id in "
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
        sub0item['value'] = str(item0.menu_id)
        sub0item['label'] = item0.menu_name
        sub0item['IS_RUN_MENU'] = False #主菜单只能是非功能菜单
        sub0item['children'] = []
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
                sub1item['value'] = str(item1.menu_id)
                sub1item['label'] = item1.menu_name
                if item1.is_run_menu == 'Y' or item1.is_run_menu == 'y':
                    sub1item['IS_RUN_MENU'] = True
                    sub1item['MENU_PATH'] = item1.menu_path
                else:
                    sub1item['children'] = []
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
                            sub2item['value'] = str(item2.menu_id)
                            sub2item['label'] = item2.menu_name
                            sub2item['MENU_PATH'] = item2.menu_path
                            sub2item['IS_RUN_MENU'] = True
                            sub1item['children'].append(sub2item)
                        else:
                            continue
                            # 功能菜单在这里赋值---end, 传入参数above_menu_id

                sub0item['children'].append(sub1item)

            else:
                continue
            # 二级菜单在这里赋值,--end

        if len(sub0item['children']) > 0:
            data['MENULIST'].append(sub0item)

    #print('返回菜单',data)

    s = json.dumps(data, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------fileup_GetMenuList-end---------------------------')
    return HttpResponse(s)

# 获取对应菜单的信息
def getmenutable(request, reqest_body):
    log = public.logger
    log.info('----------------------fileup-getmenutable-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }
    checkmenu = reqest_body.get('menuidlist', None)
    checkmenuid = checkmenu[-1]
    appid_sql = "SELECT APP_ID FROM irsadmin_menu where MENU_ID=%s"
    field_sql = "SELECT FIELD_ID,FIELD_NAME FROM irsadmin_db_tran_list " \
                    "WHERE APP_ID = %s AND STATE='Y' ORDER BY ORDER_ID"

    cur = connection.cursor()
    cur.execute(appid_sql,checkmenuid)
    appid = cur.fetchone()[0]
    menuHead = []
    menuData = []
    tmpdict2 = {}
    if appid:
        cur.execute(field_sql,appid)
        row = cur.fetchall()
        print('row=',row)
        for item in row:
            tmpdict1 = {
                "name":item[0],
                "label":item[1],
                "width":150
            }
            tmpdict2[item[0]] = ''
            menuHead.append(tmpdict1)
        menuData.append(tmpdict2)
    else:
        s = public.setrespinfo({"respcode": "210001", "respmsg": "该菜单配置信息不全!"})
        return HttpResponse(s)
    jsondata["menuHead"] = menuHead
    jsondata["menuData"] = menuData

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------fileup-getmenutable-end---------------------------')
    return HttpResponse(s)

#处理进度信息
def getdegree(request, reqest_body):
    log = public.logger
    log.info('----------------------fileup-get_degree-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "degree":{ #进度信息
            "status":"processed",  #已处理, "processing":处理中，“wrong”错误
            "wrong_info":"错误信息", #状态为wrong时值有效。
            "used_time": "100", #已处理时间,单位秒
            "surplus_time" :"80", #剩余时间
            "processed_num":"100", #已处理记录数
            "wrong_num":"0", #错误记录数
            "surplus_num": "80",  # 剩余记录数
        }
    }
    fileinfo = reqest_body.get('fileinfo', None)
    if fileinfo == None:
        s = public.setrespinfo({"respcode": "323511", "respmsg": "上送数据错误"})
        return s

    fileid = fileinfo.get('fileid', None)
    if fileid == None or fileid=='':
        s = public.setrespinfo({"respcode": "323311", "respmsg": "上送文件名错误"})
        return s

    cur = connection.cursor()  # 创建游标
    #查询文件登记表记录
    try:
        sql = "select resp_code, resp_msg, deal_num, file_rows, resp_time-tran_time, file_rows-deal_num, error_num " \
              "from irsadmin_db_unfile_info where file_id='%s'" % fileid
        log.info(sql)
        cur.execute(sql)
        row=cur.fetchone()
        respcode=row[0]
        if respcode=='888888' or respcode=='888887':
            jsondata['degree']['status'] = 'processing'
            # 剩余时间计算
            if row[2]==0: #还没有处理，初步估一个时间(每秒钟2条？？)
                jsondata['degree']['surplus_time'] = math.ceil(row[5]/2)
            elif row[4] == 0: #已用时间看不出来效果，初步估一个时间(每秒钟2条？？)
                jsondata['degree']['surplus_time'] = math.ceil(row[5] / 2)
            else:
                jsondata['degree']['surplus_time'] = math.ceil( (row[4]/row[2])*row[5] )
        elif  respcode=='000000':
            jsondata['degree']['status'] = 'processed'
            jsondata['degree']['surplus_time'] = 0
        else:
            jsondata['degree']['status'] = 'wrong'
            jsondata['degree']['surplus_time'] = 0
        jsondata['degree']['wrong_info'] = row[1]  #返回信息
        jsondata['degree']['processed_num']=row[2] #已处理记录数
        if row[4]==None:
            jsondata['degree']['used_time'] = 0  # 已使用时间，单位秒
        else:
            jsondata['degree']['used_time'] = row[4] #已使用时间，单位秒
        jsondata['degree']['surplus_num'] =row[5] #剩余记录数
        jsondata['degree']['wrong_num'] = row[6] #错误记录数



    except Exception as e:
        log.info("查询文件信息失败!" + str(e) , exc_info=True)
        s = public.setrespinfo({"respcode": "316222", "respmsg": "查询文件信息失败"})
        return s

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------fileup-get_degree-end---------------------------')
    return HttpResponse(s)


#开始处理文件
def filedeal(request, reqest_body):
    log = public.logger
    log.info('----------------------fileup-fileupload-begin---------------------------')

    data = {
        "respcode": "000000",
        "respmsg": "文件接收成功",
        "trantype": reqest_body.get('trantype', None),
    }

    #获取文件请求信息，总笔数等。
    fileinfo = reqest_body.get('fileinfo', None)
    if fileinfo == None:
        s = public.setrespinfo({"respcode": "323511", "respmsg": "上送数据错误"})
        return s

    filename = fileinfo.get('filename', None)
    if filename == None or len(filename) < 2:
        s = public.setrespinfo({"respcode": "323311", "respmsg": "上送文件名错误"})
        return s
    filerows = fileinfo.get('filerows', None)
    if filerows == None or filerows == '':
        s = public.setrespinfo({"respcode": "323311", "respmsg": "上送文件总记录数错误"})
        return s
    menuid = fileinfo.get('menuid', None)
    if menuid == None or menuid == '':
        s = public.setrespinfo({"respcode": "323311", "respmsg": "上送文件导入菜单ID错误"})
        return s

    if 'HTTP_X_FORWARDED_FOR' in request.META:
        ip = request.META.get('HTTP_X_FORWARDED_FOR')
    else:
        ip = request.META.get('REMOTE_ADDR')

    # 插入文件上传登记表一条记录
    FileInfo = models.IrsadminUnfileInfo(
        user_id=reqest_body.get('uid', None),
        ip=ip,
        tran_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        menu_id=menuid,
        file_path=public.localhome+'fileup/',
        file_name=filename,
        sheet_name=fileinfo.get('sheetname', None),
        file_rows=filerows,
        deal_num=0,
        error_num=0,
        repeat_num=0,
        resp_code='888887',
        resp_msg='正在处理中',
    )
    FileInfo.save()
    data["file_id"] = FileInfo.file_id
    cur = connection.cursor()  # 创建游标
    #新增，插入配置信息表记录
    try:
        for item in fileinfo.get('fieldlist', None):
            print(item)
            sql = "insert into irsadmin_db_unfile_cfg(FILE_ID, TABLE_FIELD, TABLE_FIELDNAME, FILE_FIELD, FILE_FIELDNAME)" \
                  "values('%s','%s','%s','%s','%s')" % (FileInfo.file_id, item['tablefield'], item['tablefieldname'], item['filefield'], item['filefieldname'])
            log.info(sql)
            cur.execute(sql)
    except:
        FileInfo.resp_code = '999999'
        FileInfo.resp_msg = '调用异步进程失败'
        FileInfo.save()
        data["resp_code"] = '999999'
        data["resp_msg"] = '调用异步进程失败'
    #=

    s = json.dumps(data, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info('----------------------fileup-fileupload-end---------------------------')
    return HttpResponse(s)

