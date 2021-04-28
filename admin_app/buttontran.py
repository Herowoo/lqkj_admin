from django.shortcuts import render,redirect,HttpResponse
import json
from admin_app import public
from admin_app import models
from django.db import connection, transaction
import pymssql

##用户点击交易按钮的操作
def tran_main(request):
    if request.method == "POST":
        log = public.logger
        #请求body转为json
        tmp=request.body
        tmp=tmp.decode(encoding='utf-8')
        reqest_body=json.loads(tmp)

        trantype=reqest_body['trantype']
        fun_name = trantype
        if globals().get(fun_name):
            resp = globals()[fun_name](request, reqest_body)
        else:
            s = public.setrespinfo({"respcode": "100000", "respmsg": "api error! lqkjerp!"})
            resp = HttpResponse(s)

        # # print('-'*20,trantype,'-'*20)
        # log.info('trantype=[%s]' % trantype)
        # if trantype == 'shownewpage':  #预览-返回url打开新页面
        #     resp = shownewpage(request, reqest_body)
        # elif trantype == 'open_oadetail':  #打开oa详情页面
        #     resp = open_oadetail(request, reqest_body)
        # elif trantype == 'open_ndformdetail':  #打开评审单详情页面
        #     resp = open_ndformdetail(request, reqest_body)
        # elif trantype == 'open_ndformalter':  #打开评审单修改页面
        #     resp = open_ndformalter(request, reqest_body)
        # elif trantype == 'open_ndformaudit':  #打开评审单修改页面
        #     resp = open_ndformaudit(request, reqest_body)
        # elif trantype == 'reset_audit':  #评审单锁定
        #     resp = reset_audit(request, reqest_body)
        # elif trantype == 'open_auditpace':  #评审单进度
        #     resp = open_auditpace(request, reqest_body)
        # elif trantype == 'lock_ndform':  #评审单锁定
        #     resp = lock_ndform(request, reqest_body)
        # elif trantype == 'unlock_ndform':  #评审单解锁
        #     resp = unlock_ndform(request, reqest_body)
        # elif trantype == 'invalidate_ndform':  #评审单解锁
        #     resp = invalidate_ndform(request, reqest_body)
        # elif trantype == 'open_filelist':  #附件下载
        #     resp = open_filelist(request, reqest_body)
        # elif trantype == 'open_setform':  # 打开生成结算报表页面
        #     resp = open_setform(request, reqest_body)
        # elif trantype == 'open_marketentry':  # 打开票据修改页面
        #     resp = open_marketentry(request, reqest_body)
        # elif trantype == 'stamp_audit':  # 印章管理审核（重审）
        #     resp = stamp_audit(request, reqest_body)
        # elif trantype == 'showqrcode':  #预览-弹出二维码
        #     resp = showqrcode(request, reqest_body)
        # elif trantype == 'common_commit':  #提交-发交易到后台
        #     resp = common_commit(request, reqest_body)
        # elif trantype == 'open_CriticalCompDetail':  # 提交-发交易到后台
        #     resp = open_CriticalCompDetail(request, reqest_body)
        # elif trantype=='apply_car_pass':
        #     resp=apply_car_pass(request,reqest_body)
        # elif trantype=='apply_car_fail':
        #     resp=apply_car_fail(request,reqest_body)
        # elif trantype=='apply_car_return':
        #     resp=apply_car_return(request,reqest_body)
        # else:
        #     s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
        #     resp = HttpResponse(s)
    elif request.method == "GET":
        s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
        resp = HttpResponse(s)

    return resp


#预览-返回url打开新页面
def shownewpage(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-shownewpage-begin---------------------------')

    #先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "url": "https://www.irusheng.com",  # 预览-返回url打开新页面
    }

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-shownewpage-end---------------------------')
    return HttpResponse(s)

#预览-弹出二维码
def showqrcode(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-showqrcode-begin---------------------------')

    #先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "qrcodeurl": "https://admin.irusheng.com/static/images/detl/222.jpg",  # 预览-弹出二维码
        "qrcodeinfo":"请扫码预览"  #二维码说明
    }

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-showqrcode-end---------------------------')
    return HttpResponse(s)


#提交-发交易到后台
def common_commit(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-common_commit-begin---------------------------')

    #先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-common_commit-end---------------------------')
    return HttpResponse(s)



#预览-打开oa详情页面
def open_oadetail(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-shownewpage-begin---------------------------')

    datainfo = reqest_body.get('datainfo')
    infoid = datainfo.get('id')
    print(datainfo)
    print(reqest_body)
    uid=reqest_body.get('uid')
    checksum=reqest_body.get('checksum')

    #先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "url": "%soahome?menu_id=104&uid=%s&checksum=%s&infoid=%s"%(request.META['HTTP_ORIGIN']+'/',uid,checksum,infoid),  # 预览-返回url打开新页面
    }
    print(request)
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-shownewpage-end---------------------------')
    return HttpResponse(s)

#元键元器件清单编辑-打开详情页面
def open_CriticalCompDetail(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-shownewpage-begin---------------------------')

    datainfo = reqest_body.get('datainfo')
    planno = datainfo.get('plan_no')
    uid=reqest_body.get('uid')
    checksum=reqest_body.get('checksum')
    menuid = reqest_body.get('MENU_ID')

    #先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "url": "%smaincomplist?menu_id=%s&uid=%s&checksum=%s&plan_no=%s"%(request.META['HTTP_ORIGIN']+'/', menuid, uid, checksum, planno),  # 预览-返回url打开新页面
    }

    print(request)
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-shownewpage-end---------------------------')
    return HttpResponse(s)

#预览-打开评审单详情页面
def open_ndformdetail(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-showndformdetail-begin---------------------------')

    datainfo = reqest_body.get('datainfo')
    infoid = datainfo.get('id')
    print(datainfo)
    print(reqest_body)
    uid=reqest_body.get('uid')
    checksum=reqest_body.get('checksum')

    #先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "url": "%sndformdetail?menu_id=104&uid=%s&checksum=%s&infoid=%s"%(request.META['HTTP_ORIGIN']+'/',uid,checksum,infoid),  # 预览-返回url打开新页面
    }
    print(request)
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-showndformdetail-end---------------------------')
    return HttpResponse(s)

#预览-打开评审单修改页面
def open_ndformalter(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-showndformalter-begin---------------------------')

    datainfo = reqest_body.get('datainfo')
    infoid = datainfo.get('id')
    print(datainfo)
    print(reqest_body)
    uid=reqest_body.get('uid')
    checksum=reqest_body.get('checksum')

    cursor = connection.cursor()
    state_sql = "select state from yw_bill_review_form_head where id = %s"
    cursor.execute(state_sql, infoid)
    state = cursor.fetchone()[0]
    if state == '2':
        s = public.setrespinfo({"respcode": "900009", "respmsg": "评审单已作废,禁止操作!"})
        return HttpResponse(s)
    cursor.close()
    #先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "url": "%sndformalter?menu_id=105&uid=%s&checksum=%s&infoid=%s"%(request.META['HTTP_ORIGIN']+'/',uid,checksum,infoid),  # 预览-返回url打开新页面
    }
    print(request)
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-showndformalter-end---------------------------')
    return HttpResponse(s)

#预览-打开评审单审核页面
def open_ndformaudit(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-showndformaudit-begin---------------------------')

    datainfo = reqest_body.get('datainfo')
    infoid = datainfo.get('id')
    uid=reqest_body.get('uid')
    checksum=reqest_body.get('checksum')

    #先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "url": "%sndformaudit?menu_id=105&uid=%s&checksum=%s&infoid=%s"%(request.META['HTTP_ORIGIN']+'/',uid,checksum,infoid),  # 预览-返回url打开新页面
    }
    print(request)
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-showndformaudit-end---------------------------')
    return HttpResponse(s)

# 预览-打开申请进度列表
def open_auditpace(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-open_auditpace-begin---------------------------')

    datainfo = reqest_body.get('datainfo')
    billid = datainfo.get('audit_billid')
    uid = reqest_body.get('uid')
    checksum = reqest_body.get('checksum')

    # 先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "重置成功",
        "trantype": reqest_body.get('trantype', None),
    }
    jsondata['dialogtitle'] = '评审进度'

    heads = [
        {
            'name':'section',
            'label':'部门',
            'width':'160'
        },
        {
            'name': 'auditor',
            'label': '审核人',
            'width': '160'
        },
        {
            'name': 'date',
            'label': '审核时间',
            'width': '160'
        },
        {
            'name': 'state',
            'label': '审核状态',
            'width': '160'
        },
    ]
    jsondata['dialogheads'] = heads

    cur = connection.cursor()
    sql = "select * from yw_bill_audit_info where audit_billid=%s order by section_id"
    cur.execute(sql,billid)
    log.info(sql%billid)
    rows = cur.fetchall()
    cur.close()
    tabledata = []
    if rows:
        for i in range(len(rows)):
            tmp_dict = {}
            tmp_dict['section'] = rows[i][3]
            tmp_dict['auditor'] = rows[i][4]
            tmp_dict['date'] = rows[i][5]
            if rows[i][6] =='0':
                tmp_dict['state'] = '待审核'
            else:
                tmp_dict['state'] = '已审核'
            tabledata.append(tmp_dict)
    else:
        s = public.setrespinfo({"respcode": "900011", "respmsg": "无审核信息!"})
        return HttpResponse(s)
    jsondata['dialogtableData'] = tabledata

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-open_auditpace-end---------------------------')
    return HttpResponse(s)


# 重置审核
def reset_audit(request,reqest_body):
    log = public.logger
    log.info('----------------------Button-lockndform-begin---------------------------')

    datainfo = reqest_body.get('datainfo')
    billid = datainfo.get('audit_billid')
    uid = reqest_body.get('uid')
    checksum = reqest_body.get('checksum')

    # 先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "重置成功",
        "trantype": reqest_body.get('trantype', None),
    }

    role_list = ['lqkj_shichang', 'lqkj_yanfa', 'lqkj_wukong', 'lqkj_zhikong', 'lqkj_shengchan', 'lqkj_pmc']
    cur = connection.cursor()
    role_sql = "select ROLE_ID from sys_user_role where USER_ID = %s"
    cur.execute(role_sql, uid)
    log.info(role_sql % uid)
    rows = cur.fetchall()
    cur.close()
    rows = str(rows)
    temp_list = []
    if rows:
        for i in range(len(role_list)):
            if role_list[i] in rows:
                temp_list.append(i)
    if len(temp_list) !=0:
        cur = connection.cursor()
        update_sql = "update yw_bill_audit_info set audit_state='0' where audit_billid = %s and section_id = %s"
        for item in temp_list:
            tmp_tuple = (billid,item)
            cur.execute(update_sql,tmp_tuple)
    else:
        s = public.setrespinfo({"respcode": "900009", "respmsg": "没有操作权限!"})
        return HttpResponse(s)
    cur.close()
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-lockndform-end---------------------------')
    return HttpResponse(s)

# 评审单锁定
def lock_ndform(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-lockndform-begin---------------------------')

    datainfo = reqest_body.get('datainfo')
    infoid = datainfo.get('id')
    billid = datainfo.get('head_id')
    print(datainfo)
    print(reqest_body)
    uid = reqest_body.get('uid')
    checksum = reqest_body.get('checksum')

    # 先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    cursor = connection.cursor()
    sql = "select ROLE_ID from sys_user_role where USER_ID = %s"
    cursor.execute(sql, uid)
    log.info(sql % uid)
    rows = cursor.fetchall()
    rows = str(rows)
    if rows:
        if ("administrator" in rows) or ("lqkj_pmc" in rows):
            state_sql = "select state from yw_bill_review_form_head where id = %s"
            cursor.execute(state_sql,infoid)
            state = cursor.fetchone()[0]
            if state == '2':
                s = public.setrespinfo({"respcode": "900009", "respmsg": "评审单已作废,禁止操作!"})
                return HttpResponse(s)
            else:
                # select_audit_sql = "select * from yw_bill_audit_info where audit_billid = %s and audit_state = '0'"
                select_audit_sql = "select * from yw_bill_audit_info where audit_billid = %s and audit_state = '0' and section_id=5"
                cursor.execute(select_audit_sql,billid)
                audit_rows = cursor.fetchone()
                if audit_rows:
                    s = public.setrespinfo({"respcode": "900010", "respmsg": audit_rows[3]+"未审核,操作失败!"})
                    return HttpResponse(s)
                else:
                    update_state_sql = "update yw_bill_review_form_head set state='0' where id = %s"
                    cursor.execute(update_state_sql,infoid)
        else:
            s = public.setrespinfo({"respcode": "900009", "respmsg": "没有操作权限!"})
            return HttpResponse(s)
    cursor.close()
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-lockndform-end---------------------------')
    return HttpResponse(s)

# 评审单作废
def invalidate_ndform(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-invalidatendform-begin---------------------------')

    datainfo = reqest_body.get('datainfo')
    infoid = datainfo.get('id')
    billid = datainfo.get('head_id')
    print(datainfo)
    print(reqest_body)
    uid = reqest_body.get('uid')
    checksum = reqest_body.get('checksum')

    # 先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    cursor = connection.cursor()
    sql = "select ROLE_ID from sys_user_role where USER_ID = %s"
    cursor.execute(sql, uid)
    log.info(sql % uid)
    rows = cursor.fetchall()
    rows = str(rows)
    if rows:
        if ("administrator" in rows) or ("lqkj_pmc" in rows):
            update_state_sql = "update yw_bill_review_form_head set state='2' where id = %s"
            cursor.execute(update_state_sql,infoid)
        else:
            s = public.setrespinfo({"respcode": "900009", "respmsg": "没有操作权限!"})
            return HttpResponse(s)
    cursor.close()
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-invalidate_ndform-end---------------------------')
    return HttpResponse(s)

# 评审单解锁
def unlock_ndform(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-lockndform-begin---------------------------')

    datainfo = reqest_body.get('datainfo')
    infoid = datainfo.get('id')
    print(datainfo)
    print(reqest_body)
    uid = reqest_body.get('uid')
    checksum = reqest_body.get('checksum')

    # 先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }


    cursor = connection.cursor()
    sql = "select ROLE_ID from sys_user_role where USER_ID = %s"
    cursor.execute(sql, uid)
    log.info(sql % uid)
    rows = cursor.fetchall()
    rows = str(rows)
    if rows:
        if ("administrator" in rows) or ("lqkj_pmc" in rows):
            state_sql = "select state from yw_bill_review_form_head where id = %s"
            cursor.execute(state_sql, infoid)
            state = cursor.fetchone()[0]
            if state == '2':
                s = public.setrespinfo({"respcode": "900009", "respmsg": "评审单已作废,禁止操作!"})
                return HttpResponse(s)
            else:
                update_state_sql = "update yw_bill_review_form_head set state='1' where id = %s"
                cursor.execute(update_state_sql,infoid)
        else:
            s = public.setrespinfo({"respcode": "900009", "respmsg": "没有操作权限!"})
            return HttpResponse(s)
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-lockndform-end---------------------------')
    return HttpResponse(s)

# 预览-打开下载弹窗
def open_filelist(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-open_filelist-begin---------------------------')

    datainfo = reqest_body.get('datainfo')
    billid = datainfo.get('billid')
    uid = reqest_body.get('uid')
    checksum = reqest_body.get('checksum')

    # 先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "重置成功",
        "trantype": reqest_body.get('trantype', None),
    }
    jsondata['dialogtitle'] = '附件列表'

    heads = [
        {
            'name':'fileid',
            'label':'附件编号',
            'width':'160'
        },
        {
            'name': 'filedate',
            'label': '上传时间',
            'width': '160'
        },
        {
            'name': 'filelist',
            'label': '附件',
            'width': '160'
        },
        {
            'name': 'state',
            'label': '审核状态',
            'width': '160'
        }
    ]
    jsondata['dialogheads'] = heads
    tabledata = []
    select_annex_sql = "select * from yw_bill_annex_info where billid=%s"
    select_filename_sql = "select file_name,tran_date from yw_workflow_file where id=%s"
    cur = connection.cursor()
    cur.execute(select_annex_sql,billid)
    annex_row = cur.fetchone()
    if annex_row:
        if annex_row[2]:
            fileidlist = annex_row[2].split('/')
            for item in fileidlist:
                state = ''
                filedict = eval(annex_row[3])
                if filedict[str(item)]==0:
                    state = '待审核'
                elif filedict[str(item)] == 1:
                    state = '通过'
                else:
                    state = '未通过'
                cur.execute(select_filename_sql, int(item))
                name_row = cur.fetchone()
                if name_row:
                    tabledata.append({
                        "fileid": item,
                        "filedate": name_row[1],
                        "filelist":{
                            "name":name_row[0],
                            "fileid":item
                        },
                        'state': state
                    })
        else:
            s = public.setrespinfo({"respcode": "900013", "respmsg": "无上传的附件！"})
            return HttpResponse(s)
    else:
        s = public.setrespinfo({"respcode": "900013", "respmsg": "无上传的附件！"})
        return HttpResponse(s)



    jsondata['dialogtableData'] = tabledata

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-open_filelist-end---------------------------')
    return HttpResponse(s)


#预览-打开结算报表页面
def open_setform(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-open_setform-begin---------------------------')

    datainfo = reqest_body.get('datainfo')
    creid = datainfo.get('code_cre_id')
    print(datainfo)
    print(reqest_body)
    uid=reqest_body.get('uid')
    checksum=reqest_body.get('checksum')
    menuid = reqest_body.get('MENU_ID')

    #先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "url": "%ssetform?menu_id=%s&uid=%s&checksum=%s&creid=%s"%(request.META['HTTP_ORIGIN']+'/',menuid,uid,checksum,creid),  # 预览-返回url打开新页面
    }
    print(request)
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-open_setform-end---------------------------')
    return HttpResponse(s)

# 印章管理审核（重审）
def stamp_audit(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-stamp_audit-begin---------------------------')

    datainfo = reqest_body.get('datainfo')
    id = datainfo.get('id')
    uid = reqest_body.get('uid')
    checksum = reqest_body.get('checksum')

    # 先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    cursor = connection.cursor()
    sql = "select ROLE_ID from sys_user_role where USER_ID = %s"
    cursor.execute(sql, uid)
    log.info(sql % uid)
    rows = cursor.fetchall()
    rows = str(rows)
    if rows:
        if ("administrator" in rows) or ("lqkj_qiguan" in rows):
            state_sql = "select examine_verify from yw_stamp where id = %s"
            cursor.execute(state_sql,id)
            state = cursor.fetchone()[0]
            if state == '未审核':
                set_state_sql = "update yw_stamp set examine_verify='已审核' where id = %s"
                cursor.execute(set_state_sql,id)
            else:
                reset_state_sql = "update yw_stamp set examine_verify='未审核' where id = %s"
                cursor.execute(reset_state_sql, id)
        else:
            s = public.setrespinfo({"respcode": "900009", "respmsg": "没有操作权限!"})
            return HttpResponse(s)
    cursor.close()
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-stamp_audit-end---------------------------')
    return HttpResponse(s)

#打开票据修改页面
def open_marketentry(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-open_marketentry-begin---------------------------')

    datainfo = reqest_body.get('datainfo')
    infoid = datainfo.get('id')
    print(datainfo)
    uid=reqest_body.get('uid')
    checksum=reqest_body.get('checksum')
    codeflag = datainfo.get('code_num',None)
    if codeflag:
        code = '1'
    else:
        code = '2'

    #先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "url": "%sMarketEntry?menu_id=104&uid=%s&checksum=%s&code=%s&infoid=%s"%(request.META['HTTP_ORIGIN']+'/',uid,checksum,code,infoid),  # 预览-返回url打开新页面
    }
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-open_marketentry-end---------------------------')
    return HttpResponse(s)


#校验用户组
def checkGroup(uid,group):
    log = public.logger
    cursor = connection.cursor()
    sql="select * from sys_user_role where user_id=%s and ROLE_ID=%s"
    log.info(sql%(uid,group))
    cursor.execute(sql,(uid,group) )
    rows = cursor.fetchall()
    if rows:
        return True
    return False


#获取申请用车审批状态
def getApplyCarStatus(id):
    log = public.logger
    cursor = connection.cursor()
    sql="select `status` from yw_workflow_apply_car where id=%s"
    log.info(sql % id)
    cursor.execute(sql,id)
    row = cursor.fetchone()
    if row:
        return row[0]
    return None


#用车申请审批通过
@public.fun_log_wrapper
def apply_car_pass(request, reqest_body):
    log = public.logger
    datainfo = reqest_body.get('datainfo')
    uid=reqest_body.get('uid')
    id=datainfo.get('id')
    if not checkGroup(uid,'lqkj_qiguan'):
        #没有企管部权限 返回错误
        jsondata = {
            "respcode": "900009",
            "respmsg": "没有操作权限",
            "trantype": reqest_body.get('trantype', None),
        }
        s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
        log.info(s)
        return HttpResponse(s)
    if getApplyCarStatus(id)=='3':
        jsondata = {
            "respcode": "655350",
            "respmsg": "已归还不能再更改状态",
            "trantype": reqest_body.get('trantype', None),
        }
        s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
        log.info(s)
        return HttpResponse(s)
    cursor = connection.cursor()
    sql="update yw_workflow_apply_car set `status`='1' where id=%s"
    log.info(sql % id)
    cursor.execute(sql, id)
    jsondata = {
        "respcode": "000000",
        "respmsg": "已通过申请",
        "trantype": reqest_body.get('trantype', None),
    }
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    return HttpResponse(s)


#用车申请审批拒绝
@public.fun_log_wrapper
def apply_car_fail(request, reqest_body):
    log = public.logger
    datainfo = reqest_body.get('datainfo')
    uid = reqest_body.get('uid')
    id = datainfo.get('id')
    if not checkGroup(uid, 'lqkj_qiguan'):
        # 没有企管部权限 返回错误
        jsondata = {
            "respcode": "900009",
            "respmsg": "没有操作权限",
            "trantype": reqest_body.get('trantype', None),
        }
        s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
        log.info(s)
        return HttpResponse(s)
    if getApplyCarStatus(id)=='3':
        jsondata = {
            "respcode": "655350",
            "respmsg": "已归还不能再更改状态",
            "trantype": reqest_body.get('trantype', None),
        }
        s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
        log.info(s)
        return HttpResponse(s)
    cursor = connection.cursor()
    sql = "update yw_workflow_apply_car set `status`='2',isend='1' where id=%s"
    log.info(sql % id)
    cursor.execute(sql, id)
    jsondata = {
        "respcode": "000000",
        "respmsg": "已拒绝申请",
        "trantype": reqest_body.get('trantype', None),
    }
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    return HttpResponse(s)

#用车申请归还
@public.fun_log_wrapper
def apply_car_return(request, reqest_body):
    log = public.logger
    datainfo = reqest_body.get('datainfo')
    uid = reqest_body.get('uid')
    id = datainfo.get('id')
    if not checkGroup(uid, 'lqkj_qiguan'):
        # 没有企管部权限 返回错误
        jsondata = {
            "respcode": "900009",
            "respmsg": "没有操作权限",
            "trantype": reqest_body.get('trantype', None),
        }
        s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
        log.info(s)
        return HttpResponse(s)
    if getApplyCarStatus(id)=='3':
        jsondata = {
            "respcode": "655350",
            "respmsg": "已归还不能再更改状态",
            "trantype": reqest_body.get('trantype', None),
        }
        s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
        log.info(s)
        return HttpResponse(s)
    cursor = connection.cursor()
    sql = "update yw_workflow_apply_car set `status`='3',isend='1' where id=%s"
    log.info(sql % id)
    cursor.execute(sql, id)
    jsondata = {
        "respcode": "000000",
        "respmsg": "已归还成功",
        "trantype": reqest_body.get('trantype', None),
    }
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    return HttpResponse(s)

#ERP制令单数据同步
def sync_erp_mo(request, reqest_body):
    log = public.logger

    datainfo = reqest_body.get('datainfo')
    orderid = datainfo.get('order_id') #制令单号
    db_id = datainfo.get('id') #主键ID

    # 获取制品名称
    try:
        sqlserver_conn = pymssql.connect(server='10.10.1.250', user='sa', password='luyao123KEJI',
                                         database="db_18", timeout=20, autocommit=True)  # 获取连接
        cursor = sqlserver_conn.cursor()  # 获取光标
    except Exception as ex:
        log.info(str(ex))
    # log.info('连接远程数据库成功:' + str(datetime.datetime.now()))

    try:
        # log.info("根据品号查询品名:" + sql)
        sql="select SO_NO,MRP_NO,REM,QTY from MF_MO where MO_NO='%s'" % orderid
        log.info(sql)
        cursor.execute(sql)
        row=cursor.fetchone()
        if row:
            plan_no=row[0]
            prd_no=row[1]
            if row[2]:
                rem=row[2]
            else:
                rem=''
            plan_num=row[3]
        else:
            sqlserver_conn.close()
            s = public.setrespinfo({"respcode": "381221", "respmsg": "制令单号在ERP系统中不存在!"})
            return HttpResponse(s)
        sql = "select NAME from PRDT where PRD_NO='%s'" % prd_no
        cursor.execute(sql)
        row = cursor.fetchone()
        prd_name = row[0]

        sqlserver_conn.close()
    except Exception as ex:
        log.info('select erpdata ERROR!'+ str(ex) )
        sqlserver_conn.close()
        s = public.setrespinfo({"respcode": "381222", "respmsg": "查询ERP数据错误!"})
        return HttpResponse(s)

    #更新本地表数据
    cur = connection.cursor()
    sql = "update yw_project_plan_info set sync_flag='1',plan_id='%s',prd_no='%s',prd_name='%s',plan_num='%s',msg_info='%s' where id=%s" \
          % (plan_no, prd_no, prd_name, plan_num, rem, db_id)
    log.info(sql)
    cur.execute(sql)

    jsondata = {
        "respcode": "000000",
        "respmsg": "根据制令单号从ERP同步数据成功",
        "trantype": reqest_body.get('trantype', None),
    }
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    return HttpResponse(s)

