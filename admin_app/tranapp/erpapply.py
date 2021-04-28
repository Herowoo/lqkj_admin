import sys
from django.shortcuts import render,redirect,HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime,time
from calendar import weekday,monthrange
from datetime import timedelta
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

# 新增物料申请添加页面
def add_material_show( request ):
    log = public.logger
    body = public.req_body
    head = public.req_head
    user_id = int(head.get('uid',None))
    form_id = body.get('form_id', '')
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    form_var_dict = {
        "launch_org":'',
        "org_list":[],
        "sponsor":user_id,
        "user_list":[],
        "tran_date":nowTime,
        "add_reason":'',
        "pro_tableData":[],
    }

    user_list,org_list = get_userlist_orglist(user_id)
    form_var_dict['user_list'] = user_list
    form_var_dict['org_list'] = org_list

    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            "form_var":form_var_dict,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 新增物料申请修改页面
def upd_material_show( request ):
    log = public.logger
    body = public.req_body
    head = public.req_head
    form_id = body.get('form_id', '')
    form_data = body.get('form_data', {})  # 可能为空
    if not form_data:
        form_data = body.get('form_var', {})
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    head_id = form_data['id']
    form_var_dict = {
        "id": head_id,
        "launch_org":form_data['launch_org'],
        "org_list":[],
        "sponsor":form_data['sponsor'],
        "user_list":[],
        "tran_date":form_data['tran_date'],
        "add_reason":form_data['add_reason'],
        "pro_tableData":[],
        "rev_tableData":[],
    }
    user_list, org_list = get_userlist_orglist(form_data['sponsor'])
    form_var_dict['user_list'] = user_list
    form_var_dict['org_list'] = org_list
    cur = connection.cursor()
    pro_tableData = []
    pro_sql = "select * from yw_erp_addmterial_probody where head_id=%s order by pro_id"
    cur.execute(pro_sql,head_id)
    rows = cur.fetchall()
    for row in rows:
        tmp_dict = {
            'pro_id':row[0],
            'head_id':row[1],
            'tran_date':row[2],
            'pro_name': row[3],
            'pro_band': row[4],
            'manufacturer': row[5],
            'pro_model': row[6],
            'pro_num': row[7],
            'big_class': row[8],
            'middle_class': row[9],
            'depot_type': row[10],
        }
        pro_tableData.append(tmp_dict)
    form_var_dict['pro_tableData'] = pro_tableData

    rev_tableData = []
    rev_sql = "select * from yw_erp_addmaterial_revbody where head_id=%s order by rev_id"
    cur.execute(rev_sql, head_id)
    rows = cur.fetchall()
    for row in rows:
        tmp_dict = {
            'rev_id': row[0],
            'head_id':row[1],
            'org_name': row[2],
            'content': row[3],
            'reviewer': row[4],
            'tran_date': row[5]
        }
        rev_tableData.append(tmp_dict)
    form_var_dict['rev_tableData'] = rev_tableData



    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            "form_var":form_var_dict,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

# 新增物料申请添加页面 保存数据接口
def save_material_info( request ):
    log = public.logger
    body = public.req_body
    head = public.req_head
    user_id = int(head.get('uid',None))
    form_id = body.get('form_id', '')
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    form_var = body.get('form_var', {})

    head_id = form_var.get('id',None)
    launch_org = form_var['launch_org'] # 发起部门
    sponsor = form_var['sponsor']
    add_reason = form_var['add_reason']
    pro_tableData = form_var['pro_tableData']
    rev_tableData = form_var['rev_tableData']

    if not launch_org or not sponsor or not add_reason:
        public.respcode, public.respmsg = "100801", "请填写完整信息!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    cur = connection.cursor()
    # head_id 不为空，数据插入更新前先清除历史数据
    del_head_sql = "delete from yw_erp_addmaterial_head where id=%s "
    del_probody_sql = "delete from yw_erp_addmterial_probody where head_id=%s "
    del_revbody_sql = "delete from yw_erp_addmaterial_revbody where head_id=%s "
    if head_id:
        cur.execute(del_head_sql,head_id)
        cur.execute(del_probody_sql,head_id)
        cur.execute(del_revbody_sql,head_id)


    head_id = None
    head_sql = "INSERT INTO yw_erp_addmaterial_head(id, tran_date, launch_org, sponsor, add_reason, status) VALUES (%s, %s, %s, %s, %s, %s);"
    pro_body_sql = "INSERT INTO yw_erp_addmterial_probody(pro_id, head_id, tran_date, pro_name, pro_band, manufacturer, pro_model, pro_num, big_class, middle_class, depot_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
    rev_body_sql = "INSERT INTO yw_erp_addmaterial_revbody(rev_id, head_id, org_name, content, reviewer, tran_date) VALUES (%s, %s, %s, %s, %s, %s);"
    cur.execute(head_sql,(None,nowTime,launch_org,sponsor,add_reason,'1'))
    head_id = cur.lastrowid
    # pro_body 数据插入
    for item in pro_tableData:
        pro_tuple = (None,head_id,nowTime,item['pro_name'],item['pro_band'],item['manufacturer'],item['pro_model'],item['pro_num'],item['big_class'],item['middle_class'],item['depot_type'])
        cur.execute(pro_body_sql,pro_tuple)

    for item in rev_tableData:
        if item['reviewer']:
            item['tran_date'] = nowTime
        else:
            item['tran_date'] = None
        rev_tuple = (None,head_id,item['org_name'],item['content'], item['reviewer'], item['tran_date'])
        cur.execute(rev_body_sql,rev_tuple)
    cur.close()

    public.respcode, public.respmsg = "000000", "保存成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            "form_var":form_var,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


 # 获取用户列表 和 用户所属部门列表
def get_userlist_orglist(user_id):
    user_org_sql = "select ORG_ID from sys_user_org where user_id=%s"
    org_sql = "select org_name from sys_org where org_id=%s "
    user_sql = "select USER_ID,USER_NAME from sys_user where user_id=%s"
    cur = connection.cursor()
    cur.execute(user_org_sql,user_id)
    rows = cur.fetchall()
    org_list = []
    for row in rows:
        cur.execute(org_sql,int(row[0]))
        item = cur.fetchone()
        tmp_dict = {
            'key': row[0],
            'value': '未知' if not item else item[0]
        }
        org_list.append(tmp_dict)
    cur.execute(user_sql,user_id)
    rows = cur.fetchall()
    user_list = []
    for item in rows:
        tmp_dict = {
            'key': item[0],
            'value': item[1]
        }
        user_list.append(tmp_dict)
    return user_list,org_list

# 一下为停用函数
# 新增物料申请添加页面
def add_material_show_bak( request ):
    log = public.logger
    body = public.req_body
    head = public.req_head
    user_id = int(head.get('uid',None))
    form_id = body.get('form_id', '')
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    form_var_dict = {
        "launch_org":'',
        "org_list":[],
        "sponsor":user_id,
        "user_list":[],
        "tran_date":nowTime,
        "add_reason":'',
        "pro_tableData":[],
        "rev_tableData":[],
    }

    user_list,org_list = get_userlist_orglist(user_id)
    form_var_dict['user_list'] = user_list
    form_var_dict['org_list'] = org_list

    seclist = ['采购部填写','研发部填写','质控部填写','工艺工程部填写','物控填写','总工填写']
    conlist = ['供应能力评估:','产品技术符合性:','样品检验结果:','','','']
    tmplist = []
    for index,item in enumerate(seclist):
        dict = {
            'org_name': item,
            'content':conlist[index],
            'reviewer':'',
            'tran_date':''
        }
        tmplist.append(dict)
    form_var_dict['rev_tableData'] = tmplist

    public.respcode, public.respmsg = "000000", "表单配置信息查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_id":form_id,
            "form_var":form_var_dict,
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo