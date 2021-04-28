import sys
from django.shortcuts import render,redirect,HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime
import pymssql

###########################################################################################################
#表单自定义按钮，发起交易
#add by litz, 2020.04.10
#
###########################################################################################################

#表单配置新增，主要是获取form_id
def form_data_testadd( request ):
    log = public.logger
    try:
        cur = connection.cursor()  # 创建游标
        cur.close() #关闭游标
        
    except Exception as ex:
        log.error("登记配置信息失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "100010", "登记配置信息失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return public.respinfo

    public.respcode, public.respmsg = "000000", "新增数据成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": { }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo


###########################################################################################################
# 表单自定义按钮，发起交易
# add by litz, 2020.04.10
#
###########################################################################################################

# 查询品号信息
def select_prd_info(request):
    log = public.logger
    form_var= public.req_body['form_var']
    prdno=form_var.get('prd_no')

    # 连接erp数据库
    sqlserver_conn = pymssql.connect(server='192.168.2.18',
                                     user='sa',
                                     password='luyao123KEJI',
                                     database="db_18",
                                     timeout=20,
                                     autocommit=True)  # sqlserver数据库链接句柄
    cursor = sqlserver_conn.cursor()  # 获取光标

    # 获取货品名称
    sql = " select NAME,IDX1,SPC,MRK, SUP1 from prdt where prd_no='%s'" % prdno
    log.info(sql, extra={'ptlsh': public.req_seq})
    cursor.execute(sql)
    row = cursor.fetchone()
    if row:
        prd_name = row[0]
        prd_type = row[1]
        prd_spc = row[2]
        prd_mrk = row[3]
        prd_sup1 = row[4]
    else:
        sqlserver_conn.close()
        log.info("货品代号不存在!", extra={'ptlsh': public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "200010", "货品代号不存在!"
        public.respinfo = HttpResponse(public.setrespinfo())
        return public.respinfo
    #获取中类名称
    sql = " select NAME from INDX where idx_no='%s'" % prd_type
    log.info(sql, extra={'ptlsh': public.req_seq})
    cursor.execute(sql)
    row = cursor.fetchone()
    if row:
        prd_type = row[0]

    #获取品牌名称
    sql = " select NAME from MARK where mark_no = '%s'" % prd_mrk
    log.info(sql, extra={'ptlsh': public.req_seq})
    cursor.execute(sql)
    row = cursor.fetchone()
    if row:
        prd_mrk = row[0]

    # 获取供应商信息
    sql = " select ISNULL(id_code, cus_no) from cust where cus_no = '%s'" % prd_sup1
    log.info(sql, extra={'ptlsh': public.req_seq})
    cursor.execute(sql)
    row = cursor.fetchone()
    if row:
        prd_sup1 = row[0]
    else:
        prd_sup1 = ''
    form_var['prd_name'] = prd_name
    form_var['prd_type'] = prd_type
    form_var['prd_spc'] = prd_spc
    form_var['prd_made'] = prd_mrk
    form_var['prd_suppliers'] = prd_sup1

    sqlserver_conn.close()

    public.respcode, public.respmsg = "000000", "数据查询成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {
            "form_var":form_var
        }
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#
# # 插入货品信息 ,,  --已作废，前端sql自己配置了。
# def insert_prd_info(request):
#     log = public.logger
#     form_var= public.req_body['form_var']
#     insert_fields=['prd_no','prd_name','prd_type','prd_spc','prd_made','prd_suppliers','prd_specifications','prd_recfile','prd_image','prd_sgsfile','prd_pack','user_id']
#     insert_dict={}
#     for field in insert_fields:
#         insert_dict[field]=form_var.get(field)
#         if field in ['prd_specifications','prd_recfile','prd_image','prd_sgsfile']:#如果是文件或图片 将列表变成逗号分隔字符串
#             if insert_dict[field]:
#                 insert_dict[field]=str(insert_dict[field])
#                 # insert_dict[field]=[str(item) for item in insert_dict[field]]
#                 # insert_dict[field]=','.join(insert_dict[field])
#     insert_dict['tran_date']=datetime.datetime.now()
#     insert_dict['user_id']=public.user_id
#
#     keys=','.join(insert_dict.keys())
#     values_seat=','.join(['%s' for i in range(len(insert_dict))])
#     values=tuple(insert_dict.values())
#     sql="insert into yw_lqerp_prd_info(%s) value(%s)"%(keys,values_seat)
#     log.info('sql=%s'%sql)
#     log.info('values=')
#     log.info(values)
#
#     try:
#         cur = connection.cursor()  # 创建游标
#         cur.execute(sql, values)
#     except Exception as ex:
#         log.error("新增数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
#         public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
#         public.respcode, public.respmsg = "100010", "新增数据失败!" + str(ex)
#         public.respinfo = HttpResponse(public.setrespinfo())
#
#     else:
#         public.respcode, public.respmsg = "000000", "新增数据成功!"
#         json_data = {
#             "HEAD": public.resphead_setvalue(),
#             "BODY": {
#                 "form_var": form_var
#             }
#         }
#         s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
#         public.respinfo = HttpResponse(s)
#     finally:
#         cur.close()  # 关闭游标
#
#     return public.respinfo


#
#
# # 更新货品信息,  --已作废，前端sql自己配置了。
# def update_prd_info(request):
#     log = public.logger
#     form_var= public.req_body['form_var']
#
#     log.info('public.req_body=%s'%public.req_body)
#     insert_fields = ['prd_no', 'prd_name', 'prd_type', 'prd_spc', 'prd_made', 'prd_suppliers', 'prd_specifications','prd_recfile', 'prd_image', 'prd_sgsfile', 'prd_pack', 'user_id']
#     insert_dict = {}
#     for field in insert_fields:
#         insert_dict[field] = form_var.get(field)
#         if field in ['prd_specifications', 'prd_recfile', 'prd_image', 'prd_sgsfile']:  # 如果是文件或图片 将列表变成逗号分隔字符串
#             if insert_dict[field]:
#                 insert_dict[field] = str(insert_dict[field])
#     insert_dict['tran_date'] = datetime.datetime.now()
#     insert_dict['user_id'] = public.user_id
#     id=form_var.get('id')
#     kvs=[key+'=%s' for key in insert_dict]
#     values=tuple(insert_dict.values())
#     sql="update yw_lqerp_prd_info set %s where id=%s"%(','.join(kvs),id)
#     log.info('sql=%s'%sql)
#
#     try:
#         cur = connection.cursor()  # 创建游标
#         cur.execute(sql, values)
#     except Exception as ex:
#         log.error("更新数据失败!" + str(ex), exc_info=True, extra={'ptlsh': public.req_seq})
#         public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
#         public.respcode, public.respmsg = "100010", "更新数据失败!" + str(ex)
#         public.respinfo = HttpResponse(public.setrespinfo())
#
#     else:
#         public.respcode, public.respmsg = "000000", "更新数据成功!"
#         json_data = {
#             "HEAD": public.resphead_setvalue(),
#             "BODY": {
#                 "form_var": form_var
#             }
#         }
#         s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
#         public.respinfo = HttpResponse(s)
#     finally:
#         cur.close()  # 关闭游标
#
#     return public.respinfo

