from django.shortcuts import HttpResponse
import json
import datetime
from admin_app import public
from admin_app import models
from django.db import connection, transaction
import os
import base64
import shutil
import time


##联桥科技oa接口
def main(request):
    if request.method == "POST":
        log = public.logger
        #请求body转为json
        tmp=request.body
        tmp=tmp.decode(encoding='utf-8')
        reqest_body=json.loads(tmp)

        trantype=reqest_body['trantype']
        log.info('trantype=[%s]' % trantype)
        if trantype == 'approval':  #我的审批
            resp = approval(request, reqest_body)
        elif trantype == 'getApproval':  #获取审批信息
            resp = getApproval(request, reqest_body)
        elif trantype == 'getFlowDetail':  #获取流转记录
            resp = getFlowDetail(request, reqest_body)
        elif trantype == 'getApplyInfo':  #获取申请信息
            resp = getApplyInfo(request, reqest_body)
        elif trantype == 'createApplyInfo':  #发起申请信息
            resp = createApplyInfo(request, reqest_body)
        elif trantype == 'getApplyPeopleList':  #获取处理人列表
            resp = getApplyPeopleList(request, reqest_body)
        elif trantype == 'PsFilesUpload':
            resp = PsFilesUpload(request, reqest_body)
        elif trantype == 'PsFilesGet':
            resp = PsFilesGet(request, reqest_body)
        elif trantype == 'PsFilesDownload':
            resp = PsFilesDownload(request, reqest_body)
        else:
            s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
            resp = HttpResponse(s)
    elif request.method == "GET":
        s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
        resp = HttpResponse(s)

    return resp



#获取审批信息
def getApproval(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjoa-getApproval-begin---------------------------')

    user_id=reqest_body.get('uid',None)
    info_id=reqest_body.get('info_id',None)

    cur = connection.cursor()

    sql = "select id,tran_date,result,content,filelist,user_id,plan_date,success_date,success_flag,info_id from yw_workflow_detail where info_id=%s and user_id=%s"
    cur.execute(sql, (info_id, user_id))
    row = cur.fetchone()
    form = None
    if row:
        form={}
        form['id']=row[0]
        result=row[2]
        filelist=row[4]
        content=row[3]
        success_flag=row[8]
        plan_date=row[6]

        form['remarks']=content
        form['planEndTime']=plan_date.strftime('%Y-%m-%d %H:%M:%S')

        if result=='1':
            form['result']='同意'
        elif result=='0':
            form['result'] = '不同意'
        else:
            form['result']=''

        if success_flag=='1':
            form['flag']='已完成'
        elif success_flag=='0':
            form['flag']='处理中'
        else:
            form['flag']=''
        if filelist:
            fileids=filelist.split(',')
            resp_filelist=[]
            for fileid in fileids:
                temp={}
                sql='select id,file_name from yw_workflow_file where id=%s'
                cur.execute(sql, (fileid))
                row = cur.fetchone()
                temp['id']=row[0]
                temp['name']=row[1]
                resp_filelist.append(temp)
            form['filelist']=resp_filelist
        else:
            form['filelist']=[]

    sql='select id from yw_workflow_handle where infoid=%s and handlerid=%s'
    cur.execute(sql, (info_id, user_id))
    row = cur.fetchone()
    if row:
        disabled = 0
    else:
        disabled = 1  # 不允许提交


    cur.close()

    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "form":form,
        "disabled":disabled,
    }
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjoa-getApproval-end---------------------------')
    return HttpResponse(s)


#审批接口
def approval(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjoa-approval-begin---------------------------')

    user_id = reqest_body.get('uid', None)
    info_id = reqest_body.get('info_id', None)


    form=reqest_body.get('form',None)

    if form['result']=='同意':
        result='1'
    elif form['result']=='不同意':
        result='0'

    filelist=''
    for item in form['filelist']:
        filelist+='%s,'%item['id']
    filelist=filelist[:-1]
    content=form['remarks']
    if form['flag']=='处理中':
        success_flag='0'
    elif form['flag']=='已完成':
        success_flag='1'

    plan_date=form['planEndTime']
    if not plan_date:
        plan_date=None
    tran_date=datetime.datetime.now()


    cur = connection.cursor()

    sql = 'select id from yw_workflow_handle where infoid=%s and handlerid=%s'
    cur.execute(sql, (info_id, user_id))
    row = cur.fetchone()
    if row:
        if form['id']:  # 有id 更新
            id = form['id']
            sql = "update yw_workflow_detail set tran_date=%s,result=%s,content=%s,filelist=%s,user_id=%s,plan_date=%s,success_flag=%s,info_id=%s where id=%s"
            res = cur.execute(sql,
                              (tran_date, result, content, filelist, user_id, plan_date, success_flag, info_id, id))
        else:  # 没id 新增
            sql = "insert into yw_workflow_detail(tran_date,result,content,filelist,user_id,plan_date,success_flag,info_id) value(%s,%s,%s,%s,%s,%s,%s,%s)"
            res = cur.execute(sql, (tran_date, result, content, filelist, user_id, plan_date, success_flag, info_id))
            id = cur.lastrowid
        jsondata = {
            "respcode": "000000",
            "respmsg": "交易成功",
            "trantype": reqest_body.get('trantype', None),
            "id": id
        }
    else:
        jsondata = {
            "respcode": "12345",
            "respmsg": "没有权限",
            "trantype": reqest_body.get('trantype', None),
        }


    cur.close()


    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjoa-approval-end---------------------------')
    return HttpResponse(s)


#获取流程记录
def getFlowDetail(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjoa-getFlowDetail-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "detail":[]
    }

    info_id=reqest_body.get('info_id',None)
    cur = connection.cursor()
    sql = "select A.id,A.tran_date,A.result,A.content,A.filelist,A.user_id,A.plan_date,A.success_date,A.success_flag,A.info_id,B.USER_NAME from yw_workflow_detail A LEFT JOIN irsadmin_user B on A.user_id=B.USER_ID where info_id=%s"
    cur.execute(sql, info_id)
    rows = cur.fetchall()
    detail=[]
    for row in rows:
        temp={}
        temp['depart']='人事部'
        temp['people']=row[10]
        if row[2]=='1':
            temp['result']='同意'
        elif row[2]=='0':
            temp['result']='不同意'
        filelist=row[4].split(',')
        temp['enclosure']=[]
        for fileid in filelist:
            if not fileid:
                continue
            tempfile={}
            tempfile['id']=fileid
            sql = "select * from yw_workflow_file where id=%s"
            cur.execute(sql,fileid)
            rows2 = cur.fetchone()
            if rows2:
                tempfile['name']=rows2[2]
            else:
                tempfile['name']=''
            temp['enclosure'].append(tempfile)

        temp['remarks']=row[3]
        temp['evaltime']=row[1]
        temp['plantime']=row[6]
        temp['endtime']=row[7]
        if row[8]=='0':
            temp['flag']='处理中'
        elif row[8]=='1':
            temp['flag']='已完成'
        detail.append(temp)


    cur.close()
    jsondata['detail']=detail


    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjoa-getFlowDetail-end---------------------------')
    return HttpResponse(s)


#获取申请信息
def getApplyInfo(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjoa-getApplyInfo-begin---------------------------')

    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "info": []
    }

    info_id=reqest_body.get('info_id')

    cur = connection.cursor()
    sql = "select A.id,A.tran_date,A.user_id,A.tran_type,A.title,A.state,A.filelist,A.remarks,A.important,B.USER_NAME from yw_workflow_info A LEFT JOIN irsadmin_user B on A.user_id=B.USER_ID where id=%s"
    cur.execute(sql, info_id)
    row = cur.fetchone()
    important={
        '1':'低',
        '2':'中',
        '3':'高'
    }
    info=[]
    if row:
        info.append({'name': '流水号', 'info': '123456789'})
        info.append({'name': '主题', 'info': row[4]})
        info.append({'name': '分类', 'info': row[3]})
        info.append({'name': '发起人', 'info': row[9]})
        info.append({'name': '优先程度', 'info': important[row[8]]})
        info.append({'name': '申请时间', 'info': row[1]})
        filelist = []
        if row[6]:
            fileidlist=row[6].split(',')
            for fileid in fileidlist:
                tempfile={}
                sql = "select * from yw_workflow_file where id=%s"
                cur.execute(sql, int(fileid))
                row2 = cur.fetchone()
                tempfile['id']=row2[0]
                if row2:
                    tempfile['name'] = row2[2]
                else:
                    tempfile['name'] = ''
                filelist.append(tempfile)
        info.append({'name': '附件', 'info': filelist})
        info.append({'name': '备注', 'info': row[7]})

    jsondata['info']=info

    cur.close()


    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjoa-getApplyInfo-end---------------------------')
    return HttpResponse(s)


#创建申请信息
def createApplyInfo(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjoa-createApplyInfo-begin---------------------------')


    form=reqest_body.get('form')
    title=form.get('title')
    type=form.get('type')
    important=form.get('important')
    remarks=form.get('remarks')
    filelist = ','.join(form.get('filelist',[]))
    tran_date = datetime.datetime.now()
    user_id = reqest_body.get('uid')
    ptlsh='1234567890'#流水号



    cur = connection.cursor()
    sql = "insert into yw_workflow_info(tran_date,user_id,tran_type,title,state,filelist,remarks,important,ptlsh) value(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    res = cur.execute(sql, (tran_date, user_id, type, title, '1', filelist, remarks, important,ptlsh))
    id = cur.lastrowid

    #插入处理人表
    handlePeoples = form.get('tags')
    for item in handlePeoples:
        userid=item.get('userid')
        sql='insert into yw_workflow_handle(infoid,userid,handlerid) value(%s,%s,%s)'
        res = cur.execute(sql, (id,user_id,userid))


    cur.close()
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "id":id
    }

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjoa-createApplyInfo-end---------------------------')
    return HttpResponse(s)


#获取处理人列表
def getApplyPeopleList(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjoa-getApplyPeopleList-begin---------------------------')

    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "peoples": [],
        "history":[]
    }

    cur = connection.cursor()
    #查询所有用户（过滤掉超级管理员）
    sql = "select USER_ID,USER_NAME from irsadmin_user where USER_ID not in (select USER_ID from irsadmin_user_rule where ROLE_ID='administrator')"
    cur.execute(sql)
    rows = cur.fetchall()

    peoples=[]
    for item in rows:
        temp={}
        temp['userid']=item[0]
        temp['value']=item[1]
        peoples.append(temp)
    jsondata['peoples'] = peoples

    sql = "select DISTINCT A.handlerid,B.user_name from yw_workflow_handle A left join irsadmin_user B on A.handlerid=B.user_id "
    cur.execute(sql)
    rows = cur.fetchall()

    history = []
    for item in rows:
        temp = {}
        temp['userid'] = item[0]
        temp['value'] = item[1]#username
        history.append(temp)
    jsondata['history'] = history
    cur.close()
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjoa-getApplyPeopleList-end---------------------------')
    return HttpResponse(s)


#根据评审单号获取年月
def getPsYearMonth(ps_id):
    year = '20%s' % ps_id[2:4]
    month = ps_id[4:6].lstrip('0')
    return year,month

#根据评审单号获取计划号
def getPlanidByPsid(ps_id):
    cur = connection.cursor()
    sql = "select plan_number from yw_bill_review_form_head where head_id='%s'" % ps_id
    cur.execute(sql)
    row = cur.fetchone()
    if row:
        return row[0]
    return None

#将一个文件夹下的文件全部移到另一个文件夹下（保留子路径） 例：movePath('./dir/b','./dir/a')
def movePath(fromPath,toPath):
    if not os.path.exists(fromPath) or not os.path.exists(toPath):
        return
    filelist=os.listdir(fromPath)
    for filename in filelist:
        fromFile=fromPath+'/'+filename
        toFile=toPath+'/'+filename
        if os.path.exists(toFile):#重复
            if os.path.isdir(fromFile):#是文件夹
                movePath(fromFile,toFile)
                os.system('rm -rf %s'%fromFile)
        else:
            shutil.move(fromPath+'/'+filename,toPath)
    os.system('rm -rf %s' % fromPath)


#将计划号关联的评审单号移入计划号文件夹下
def movePs2Plan(log,plan_id,ps_id):
    root = '/home/admin/lqkj_admin/SVN/项目外来文件'
    year, month = getPsYearMonth(ps_id)
    # 根据计划号反查评审单号
    cur = connection.cursor()
    sql = "select head_id from yw_bill_review_form_head where plan_number='%s'" % plan_id
    cur.execute(sql)
    rows = cur.fetchall()
    ps_ids = []
    if rows:
        for row in rows:
            ps_ids.append(row[0])
    # 将评审单号下的文件移入计划单号下
    new_path = '%s/%s年订单目录/%s月订单详情/%s/' % (root, year, month, plan_id)
    if not os.path.exists(new_path):  # 路径不存在则创建
        os.mkdir(new_path)
    log.info('ps_ids=%s' % ps_ids)
    for pid in ps_ids:
        old_path = '%s/%s年订单目录/%s月订单详情/%s/' % (root, year, month, pid)
        movePath(old_path[:-1], new_path[:-1])
        # filelist = os.listdir(old_path)
        # for fileitem in filelist:
        #     movefilepath = old_path + fileitem
        #     log.info('移动文件：%s->%s' % (movefilepath, new_path))
        #     shutil.move(movefilepath, new_path)
        # # 删除目录
        # os.system('rm -rf %s' % old_path[:-1])

#根据ps_id获取附件路径
def getPathByPsid(ps_id):
    root = '/home/admin/lqkj_admin/SVN/项目外来文件'
    year, month = getPsYearMonth(ps_id)
    plan_id = getPlanidByPsid(ps_id)
    if plan_id[0:2]!='JH':
        filepath = '%s/%s年订单目录/%s月订单详情/%s/未审核/' % (root, year, month, ps_id)
    else:
        filepath = '%s/%s年订单目录/%s月订单详情/%s/未审核/' % (root, year, month, plan_id)
    return filepath

#文件资源上传,OA评审单上的文件，上传到指定目录
def PsFilesUpload(request, reqest_body):
    log = public.logger
    log.info('----------------------fileup-files_upload-begin---------------------------')
    filename=reqest_body.get('filename',None)
    if filename==None or len(filename)<2:
        s = public.setrespinfo({"respcode": "323311", "respmsg": "上送文件名错误"})
        return s
    uid=reqest_body.get('uid',None)
    ps_id=reqest_body.get('ps_id')
    if ps_id==None:
        s = public.setrespinfo({"respcode": "323313", "respmsg": "评审单号有误"})
        return s
    #判断评审单是否提交（查数据库）
    plan_id=getPlanidByPsid(ps_id)
    if not plan_id:
        s = public.setrespinfo({"respcode": "323314", "respmsg": "请先提交评审单"})
        return s
    #开始保存文件
    file = reqest_body.get('file', None)
    if file == None:
        s = public.setrespinfo({"respcode": "323312", "respmsg": "上送文件内容错误"})
        return s

    #################开始处理#################
    # 保存文件到本地文件上传目录
    root = '/home/admin/lqkj_admin/SVN/项目外来文件'
    year, month = getPsYearMonth(ps_id)
    filepath = '%s/%s年订单目录/%s月订单详情/%s/未审核/' % (root, year, month, ps_id)
    if not os.path.exists(filepath):  # 如果路径不存在
        os.makedirs(filepath)
    file_name = open(filepath + filename, 'wb')  # 有重名的会覆盖
    file_name.write(file.encode('raw_unicode_escape'))  # 前端在json报文中，把二进制当字符串上送了，可以这样转换
    file_name.close()

    #如果有计划号，移动文件到计划号文件夹
    if plan_id[0:2] != 'JH':
        plan_id = None
    if plan_id:
        movePs2Plan(log,plan_id,ps_id)

    data = {
        "respcode": "000000",
        "respmsg": "上传成功",
        "trantype": reqest_body.get('trantype', None),
        'filename':filename
    }

    s = json.dumps(data, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info('----------------------fileup-files_upload-end---------------------------')
    return HttpResponse(s)



#文件资源获取,获取OA评审单上的文件
def PsFilesGet(request, reqest_body):
    log = public.logger
    log.info('----------------------fileup-PsFilesGet-begin---------------------------')
    uid=reqest_body.get('uid',None)
    ps_id=reqest_body.get('ps_id')
    if ps_id==None:
        s = public.setrespinfo({"respcode": "323313", "respmsg": "评审单号有误"})
        return s
    #根据评审单号获取附件存放路径
    filepath=getPathByPsid(ps_id)
 
    noverify_file_list=os.listdir(filepath)
    verify_file_list=os.listdir(filepath.replace('/未审核',''))
    verify_file_list.remove('未审核')

    data = {
        "respcode": "000000",
        "respmsg": "上传成功",
        "trantype": reqest_body.get('trantype', None),
        'noverify_file_list':noverify_file_list,
        'verify_file_list':verify_file_list
    }

    s = json.dumps(data, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info('----------------------fileup-PsFilesGet-end---------------------------')
    return HttpResponse(s)


#文件资源下载，下载OA评审单上的文件
def PsFilesDownload(request, reqest_body):
    log = public.logger
    log.info('----------------------Admin-PsFilesDownload-begin---------------------------')
    ps_id=reqest_body.get('ps_id',None)
    file_name=reqest_body.get('file_name',None)
    if not ps_id or not file_name:
        s = public.setrespinfo({"respcode": "323311", "respmsg": "请求参数有误"})
        return s

    filepath=getPathByPsid(ps_id).replace('/未审核','')
    # filepath = '%s/%s年订单目录/%s月订单详情/%s/' % (root, year, month, ps_id)
    file = open(filepath+file_name, 'rb')
    # response = HttpResponse(file)

    data = {
        "respcode": "000000",
        "trantype": reqest_body.get('trantype', None),
        "data": base64.b64encode(file.read()).decode(),
        "file_name":file_name
    }

    s = json.dumps(data)
    # response['Content-Type'] = 'application/octet-stream'
    # response['Content-Disposition'] = 'attachment;filename="%s"'%filename
    return HttpResponse(s)