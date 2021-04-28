from django.shortcuts import HttpResponse
import json
import datetime
from  admin_app.sys import public
import os
import base64
import hashlib
from django.db import connection

###########################################################################################################
#文件接口  文件上传，下载，列表查看
#add by litz, 20200414
#
###########################################################################################################

#上传文件
def upload(request):
    log = public.logger

    if request.method != "POST":  # 仅支持POST调用
        public.respcode, public.respmsg = "100000", "api error! Support only POST!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    # 获取公共数据
    public.menu_id = request.POST.get('mid')
    public.user_id = request.POST.get('uid')
    public.tran_type = request.POST.get('tran_type')
    public.check_sum = request.POST.get('check_sum')
    public.req_seq = request.POST.get('req_seq')
    public.req_ip = request.META.get('REMOTE_ADDR')  # 请求IP地址

    # 获取文件信息,
    file_obj = request.FILES.get("file")

    filename_ext = file_obj.name.split('.')[1]
    # 获取文件内容到变量中
    filexx=b''
    for line in file_obj.chunks():
        filexx=filexx+line

    # 生成md5值的文件名
    m2 = hashlib.md5()
    m2.update(filexx)
    md5filename = m2.hexdigest() + '.' + filename_ext
    del filexx
    #判断文件是否存在,存在不处理，不存在则写处
    if not os.path.exists(public.localhome+"fileup/"+md5filename):
        # 写入本地指定目录
        with open(public.localhome+"fileup/"+md5filename, 'wb') as f:
            for line in file_obj.chunks():
                f.write(line)
        f.close()

    # 登记文件信息表
    cur = connection.cursor()  # 创建游标
    sql = "insert into sys_fileup(file_name,file_size,md5_name,tran_date,user_id, menu_id,content_type,req_seq,req_ip,state) " \
          "values('%s','%s','%s','%s','%s', '%s','%s','%s','%s','%s')" \
          % (file_obj.name, file_obj.size, md5filename, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             public.user_id, public.menu_id, file_obj.content_type, public.req_seq, public.req_ip, '1')
    # print(sql)
    cur.execute(sql)
    cur.execute("SELECT LAST_INSERT_ID()")  # 获取自增字段刚刚插入的ID
    connection.commit()
    row = cur.fetchone()
    if row:
        file_id = row[0]
    else:
        public.respcode, public.respmsg = "100132", "文件上传失败!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "上传文件成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "file_id": file_id
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#下载文件
def download(request):
    log = public.logger
    if request.method != "POST":  # 仅支持POST调用
        public.respcode, public.respmsg = "100000", "api error! Support only POST!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    reqest_body = json.loads(request.body.decode(encoding='utf-8'))  # 请求报文转换为JSON报文
    # 获取请求变量
    public.req_ip = request.META.get('REMOTE_ADDR')  # 请求IP地址
    public.req_head = reqest_body.get('HEAD', None)  # 请求报文头
    public.req_body = reqest_body.get('BODY', None)  # 请求报文体
    if public.req_head:
        public.menu_id = public.req_head.get('mid', '')  # 菜单ID
        public.user_id = public.req_head.get('uid', '')  # 请求用户ID
        public.check_sum = public.req_head.get('checksum', '')  # session校验码
        public.tran_type = public.req_head.get('tran_type', '')  # 交易代码
        public.req_seq = public.req_head.get('req_seq', '')  # 请求流水号
    else:
        log.info("请求报文头错误!", extra={'ptlsh': public.req_seq})
        public.respcode, public.respmsg = "100000", "请求报文头错误!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    # 获取文件信息,
    file_id=public.req_body.get("file_id")
    # print('file_id=',file_id)

    # 查询文件信息表
    cur = connection.cursor()  # 创建游标
    sql = "select file_name,md5_name,content_type from sys_fileup where file_id='%s' and state='1'" % (file_id)
    cur.execute(sql)
    row = cur.fetchone()
    if row:
        file_name = row[0]
        file_md5name = row[1]
        file_contenttype = row[2]
    else:
        public.respcode, public.respmsg = "100133", "文件不存在!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    fullpathfile=public.localhome+"fileup/"+file_md5name
    # print('fullpathfile=',fullpathfile)
    if not os.path.exists(fullpathfile):
        public.respcode, public.respmsg = "100134", "文件已过期!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    with open(public.localhome+"fileup/"+file_md5name, 'rb') as f:
        base64_data = base64.b64encode(f.read())
        file_base64 = base64_data.decode()

    public.respcode, public.respmsg = "000000", "文件下载成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "id": file_id,
            "name":file_name,
            "type":file_contenttype,
            "url":'data:%s;base64,%s' % (file_contenttype, file_base64),
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

