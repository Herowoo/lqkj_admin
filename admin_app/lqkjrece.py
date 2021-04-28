from django.shortcuts import HttpResponse
from django.db import connection
import json
from admin_app import public
from admin_app import models
import datetime
from decimal import Decimal

def main(request):
    log = public.logger
    log.info('----------------------lqkjrece-begin---------------------------')
    if request.method == "POST": #POST请求
        #请求body转为json
        tmp=request.body
        tmp=tmp.decode(encoding='utf-8')
        request_body=json.loads(tmp)
        trantype=request_body['trantype']
        log.info('trantype=[%s]' % trantype)
        fun_name = trantype
        if globals().get(fun_name):
            resp = globals()[fun_name](request, request_body)
        else:
            s = public.setrespinfo({"respcode": "100000", "respmsg": "api error! lqkjerp!"})
            resp = HttpResponse(s)
    elif request.method == "GET": #GET请求
        s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
        resp = HttpResponse(s)
    log.info('----------------------lqkjrece-end---------------------------')
    return resp

#函数装饰器
def func_wrapper(func):
    def wrapper(request, request_body,*args,**kwargs):
        log = public.logger
        fun_name=func.__name__
        log.info('----------------------lqkjrece-%s-begin---------------------------'%fun_name)
        jsondata = {
            "respcode": "000000",
            "respmsg": "交易成功",
            "trantype": request_body.get('trantype', None),
        }
        res=func(jsondata,log,request, request_body,*args,**kwargs)
        s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
        log.info(s)
        log.info('----------------------lqkjrece-%s-end---------------------------'%fun_name)
        return HttpResponse(s)
    return wrapper

# 获取客户列表
@func_wrapper
def get_cuslist(jsondata, log, request, request_body):
    user_id = request_body.get('uid', None)

    cus_sql = "select cre_id,cus_name from yw_rece2_customer_info where state='1'"
    cursor = connection.cursor()
    log.info(cus_sql)
    cursor.execute(cus_sql)
    cus_rows = cursor.fetchall()
    cuslist = []
    if cus_rows:
        for item in cus_rows:
            tmpdict = {
                "value":item[0],
                "label":item[1]
            }
            cuslist.append(tmpdict)
    jsondata["cuslist"] = cuslist

# 获取客户订单列表
@func_wrapper
def get_orderlist(jsondata, log, request, request_body):
    user_id = request_body.get('uid', None)
    cre_id = request_body.get('cre_id',None)
    order_sql = "select order_id,order_info from yw_rece2_order_info where order_state='0' and order_cre_id=%s"
    cursor = connection.cursor()
    log.info(order_sql%cre_id)
    cursor.execute(order_sql,cre_id)
    order_rows = cursor.fetchall()
    waitselect = []
    if order_rows:
        for item in order_rows:
            tmpdict = {
                "orderid":item[0],
                "label":item[1]
            }
            waitselect.append(tmpdict)
    jsondata["waitselect"] = waitselect

# 提交票据信息
@func_wrapper
def hand_invoform(jsondata,log,request, request_body):
    user_id = request_body.get('uid',None)
    invoForm = request_body.get('invoForm',None)
    flag = request_body.get('flag',None)

    if len(invoForm["orderlist"]) ==0 and flag==False:
        jsondata['flag'] = True
        jsondata['alert'] = '未关联订单号, 是否继续提交?'
        return
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if invoForm["codetype"] =='1': # 发票
        con_order = ','.join(invoForm["orderlist"])
        if invoForm["handdate"]=='':
            handdate = None
        else:
            handdate = invoForm["handdate"]
        insert_sql = "INSERT INTO yw_rece2_invoice_info(id, code_tran_date, code_upd_date, code_enter_person, cre_id, code_pay_type, code_num,code_date,code_amo_money, code_annex, con_order_id, code_hand_date,remarks,code_state) " \
                     "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)"
        tmp = (None,nowTime,nowTime,user_id,invoForm["customer"],invoForm["paytype"],invoForm["codenum"],invoForm["codedate"],
               invoForm["codemoney"],invoForm["annex"],con_order,handdate,invoForm["remarks"],'1')
        cursor = connection.cursor()
        log.info(insert_sql % tmp)
        cursor.execute(insert_sql, tmp)
        jsondata['flag'] = False
        jsondata["respmsg"] = '提交成功'
    else: # 回款
        con_order = ','.join(invoForm["orderlist"])
        if invoForm["handdate"]=='':
            handdate = None
        else:
            handdate = invoForm["handdate"]
        insert_sql = "INSERT INTO yw_rece2_return_info(id, ret_tran_date, ret_upd_date, ret_enter_person, cre_id, ret_pay_type, ret_num,ret_date,ret_amo_money, ret_annex, con_order_id, ret_hand_date,remarks,ret_state) " \
                     "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)"
        tmp = (None, nowTime, nowTime,user_id, invoForm["customer"], invoForm["paytype"], invoForm["serialnum"], invoForm["retdate"],
        invoForm["retmoney"], invoForm["annex"], con_order, handdate, invoForm["remarks"], '1')
        cursor = connection.cursor()
        log.info(insert_sql% tmp)
        cursor.execute(insert_sql,tmp)
        jsondata['flag'] = False
        jsondata["respmsg"] = '提交成功'

# 修改票据信息
@func_wrapper
def upd_invoform(jsondata,log,request, request_body):
    user_id = request_body.get('uid',None)
    invoForm = request_body.get('invoForm',None)
    flag = request_body.get('flag',None)
    infoid = request_body.get('infoid',None)
    code = request_body.get('code',None)

    if len(invoForm["orderlist"]) ==0 and flag==False:
        jsondata['flag'] = True
        jsondata['alert'] = '未关联订单号, 是否继续提交?'
        return
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if code == '1':
        select_sql = "select cre_id, code_pay_type, code_num,code_date,code_amo_money, code_annex, con_order_id, code_hand_date,remarks " \
                     "from yw_rece2_invoice_info where id = %s"
        fieldlist = ["cre_id", "code_pay_type", "code_num", "code_date", "code_amo_money", "code_annex", "con_order_id",
                     "code_hand_date", "remarks"]
        cursor = connection.cursor()
        log.info(select_sql % infoid)
        cursor.execute(select_sql, infoid)
        row = cursor.fetchone()
        tmpstr = ''
        tuple = ()
        if row:
            i = 0
            del invoForm['codetype']
            invoForm['codemoney'] = Decimal(invoForm['codemoney']).quantize(Decimal('0.000000'))
            invoForm['orderlist'] = ','.join(invoForm["orderlist"])
            for key in invoForm:
                if str(row[i]) != str(invoForm[key]):
                    tmpstr = tmpstr + fieldlist[i] + "=%s,"
                    tuple = tuple + (invoForm.get(key, None),)
                i = i + 1
            if len(tmpstr) != 0:
                tuple = (nowTime,) + tuple + (infoid,)
                sql = "update yw_rece2_invoice_info set code_upd_date =%s," + tmpstr[:-1] + " where id =%s"
                cursor = connection.cursor()
                log.info(sql%tuple)
                cursor.execute(sql,tuple)
                jsondata['flag'] = False
                jsondata["respmsg"] = '修改成功'
            else:
                jsondata['flag'] = False
                jsondata["respmsg"] = '未做任何修改'
    else:
        select_sql = "select cre_id, ret_pay_type, ret_num,ret_date,ret_amo_money, ret_annex, con_order_id, ret_hand_date,remarks " \
                     "from yw_rece2_return_info where id = %s"
        fieldlist = ["cre_id", "ret_pay_type", "ret_num", "ret_date", "ret_amo_money", "ret_annex", "con_order_id",
                     "ret_hand_date", "remarks"]
        cursor = connection.cursor()
        log.info(select_sql % infoid)
        cursor.execute(select_sql, infoid)
        row = cursor.fetchone()
        tmpstr = ''
        tuple = ()
        if row:
            i = 0
            del invoForm['codetype']
            invoForm['retmoney'] = Decimal(invoForm['retmoney']).quantize(Decimal('0.000000'))
            invoForm['orderlist'] = ','.join(invoForm["orderlist"])
            for key in invoForm:
                if str(row[i]) != str(invoForm[key]):
                    tmpstr = tmpstr + fieldlist[i] + "=%s,"
                    tuple = tuple + (invoForm.get(key, None),)
                i = i + 1
            if len(tmpstr) != 0:
                tuple = (nowTime,) + tuple + (infoid,)
                sql = "update yw_rece2_return_info set ret_upd_date=%s," + tmpstr[:-1] + " where id =%s"
                cursor = connection.cursor()
                log.info(sql% tuple)
                cursor.execute(sql,tuple)
                jsondata['flag'] = False
                jsondata["respmsg"] = '修改成功'
            else:
                jsondata['flag'] = False
                jsondata["respmsg"] = '未做任何修改'

# 获取票据详情信息
@func_wrapper
def get_detail(jsondata, log, request, request_body):
    user_id = request_body.get('uid', None)
    infoid = request_body.get('infoid',None)
    code = request_body.get('code',None)
    invoForm = {}
    if code=='1':
        select_sql = "select cre_id, code_pay_type, code_num,code_date,code_amo_money, code_annex, con_order_id, code_hand_date,remarks " \
                     "from yw_rece2_invoice_info where id = %s"
        cursor = connection.cursor()
        log.info(select_sql % infoid)
        cursor.execute(select_sql, infoid)
        row= cursor.fetchone()
        if row:
            invoForm["customer"]=row[0]
            invoForm["codetype"]='1'
            invoForm["paytype"]=row[1]
            invoForm["codenum"]=row[2]
            invoForm["codedate"]=row[3]
            invoForm["codemoney"]=row[4]
            invoForm["annex"]=row[5]
            invoForm["orderlist"]=row[6].split(',')
            invoForm["handdate"]=row[7]
            invoForm["remarks"]=row[8]
        jsondata["invoForm"] = invoForm
    else:
        select_sql = "select cre_id, ret_pay_type, ret_num,ret_date,ret_amo_money, ret_annex, con_order_id, ret_hand_date,remarks " \
                     "from yw_rece2_return_info where id = %s"
        cursor = connection.cursor()
        log.info(select_sql % infoid)
        cursor.execute(select_sql, infoid)
        row = cursor.fetchone()
        if row:
            invoForm["customer"]=row[0]
            invoForm["codetype"]='2'
            invoForm["paytype"]=row[1]
            invoForm["serialnum"]=row[2]
            invoForm["retdate"]=row[3]
            invoForm["retmoney"]=row[4]
            invoForm["annex"]=row[5]
            invoForm["orderlist"]=row[6].split(',')
            invoForm["handdate"]=row[7]
            invoForm["remarks"]=row[8]
        jsondata["invoForm"] = invoForm


