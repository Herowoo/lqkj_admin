import sys
from django.shortcuts import render,redirect,HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime
from admin_app.sys import public_db
import os
import requests
import xlrd

###########################################################################################################
#考勤数据处理
#add by litz, 2021.03.12
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


#考勤记录导入
def attend_detail_import(request):
    log = public.logger
    body=public.req_body
    form_var=body.get('form_var')
    excelfile = form_var.get('excelfile')
    month = form_var.get('import_month')
    if not excelfile:
        public.respcode, public.respmsg = "300332", "请先选择文件!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    if not month:
        public.respcode, public.respmsg = "300332", "请先选择考勤月份!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    try:
        cur = connection.cursor()  # 创建游标
        # 创建游标#根据fileid查询文件
        sql = "select md5_name from sys_fileup where file_id=%s"
        cur.execute(sql, excelfile)
        row = cur.fetchone()
        if not row:
            cur.close()  # 关闭游标
            public.respcode, public.respmsg = "300333", "文件不存在!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        kaoqin_file_md5name = row[0]
        # 检查文件是否存在
        kaoqin_fullpathfile = public.localhome + "fileup/" + kaoqin_file_md5name
        log.info("检查文件是否存在!" + str(kaoqin_fullpathfile), extra={'ptlsh': public.req_seq})
        if not os.path.exists(kaoqin_fullpathfile):
            public.respcode, public.respmsg = "100134", "文件已过期!"
            public.respinfo = HttpResponse(public.setrespinfo())
            return public.respinfo
        # 开始导入暂估入库数据
        sql = "delete from yw_workflow_attend_mx where month_id = %s"
        cur.execute(sql, month)  # 先清一下数据
        excel = xlrd.open_workbook(kaoqin_fullpathfile, formatting_info=True)
        ws = excel.sheet_by_index(0)
        # 获取行列数
        row = ws.nrows
        start_row = 1  # 从第二行开始读取数据 0是第一行
        total_row = row  # 总行数
        for i in range(start_row, total_row):
            sql = "insert into yw_workflow_attend_mx(month_id, seq_no, job_num, name, department, attend_time, attend_type) values(%s, %s, %s, %s, %s, %s, %s)"
            tuple_date = []
            tuple_date.append(month)
            for j in range(0, 6):
                tmp = ws.cell_value(rowx=i, colx=j)
                if not tmp:
                    tmp = 0
                tuple_date.append(tmp)
            tuple_date = tuple(tuple_date)
            # log.info(sql % tuple_date)
            cur.execute(sql, tuple_date)
        zjrk_total = total_row
        form_var['result'] = '导入结果：导入成功!共导入明细[%s]条' % ( zjrk_total)

        cur.close()  # 关闭游标
    except Exception as ex:
        log.error("交易失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "交易失败!" + str(ex)
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": body
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo
 