from django.shortcuts import HttpResponse
import json
import datetime
from admin_app import public
from admin_app import models
from django.db import connection, transaction


### 联桥科技结算报表接口
def main(request):
    if request.method == "POST":
        log = public.logger
        # 请求body转为json
        tmp = request.body
        tmp = tmp.decode(encoding='utf-8')
        reqest_body = json.loads(tmp)

        trantype = reqest_body['trantype']
        log.info('trantype=[%s]' % trantype)
        if trantype == 'initsetform':  # 初始化页面表单数据
            resp = initsetform(request, reqest_body)
        elif trantype == 'creallcusform':  # 市场所有客户结算报表
            resp = creallcusform(request, reqest_body)
        elif trantype == 'creonefacform':  # 采购单个客户结算报表
            resp = creonefacform(request, reqest_body)
        elif trantype == 'creallfacform':  # 采购单个客户结算报表
            resp = creallfacform(request, reqest_body)
        else:
            s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
            resp = HttpResponse(s)
    elif request.method == "GET":
        s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
        resp = HttpResponse(s)

    return resp


# 初始化页面(根据MENU_ID返回不同的表单数据)
def initsetform(reqest, reqest_body):
    log = public.logger
    log.info('----------------------Button-initsetform-begin---------------------------')

    uid = reqest_body.get('uid', None)
    checksum = reqest_body.get('checksum', None)
    menuid = reqest_body.get('menuid', None)
    creid = reqest_body.get('creid', None)

    # 先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }
    options = []
    if menuid == '165' and not creid:
        temp_options = [{
            'value': 'creallcusform',
            'label': '所有客户结算报表'
        }]
        options = temp_options
    elif menuid == '168' and not creid:
        temp_options = [{
            'value': 'creallfacform',
            'label': '所有厂商结算报表'
        }]
        options = temp_options
    elif menuid == '167' and creid:
        sql = "select fac_name from yw_payable_factory_info where cre_id=%s"
        cur = connection.cursor()
        cur.execute(sql,creid)
        row = cur.fetchone()
        cur.close()
        temp_options = [{
            'value': 'creonefacform',
            'label': creid +'-'+ row[0],
        }]
        options = temp_options

    jsondata["options"] = options

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-initsetform-end---------------------------')
    return HttpResponse(s)


# 市场部所有你客户结算报表
def creallcusform(reqest, reqest_body):
    log = public.logger
    log.info('----------------------Button-creallcusform-begin---------------------------')

    uid = reqest_body.get('uid', None)
    checksum = reqest_body.get('checksum', None)
    menuid = reqest_body.get('menuid', None)
    datevalue = reqest_body.get('datevalue', None)

    # 先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }
    # '发票金额总计：起始日期 到 截止日期 内来发票金额总计',
    # '已付款总计：起始日期 到 截止日期 内来付款金额总计（支票 & 电汇 & 电子承兑 & 纸质承兑）',
    # '扣款总计：起始日期 到 截止日期 内扣款金额总计',
    # 报表表格数据结构(初始化)
    formdata = {
       'head': {
           'title': 'XXXXXX报表',
           'value': '截止日期：',
       },
       'body': [
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           ],
       'explain': {
           'name': '说明：',
           'value': ['','','']
       },
       'exaime': [
           [{
               'name': '审核',
               'value': ''
           },
               {
                   'name': '批准',
                   'value': ''
               }],
           [{
               'name': '日期',
               'value': ''
           },
               {
                   'name': '日期',
                   'value': ''
               }]
           ],
       'other': {
           'one': '',
           'two': '',
       }
    }

    sql = 'select * from view_receipt_sum'
    cur = connection.cursor()
    cur.execute(sql)
    row = cur.fetchone()
    cur.close()
    if row:
        formdata['head']['title'] = '销售结算报表'
        formdata['head']['value'] = '截止日期：'+ str(row[0])
        formdata['body'][0][0]['name'] = '客户名称'
        formdata['body'][0][0]['value'] = '***'+str(row[1]) +'***'
        formdata['body'][0][1]['name'] = '账期'
        formdata['body'][0][1]['value'] = '-'
        formdata['body'][1][0]['name'] = '销售员'
        formdata['body'][1][0]['value'] = '-'
        formdata['body'][2][0]['name'] = '销售金额总计'
        formdata['body'][2][0]['value'] = str(row[2])
        formdata['body'][2][1]['name'] = '扣款总计'
        formdata['body'][2][1]['value'] = str(row[3])
        formdata['body'][3][0]['name'] = '已收款总计'
        formdata['body'][3][0]['value'] = str(row[4])
        formdata['body'][3][1]['name'] = '应收款总计'
        formdata['body'][3][1]['value'] = str(row[5])
        formdata['body'][4][1]['name'] = '到期应收款总计'
        formdata['body'][4][1]['value'] = str(row[6])
        formdata['body'][5][1]['name'] = '未到期因收款总计'
        formdata['body'][5][1]['value'] = str(row[7])
        #其它信息
        formdata['explain']['value'] = ['销售金额总计 - 扣款 = 已收款合计 + 未收款合计（已减去扣款）','未收款合计 = 到期未收款合计 + 未到期未收款合计']
        formdata['other']['one'] = '（已经减去 扣款总计）'
        formdata['other']['two'] = '（已经减去 扣款总计）'


    jsondata["formdata"] = formdata


    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-creallcusform-end---------------------------')
    return HttpResponse(s)

# 采购单个客户结算报表
def creonefacform(reqest, reqest_body):
    log = public.logger
    log.info('----------------------Button-creonefacform-begin---------------------------')

    uid = reqest_body.get('uid', None)
    checksum = reqest_body.get('checksum', None)
    menuid = reqest_body.get('menuid', None)
    datevalue = reqest_body.get('datevalue', None)
    creid = reqest_body.get('creid',None)

    # 先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }
    # '发票金额总计：起始日期 到 截止日期 内来发票金额总计',
    # '已付款总计：起始日期 到 截止日期 内来付款金额总计（支票 & 电汇 & 电子承兑 & 纸质承兑）',
    # '扣款总计：起始日期 到 截止日期 内扣款金额总计',
    # 报表表格数据结构(初始化)
    formdata = {
       'head': {
           'title': 'XXXXXX报表',
           'value': '截止日期：',
       },
       'body': [
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           ],
       'explain': {
           'name': '说明：',
           'value': ['','','']
       },
       'exaime': [
           [{
               'name': '审核',
               'value': ''
           },
               {
                   'name': '批准',
                   'value': ''
               }],
           [{
               'name': '日期',
               'value': ''
           },
               {
                   'name': '日期',
                   'value': ''
               }]
           ],
       'other': {
           'one': '',
           'two': '',
       }
    }

    # 获取当前客户名称
    facname_sql = "select fac_name,ass_period from yw_payable_factory_info where cre_id=%s"
    cur = connection.cursor()
    cur.execute(facname_sql,creid)
    row = cur.fetchone() # 客户名称
    cur.close()
    fac_name = row[0]
    ass_period = row[1]



    cgmoney_sum_sql = "SELECT code_cre_id,SUM(code_amo_money) as sum_get_money FROM view_payable_get WHERE code_cre_id=%s AND code_date>=%s AND code_date<=%s group by code_cre_id"
    paymoney_sum_sql = "SELECT code_cre_id,SUM(code_amo_money) as sum_out_money FROM yw_payable_invoice_info WHERE code_cre_id=%s " \
                       "AND CODE='2' AND code_date>=%s AND code_date<=%s group by code_cre_id"
    # 当前时间
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if datevalue:
        cur = connection.cursor()
        cur.execute(cgmoney_sum_sql,(creid,datevalue[0],datevalue[1]))
        cgrow = cur.fetchone()
        cur.execute(paymoney_sum_sql, (creid, datevalue[0], datevalue[1]))
        payrow = cur.fetchone()
        cur.close()
        # 表格数据
        formdata['head']['title'] = '采购结算报表'
        formdata['head']['value'] = '生成日期：'+ nowTime
        formdata['body'][0][0]['name'] = '厂商名称'
        formdata['body'][0][0]['value'] = fac_name
        formdata['body'][0][1]['name'] = '账期'
        formdata['body'][0][1]['value'] = str(ass_period)
        formdata['body'][1][0]['name'] = '起始时间'
        formdata['body'][1][0]['value'] = str(datevalue[0])
        formdata['body'][1][1]['name'] = '截止时间'
        formdata['body'][1][1]['value'] = str(datevalue[1])
        formdata['body'][2][0]['name'] = '采购金额总计'
        if cgrow:
            formdata['body'][2][0]['value'] = str(cgrow[1])
        else:
            formdata['body'][2][0]['value'] = '0'
        formdata['body'][3][0]['name'] = '已付款总计'
        if payrow:
            formdata['body'][3][0]['value'] = str(payrow[1])
        else:
            formdata['body'][3][0]['value'] = '0'

        #其它信息
        formdata['explain']['value'] = ['采购金额总计：起始日期 到 截止日期 内来采购金额总计','已付款总计：起始日期 到 截止日期 内来付款金额总计（支票 & 电汇 & 电子承兑 & 纸质承兑）']
        formdata['other']['one'] = '（已经减去 已付款总计）'
    else:
        allfac_sql = "select * from view_payable_form where code_cre_id = %s"
        cur = connection.cursor()
        cur.execute(allfac_sql,creid)
        onefac_row = cur.fetchone()
        cur.close()
        # 表格数据
        formdata['head']['title'] = '采购结算报表'
        formdata['head']['value'] = '生成日期：' + nowTime
        formdata['body'][0][0]['name'] = '厂商名称'
        formdata['body'][0][0]['value'] = str(onefac_row[1])
        formdata['body'][0][1]['name'] = '账期'
        formdata['body'][0][1]['value'] = str(onefac_row[2])
        formdata['body'][1][0]['name'] = '起始时间'
        formdata['body'][1][0]['value'] = '-'
        formdata['body'][1][1]['name'] = '截止时间'
        formdata['body'][1][1]['value'] = '-'
        formdata['body'][2][0]['name'] = '采购金额总计'
        formdata['body'][2][0]['value'] = str(onefac_row[3])
        formdata['body'][3][0]['name'] = '已付款总计'
        formdata['body'][3][0]['value'] = str(onefac_row[4])
        formdata['body'][3][1]['name'] = '未付款总计'
        formdata['body'][3][1]['value'] = str(int(onefac_row[5])+int(onefac_row[6]))
        formdata['body'][4][1]['name'] = '到期应付款总计'
        formdata['body'][4][1]['value'] = str(onefac_row[5])
        formdata['body'][5][1]['name'] = '未到期应付款总计'
        formdata['body'][5][1]['value'] = str(onefac_row[6])
        # 其它信息
        formdata['explain']['value'] = ['采购金额总计 = 已付款合计 + 未付款合计',
                                        '未付款合计 = 到期应付款合计 + 未到期应付款合计']
        formdata['other']['one'] = '（已经减去 已付款总计）'
        formdata['other']['two'] = '（已经减去 已付款总计）'

    jsondata["formdata"] = formdata


    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-creonefacform-end---------------------------')
    return HttpResponse(s)

# 采购所有客户结算报表
def creallfacform(reqest, reqest_body):
    log = public.logger
    log.info('----------------------Button-creallfacform-begin---------------------------')

    uid = reqest_body.get('uid', None)
    checksum = reqest_body.get('checksum', None)
    menuid = reqest_body.get('menuid', None)
    datevalue = reqest_body.get('datevalue', None)
    creid = reqest_body.get('creid',None)

    # 先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }
    # '发票金额总计：起始日期 到 截止日期 内来发票金额总计',
    # '已付款总计：起始日期 到 截止日期 内来付款金额总计（支票 & 电汇 & 承兑 & 延期支票）',
    # '扣款总计：起始日期 到 截止日期 内扣款金额总计',
    # 报表表格数据结构(初始化)
    formdata = {
       'head': {
           'title': 'XXXXXX报表',
           'value': '截止日期：',
       },
       'body': [
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           [{
               'name': '',
               'value': ''
           },
               {
                   'name': '',
                   'value': ''
               }],
           ],
       'explain': {
           'name': '说明：',
           'value': ['','','']
       },
       'exaime': [
           [{
               'name': '审核',
               'value': ''
           },
               {
                   'name': '批准',
                   'value': ''
               }],
           [{
               'name': '日期',
               'value': ''
           },
               {
                   'name': '日期',
                   'value': ''
               }]
           ],
       'other': {
           'one': '',
           'two': '',
       }
    }

    # 计算指定时间范围内 采购金额总计（所有客户）
    allfac_get_sql = "SELECT SUM(code_amo_money) as sum_get_money FROM view_payable_get WHERE code_date>=%s AND code_date<=%s"
    # 计算指定时间范围 付款金额总计（所有客户）
    allfac_out_sql = "SELECT SUM(code_amo_money) as sum_out_money FROM yw_payable_invoice_info " \
                     "WHERE CODE='2' AND code_date>=%s AND code_date<=%s"
    # 计算指定范围 付款支票金额总计（所有客户）
    allfac_out_type_sql = "SELECT code_pay_type,code_amo_money FROM yw_payable_invoice_info " \
                     "WHERE CODE='2' AND code_date>=%s AND code_date<=%s"
    # 所有客户采购结算
    allfac_sql = "SELECT SUM(sum_amo_money),SUM(out_true_money),(SUM(due_paymoney)+SUM(undue_paymoney)) AS unpay_money," \
                 "SUM(due_paymoney),SUM(undue_paymoney) FROM view_payable_form"

    # 当前时间
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if datevalue:
        cur = connection.cursor()
        cur.execute(allfac_get_sql,(datevalue[0],datevalue[1]))
        facget_row = cur.fetchone()
        cur.execute(allfac_out_sql,(datevalue[0],datevalue[1]))
        facout_row = cur.fetchone()
        cur.execute(allfac_out_type_sql,(datevalue[0],datevalue[1]))
        outtype_rows = cur.fetchall()
        cur.close()
        # 付款方式:电汇,电子承兑,纸质承兑,支票 (各类型总金额，指定时间区间)
        dh,dzcd,zzcd,zp = 0,0,0,0
        if outtype_rows:
            for item in outtype_rows:
                if item[0] == '1':
                    dh = dh + int(item[1])
                elif item[0]=='2':
                    dzcd = dzcd + int(item[1])
                elif item[0]=='3':
                    zzcd = zzcd + int(item[1])
                elif item[0]=='4':
                    zp = zp + int(item[1])
        # 采购金额总计，已付款金额总计（指定时间区间）
        cgsum_money,paysum_money = 0,0

        if facget_row[0]:
            cgsum_money = facget_row[0]
        if facout_row[0]:
            paysum_money = facout_row[0]

        # 表格数据
        formdata['head']['title'] = '采购结算报表'
        formdata['head']['value'] = '生成日期：'+ nowTime
        formdata['body'][0][0]['name'] = '厂商名称'
        formdata['body'][0][0]['value'] = '***所有厂商***'
        formdata['body'][0][1]['name'] = '账期'
        formdata['body'][0][1]['value'] = '-'
        formdata['body'][1][0]['name'] = '起始时间'
        formdata['body'][1][0]['value'] = str(datevalue[0])
        formdata['body'][1][1]['name'] = '截止时间'
        formdata['body'][1][1]['value'] = str(datevalue[1])
        formdata['body'][2][0]['name'] = '采购金额总计'
        formdata['body'][2][0]['value'] = '%.2f' % cgsum_money
        formdata['body'][3][0]['name'] = '已付款总计'
        formdata['body'][3][0]['value'] = '%.2f' % paysum_money
        formdata['body'][4][0]['name'] = '电汇总计'
        formdata['body'][4][0]['value'] = '%.2f' % dh
        formdata['body'][4][1]['name'] = '电子承兑总计'
        formdata['body'][4][1]['value'] = '%.2f' % dzcd
        formdata['body'][5][0]['name'] = '纸质承兑总计'
        formdata['body'][5][0]['value'] = '%.2f' % zzcd
        formdata['body'][5][1]['name'] = '支票总计'
        formdata['body'][5][1]['value'] = '%.2f' % zp


        #其它信息
        formdata['explain']['value'] = ['采购金额总计：起始日期 到 截止日期 内来采购金额总计','已付款总计：起始日期 到 截止日期 内来付款金额总计（支票 & 电汇 & 电子承兑 & 纸质承兑）']
    else:
        cur = connection.cursor()
        cur.execute(allfac_sql)
        allfac_row = cur.fetchone()
        cur.close()
        # 表格数据
        formdata['head']['title'] = '采购结算报表'
        formdata['head']['value'] = '生成日期：' + nowTime
        formdata['body'][0][0]['name'] = '厂商名称'
        formdata['body'][0][0]['value'] = '***所有厂商***'
        formdata['body'][0][1]['name'] = '账期'
        formdata['body'][0][1]['value'] = '-'
        formdata['body'][1][0]['name'] = '起始时间'
        formdata['body'][1][0]['value'] = '-'
        formdata['body'][1][1]['name'] = '截止时间'
        formdata['body'][1][1]['value'] = '-'
        formdata['body'][2][0]['name'] = '采购金额总计'
        formdata['body'][2][0]['value'] = '%.2f' % allfac_row[0]
        formdata['body'][3][0]['name'] = '已付款总计'
        formdata['body'][3][0]['value'] = '%.2f' % allfac_row[1]
        formdata['body'][3][1]['name'] = '应付款总计'
        formdata['body'][3][1]['value'] = '%.2f' % allfac_row[2]
        formdata['body'][4][1]['name'] = '到期应付款总计'
        formdata['body'][4][1]['value'] = '%.2f' % allfac_row[3]
        formdata['body'][5][1]['name'] = '未到期应付款总计'
        formdata['body'][5][1]['value'] = '%.2f' % allfac_row[4]
        # 其它信息
        formdata['explain']['value'] = ['采购金额总计 = 已付款合计 + 未付款合计',
                                        '未付款合计 = 到期应付款合计 + 未到期应付款合计']
        formdata['other']['one'] = '（已经减去 已付款总计）'
        formdata['other']['two'] = '（已经减去 已付款总计）'

    jsondata["formdata"] = formdata


    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-creallcusform-end---------------------------')
    return HttpResponse(s)
