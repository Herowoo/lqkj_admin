from django.shortcuts import HttpResponse
import json
import datetime
import calendar
from admin_app import public
from admin_app import models
from django.db import connection, transaction
from docxtpl import DocxTemplate
import os
import random
import base64
import shutil
import pymssql


# 索引关系对照：0：市场部；1：研发中心；2：物控中心；3：质控中心；4：制造中心；5：PMC
section_term = [0,1,2,4,3,5] # 各部门顺序索引
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
        if trantype == 'ndformView': ## 评审单页面初始化
            resp = ndformView(request,reqest_body)
        elif trantype == 'bomView': ## BOM页面初始化
            resp = bomView(request,reqest_body)
        elif trantype == 'softwareView': ## 软件版本确认单页面初始化
            resp = softwareView(request,reqest_body)
        elif trantype == 'uploadndform': ## 上传评审单页面数据
            resp = uploadndform(request,reqest_body)
        elif trantype == 'uploadbomform': ## 上传 BOM页面数据
            resp = uploadbomform(request, reqest_body)
        elif trantype == 'uploadsoftwareform': ## 上传 软件版本确认单页面数据
            resp = uploadsoftwareform(request, reqest_body)
        elif trantype == 'ndformdetail': ## 评审单详情页
            resp = ndformdetail(request, reqest_body)
        elif trantype == 'ndformaudit': ## 评审单审批接口
            resp = ndformaudit(request, reqest_body)
        elif trantype == 'reset_audit': ## 评审单重审接口
            resp = reset_audit(request, reqest_body)
        elif trantype == 'ndformproof': ## 评审单审核接口
            resp = ndformproof(request, reqest_body)
        elif trantype == 'doprint': ## 打印接口（暂未做限制）
            resp = doprint(request, reqest_body)
        elif trantype == 'schedule': ## 评审单进度页面
            resp = schedule(request, reqest_body)
        elif trantype == 'open_ndformalter': ## 返回评审单页面url
            resp = open_ndformalter(request, reqest_body)
        elif trantype == 'handfilelist': ## 上传附件信息
            resp = handfilelist(request, reqest_body)
        elif trantype == 'filelist_info': ## 附件列表
            resp = filelist_info(request, reqest_body)
        elif trantype == 'fileExamine': ## 附件审核
            resp = fileExamine(request, reqest_body)
        elif trantype == 'getBomList': ## 获取BOM列表
            resp = getBomList(request, reqest_body)
        elif trantype == 'getSoftwareList': ## 获取Software列表
            resp = getSoftwareList(request, reqest_body)
        elif trantype == 'getModelList': ## 获取model列表
            resp = getModelList(request, reqest_body)
        elif trantype == 'exportWord': ## 导出Word
            resp = exportWord(request, reqest_body)
        elif trantype == 'getHardinfo': ## 获取硬件版本信息
            resp = getHardinfo(request, reqest_body)
        elif trantype == 'getWorkview': ## 各部门填写效率统计
            resp = getWorkview(request, reqest_body)
        elif trantype == 'getOneprocess': ## 单个评审单填写流水
            resp = getOneprocess(request, reqest_body)
        else:
            s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
            resp = HttpResponse(s)
    elif request.method == "GET":
        s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
        resp = HttpResponse(s)
    return resp

# 获取单个评审单的填写流水
def getOneprocess(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-getOneprocess-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }
    user_id = reqest_body.get('uid', None)
    billid = reqest_body.get('billid', None)

    ProcessData = []
    # 市场因有head 表，先单独处理
    sc_sql = "SELECT insert_time,'市场部' AS tmp_name FROM yw_bill_review_form_head WHERE head_id = %s "
    sc_his_sql = "SELECT distinct insert_time,'市场部' AS tmp_name FROM yw_bill_review_form_head_his WHERE head_id = %s ORDER BY insert_time"
    cur = connection.cursor()
    sc_dict = {}
    cur.execute(sc_sql,billid)
    row = cur.fetchone()
    if row:
        sc_dict[str(row[0])] = {
            'content':str(row[1] or '') + '修改',
            'timestamp':row[0]
        }
    sc_body_sql = "SELECT distinct complement_time,fzr from yw_bill_review_form_body WHERE head_id = %s and name_id ='0'" \
                  " and complement_time is not NULL order by complement_time"
    cur.execute(sc_body_sql,billid)
    rows = cur.fetchall()
    if rows:
        for index,item in enumerate(rows):
            if index==0:
                sc_dict[str(item[0])] = {
                    'content':str(item[1] or '') + '填写',
                    'timestamp':item[0]
                }
            else:
                sc_dict[str(item[0])] = {
                    'content': str(item[1] or '') + '修改',
                    'timestamp': item[0]
                }
    cur.execute(sc_his_sql, billid)
    rows = cur.fetchall()
    if rows:
        for index, item in enumerate(rows):
            if index == 0:
                sc_dict[str(item[0])] = {
                    'content': str(item[1] or '') + '发起并填写',
                    'timestamp': item[0]
                }
            else:
                sc_dict[str(item[0])] = {
                    'content': str(item[1] or '') + ' 修改',
                    'timestamp': item[0]
                }
    sc_audit_sql = "SELECT audit_date,auditor FROM yw_bill_audit_info WHERE audit_billid = %s and section_id = '0' and audit_state='1'"
    cur.execute(sc_audit_sql, billid)
    row = cur.fetchone()
    if row:
        sc_dict[str(row[0])] = {
            'content': str(row[1] or '') + '审核',
            'timestamp': row[0]
        }
    sc_audit_his_sql = "SELECT audit_date,auditor,audit_state FROM yw_bill_audit_info_his WHERE audit_billid = %s and section_id = '0' and audit_date is not NULL"
    cur.execute(sc_audit_his_sql, billid)
    rows = cur.fetchall()
    if rows:
        for item in rows:
            if item[2] =='0':
                sc_dict[str(item[0])] = {
                    'content': str(item[1] or '') + '审核',
                    'timestamp': item[0]
                }
            else:
                sc_dict[str(item[0])] = {
                    'content': str(item[1] or '') + '返审核',
                    'timestamp': item[0]
                }
    hardware_sql = "SELECT lq_confirmation_date,lq_confirmation FROM yw_bill_hardware_version_confirm where head_id = %s ORDER BY id"
    software_sql = "SELECT lq_confirmation_date,lq_confirmation FROM yw_bill_software_version_confirm where head_id = %s ORDER BY id"
    cur.execute(hardware_sql, billid)
    rows = cur.fetchall()
    if rows:
        for index, item in enumerate(rows):
            if index == 0:
                sc_dict[str(item[0])] = {
                    'content': str(item[1] or '') + '填写硬件版本确认单',
                    'timestamp': item[0]
                }
            else:
                sc_dict[str(item[0])] = {
                    'content': item[1] + '修改硬件版本确认单',
                    'timestamp': item[0]
                }
    cur.execute(software_sql, billid)
    rows = cur.fetchall()
    if rows:
        for index, item in enumerate(rows):
            if index == 0:
                sc_dict[str(item[0])] = {
                    'content': str(item[1] or '') + '填写软件版本确认单',
                    'timestamp': item[0]
                }
            else:
                sc_dict[str(item[0])] = {
                    'content': str(item[1] or '') + '修改软件版本确认单',
                    'timestamp': item[0]
                }
    key_list = list(sc_dict.keys())
    key_list.sort(reverse=True)
    tmp_list = []
    for item in key_list:
        tmp_list.append(sc_dict[item])
    ProcessData.append(tmp_list)

    # 其他部门
    for i in range(1,6):
        other_dict = {}
        body_sql = "SELECT distinct complement_time,fzr from yw_bill_review_form_body WHERE head_id = %s and name_id =%s" \
                      " and complement_time is not NULL order by id"
        cur.execute(body_sql, (billid,str(i)))
        rows = cur.fetchall()
        if rows:
            for index, item in enumerate(rows):
                if index == 0:
                    other_dict[str(item[0])] = {
                        'content': str(item[1] or '') + '填写',
                        'timestamp': item[0]
                    }
                else:
                    other_dict[str(item[0])] = {
                        'content': str(item[1] or '') + '修改',
                        'timestamp': item[0]
                    }
        audit_sql = "SELECT audit_date,auditor FROM yw_bill_audit_info WHERE audit_billid = %s and section_id = %s and audit_state='1'"
        cur.execute(audit_sql, (billid,str(i)))
        row = cur.fetchone()
        if row:
            other_dict[str(row[0])] = {
                'content': str(row[1] or '') + '审核',
                'timestamp': row[0]
            }
        audit_his_sql = "SELECT audit_date,auditor,audit_state FROM yw_bill_audit_info_his WHERE audit_billid = %s and section_id = %s and audit_date is not NULL "
        cur.execute(audit_his_sql, (billid,str(i)))
        rows = cur.fetchall()
        if rows:
            for item in rows:
                if item[2] == '0':
                    other_dict[str(item[0])] = {
                        'content': str(item[1] or '') + '审核',
                        'timestamp': item[0]
                    }
                else:
                    other_dict[str(item[0])] = {
                        'content': str(item[1] or '') + '返审核',
                        'timestamp': item[0]
                    }
        keys_list = list(other_dict.keys())
        keys_list.sort(reverse=True)  # 降序排序
        tmp_list = []
        if keys_list:
            for item in keys_list:
                tmp_list.append(other_dict[item])
        else:
            nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            tmp_list.append({
                'content': '暂未填写',
                'timestamp': ''
            })
        ProcessData.append(tmp_list)
    # 根据部门顺序调整显示
    section_name = ['市场部','项目管理部','物控中心','质控中心','制造中心','PMC']
    true_processdata = []
    true_section_name = []
    for item in section_term:
        true_processdata.append(ProcessData[item])
        true_section_name.append(section_name[item])
    jsondata['processdata'] = true_processdata
    jsondata['section_list'] = true_section_name

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------lqkjbill-getOneprocess-end---------------------------')
    return HttpResponse(s)

# 评审单各部门工作效率查询
def getWorkview(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-getWorkview-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }
    user_id = reqest_body.get('uid', None)
    type = reqest_body.get('type',None)
    data = reqest_body.get('data',None)
    dateList = reqest_body.get('dateList',None)

    tmp_heads = [
                {
                    'name':'billid',
                    'label':'评审单号',
                    'width':120
                },
                {
                    'name':'shichang',
                    'label':'市场部(小时)',
                    'width':120
                },
                {
                    'name':'yanfa',
                    'label': '项目管理部(小时)',
                    'width':120
                },
                {
                    'name':'wukong',
                    'label': '物控中心(小时)',
                    'width':120
                },
                {
                    'name':'zhikong',
                    'label': '质控中心(小时)',
                    'width':120
                },
                {
                    'name':'zhizao',
                    'label': '制造中心(小时)',
                    'width':120
                },
                {
                    'name':'PMC',
                    'label': 'PMC(小时)',
                    'width':120
                }
            ]
    heads = [tmp_heads[0]]
    for item in section_term:
        heads.append(tmp_heads[item+1])
    tableData = []
    begin_bill = ''
    end_bill = ''
    if type=='Month':
        tmp_list = data.split('-')
        year = int(tmp_list[0])
        month = int(tmp_list[1])
        firstDayWeekDay, monthRange = calendar.monthrange(year, month)
        # 获取当月的第一天
        firstDay = datetime.date(year=year, month=month, day=1)
        lastDay = datetime.date(year=year, month=month, day=monthRange)
        firstDay_list = str(firstDay).split('-')
        lastDay_list = str(lastDay).split('-')
        begin_bill = 'PS' + firstDay_list[0][-2:] + firstDay_list[1] + firstDay_list[2] +'00'
        end_bill = 'PS' + lastDay_list[0][-2:] + lastDay_list[1] + lastDay_list[2] +'99'
    elif type=='Week':
        begin_time = datetime.datetime.strptime(data, '%Y-%m-%d %H:%M:%S')
        delta = datetime.timedelta(days=7)
        end_time = begin_time + delta
        begin_list = (str(begin_time).split(' ')[0]).split('-')
        end_list = (str(end_time).split(' ')[0]).split('-')
        begin_bill = 'PS' + begin_list[0][-2:] + begin_list[1] + begin_list[2] + '00'
        end_bill = 'PS' + end_list[0][-2:] + end_list[1] + end_list[2] + '99'
    elif type=='DateRange':
        begin_list = str(dateList[0]).split('-')
        end_list = str(dateList[1]).split('-')
        begin_bill = 'PS' + begin_list[0][-2:] + begin_list[1] + begin_list[2] + '00'
        end_bill = 'PS' + end_list[0][-2:] + end_list[1] + end_list[2] + '99'
    # 计算各部门所用时间（或平均时间）
    if type == 'Billid':
        # 查询评审单号是否存在，验证评审单号正确性
        sql = "select count(1) from yw_bill_review_form_head where head_id = %s"
        cur = connection.cursor()
        cur.execute(sql,data)
        num = cur.fetchone()[0]
        if num == 0:
            s = public.setrespinfo({"respcode": "900015", "respmsg": "评审单号不存在，请检查输入!"})
            return HttpResponse(s)
        else:
            tmp_time = count_time2(log,data)
            tmp_section = ['市场部', '项目管理部', '物控中心', '质控中心', '制造中心', 'PMC']
            tmp_section_keys = ['shichang', 'yanfa', 'wukong', 'zhikong', 'zhizao', 'PMC']
            section_name,time_list,section_list = [],[],[]
            for item in section_term:
                section_name.append(tmp_section[item])
                time_list.append(tmp_time[item])
                section_list.append(tmp_section_keys[item])
            jsondata['xname'] = '部门'
            jsondata['yname'] = '所用时长(小时)'
            jsondata['xdata'] = section_name
            jsondata['ydata'] = time_list

            tmp_dict = {}
            tmp_dict['billid'] = data
            for index,item in enumerate(time_list):
                if item == 0:
                    tmp_dict[section_list[index]] = '未审核'
                else:
                    tmp_dict[section_list[index]] = item
            count = 0
            for key in tmp_dict.keys():
                if tmp_dict[key] == '':
                    count = count + 1
            if count != 6:
                tableData.append(tmp_dict)
    else:
        bill_sql = "SELECT head_id FROM yw_bill_review_form_head WHERE head_id >%s and head_id< %s and state!='2' "
        cur = connection.cursor()
        cur.execute(bill_sql,(begin_bill,end_bill))
        rows = cur.fetchall()
        if rows:
            all_dict = {}
            for item in rows:
                all_dict[item[0]] = count_time2(log,item[0])
            count_list = [0,0,0,0,0,0]
            total_list = [0,0,0,0,0,0]
            section_list = ['shichang','yanfa','wukong','zhikong','zhizao','PMC']
            count = 1
            for key in all_dict.keys():
                tmp_dict = {}
                tmp_dict['billid'] = key
                tmp_dict['id'] = count
                count = count +1
                for i in range(len(all_dict[key])):
                    tmp_num = total_list[i]
                    total_list[i] = tmp_num + all_dict[key][i]
                    if all_dict[key][i]==0:
                        tmp_dict[section_list[i]] = '未审核'
                    else:
                        tmp = count_list[i]
                        count_list[i] = tmp + 1
                        tmp_dict[section_list[i]] = all_dict[key][i]
                tableData.append(tmp_dict)
            tmp_true_list = []
            for index,item in enumerate(total_list):
                if count_list[index] !=0:
                    if (item/count_list[index])<0.01:
                        tmp_value = round((item/count_list[index]),4)
                    else:
                        tmp_value = round((item/count_list[index]),2)
                else:
                    tmp_value = 0
                tmp_true_list.append(tmp_value)
            # 根据部门顺序统一处理
            tmp_section_name = ['市场部', '项目管理部', '物控中心', '质控中心', '制造中心', 'PMC']
            section_name,true_list = [],[]
            for item in section_term:
                section_name.append(tmp_section_name[item])
                true_list.append(tmp_true_list[item])
            jsondata['xname'] = '部门'
            jsondata['yname'] = '平均所用时长(小时)'
            jsondata['xdata'] = section_name
            jsondata['ydata'] = true_list
        else:
            s = public.setrespinfo({"respcode": "900016", "respmsg": "所选时间区间无评审单!"})
            return HttpResponse(s)

    jsondata['heads'] = heads
    jsondata['tableData'] = tableData
    jsondata['section_term'] = section_term

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------lqkjbill-getWorkview-end---------------------------')
    return HttpResponse(s)

# 评审单附件审核接口
def fileExamine(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-fileExamine-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }
    user_id = reqest_body.get('uid', None)
    billid = reqest_body.get('billid',None)
    fileid = reqest_body.get('fileid',None)
    flag = reqest_body.get('flag',None)

    update_annex_sql = "update yw_bill_annex_info set status=%s where billid=%s"
    cur = connection.cursor()
    select_annex_sql = "select status from yw_bill_annex_info where billid=%s"
    cur.execute(select_annex_sql,billid)
    row = cur.fetchone()
    status = eval(row[0])
    if flag =='pass':
        status[str(fileid)] = 1
    else:
        status[str(fileid)] = 2
    cur.execute(update_annex_sql, (str(status), billid))
    cur.close()

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------lqkjbill-fileExamine-end---------------------------')
    return HttpResponse(s)

# 获取硬件版本信息
def getHardinfo(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjerp_getHardinfo_begin---------------------------')
    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "hardinfo":None
    }

    prompf = reqest_body.get("prompf",None)
    hardinfo = {
        'name': '硬件版本（*）',
        'value': ['', '', '', '', ''],
        'cltime': ['', '', '', '', ''],
        'wctime': ['', '', '', '', '']
    }
    sql = "select map_id,pcb1,pcb2,pcb3,pcb4 from yw_bill_bom_version where bom_id=%s and status='1' order by id desc limit 1"
    cursor = connection.cursor()
    cursor.execute(sql,prompf)
    row = cursor.fetchone()
    if row:
        for i in range(len(hardinfo['value'])):
            hardinfo['value'][i] = row[i]
    jsondata['hardinfo'] = hardinfo

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjerp_getHardinfo_end---------------------------')
    return HttpResponse(s)

# 导出Word
def exportWord(request, reqest_body):
    log = public.logger
    log.info('----------------------lqkjerp_exportWord_begin---------------------------')
    # 返回信息赋值
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "filename":'',
        "data":None
    }
    user_id = reqest_body.get('uid', None)
    postdata=reqest_body.get('data',None)
    type = postdata.get('type',None)
    filenum = postdata.get('filenum',None)
    billid = postdata.get('billid',None)

    cur = connection.cursor()
    flag_rows = ''
    if type=='hardware':
        select_sql = "select * from yw_bill_hardware_version_confirm where file_number=%s"
        cur.execute(select_sql,filenum)
        flag_rows = cur.fetchall()
    elif type == 'software':
        select_sql = "select * from yw_bill_software_version_confirm where file_number=%s"
        cur.execute(select_sql,filenum)
        flag_rows = cur.fetchall()
    if not flag_rows:
        s = public.setrespinfo({"respcode": "900012", "respmsg": "请先提交数据!"})
        return HttpResponse(s)

    sql = "select export_power from yw_bill_power_config where user_id = %s"
    cur.execute(sql, user_id)
    cur.close()
    row = cur.fetchone()

    if row and row[0]=='Y':
        if filenum and type == 'hardware':
            file_name = "硬件版本确认单_" + filenum + ".docx"
        elif filenum and type == 'software':
            file_name = "软件版本确认单_" + filenum + ".docx"


        # save_path = getPsFileUri(billid)
        # save_path = save_path + file_name
        # if not os.path.exists(save_path):  # 如果路径不存在
        file = CreateWord(billid,filenum,type)

        # file = open(save_path, 'rb')
        jsondata['filename']=file_name
        jsondata['data']=base64.b64encode(file.read()).decode()
    else:
        s = public.setrespinfo({"respcode": "900009", "respmsg": "没有操作权限!"})
        return HttpResponse(s)


    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjerp_exportWord_end---------------------------')
    return HttpResponse(s)

# 获取模板列表
def getModelList(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-getModelList-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }
    user_id = reqest_body.get('uid', None)

    sql = "select DISTINCT(head_id) from yw_bill_review_form_head_model"
    cur = connection.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    modelList = []
    if rows:
        for item in rows:
            tmp_dict = {
                'value': item[0],
                'label': item[0]
            }
            modelList.append(tmp_dict)
    jsondata["modelList"] = modelList

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------lqkjbill-getModelList-end---------------------------')
    return HttpResponse(s)

# 评审单进度页面数据
def schedule(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-schedule-begin---------------------------')
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    user_id = reqest_body.get('uid', None)
    pagesize = int(reqest_body.get('pagesize', "10"))
    pagenum = int(reqest_body.get('pagenum', "1"))

    total_sql = "select COUNT(1) as totalnum from yw_bill_review_form_head where state!='2'"
    cur = connection.cursor()
    cur.execute(total_sql)
    row = cur.fetchone()
    totalnumber = row[0]
    jsondata["totalnumber"] = totalnumber

    #分页查询
    if pagesize==0 or not pagesize:
        pagesize = 10
    if pagenum==0  or not pagenum:
        pagenum = 1
    # 查询开始位置
    startno = (pagenum - 1) * pagesize
    data_sql = "select id,head_id,order_type,product_name,quantity,customer_name,area FROM yw_bill_review_form_head WHERE state!='2'  ORDER BY state DESC,head_id DESC limit %s,%s" % (startno, pagesize)
    cur.execute(data_sql)
    log.info(data_sql)
    rows = cur.fetchall()
    tableData = []
    if rows:
        for index,item in enumerate(rows):
            tmp_allschedule = sched_one(item[1])
            tmp_tabledata ={
                'id': str(item[0]),
                'billid': item[1],
                'billtype': item[2],
                'product': item[3],
                'number': item[4],
                'customer': item[5],
                'usearea': item[6],
                'allschedule':tmp_allschedule
            }
            tableData.append(tmp_tabledata)
    jsondata["tableData"] = tableData

    heads = [
        {
            'name': 'billid',
            'label': '评审单号',
            'width': '80'
        },
        {
            'name': 'billtype',
            'label': '类型',
            'width': '80'
        },
        {
            'name': 'product',
            'label': '产品名称',
            'width': '80'
        },
        {
            'name': 'number',
            'label': '数量',
            'width': '80'
        },
        {
            'name': 'customer',
            'label': '客户名称',
            'width': '80'
        },
        {
            'name': 'usearea',
            'label': '使用地区',
            'width': '80'
        },
    ]
    jsondata["heads"] = heads
    # 各部门角色列表
    tmp_role_list = ['lqkj_shichang', 'lqkj_yanfa', 'lqkj_wukong', 'lqkj_zhikong', 'lqkj_shengchan', 'lqkj_pmc']
    role_sql = "select ROLE_ID from sys_user_role where USER_ID = %s"
    cur.execute(role_sql, user_id)
    log.info(role_sql % user_id)
    power_rows = cur.fetchall()
    cur.close()
    power_rows = str(power_rows)
    temp_list = []
    scdetail = False
    if power_rows:
        if 'lqkj_pmc' in power_rows or 'administrator' in power_rows:
            scdetail = True
    scdetail = True # 2020/04/23 修改所有部门都可查看明细
    jsondata["scdetail"] = scdetail
    # 根据部门索引顺序调整
    role_list = []
    for item in section_term:
        role_list.append(tmp_role_list[item])
    section_index = 0
    for i in range(len(role_list)):
        if role_list[i] in power_rows:
            section_index = i+1
            break
    jsondata["section_index"] = section_index

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------lqkjbill-schedule-end---------------------------')
    return HttpResponse(s)

# 返回评审单修改页面url
def open_ndformalter(request, reqest_body):
    log = public.logger
    log.info('----------------------Button-showndformalter-begin---------------------------')

    infoid = reqest_body.get('infoid',None)

    uid=reqest_body.get('uid',None)
    checksum=reqest_body.get('checksum',None)

    #先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "url": "%sndformalter?menu_id=105&uid=%s&checksum=%s&infoid=%s"%(request.META['HTTP_ORIGIN']+'/',uid,checksum,infoid),  # 预览-返回url打开新页面
    }
    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------Button-showndformalter-end---------------------------')
    return HttpResponse(s)

# 评审单页面数据（初始化）
def ndformView(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-ndformView-begin---------------------------')

    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "ndforminfo": {}
    }

    user_id = reqest_body.get('uid', None)

    ndformdata = {}
    ndformdata["title"]="需求评审单"
    #查询数据库历史记录生成评审单号
    today = datetime.date.today()
    formatted_today = today.strftime('%y%m%d')
    cur = connection.cursor()
    sql = "select head_id from yw_bill_review_form_head order by id desc limit 1"
    cur.execute(sql)
    row = cur.fetchone()

    if row:
        his_billid = row[0]
        his_billid_date = his_billid[2:8]
        if his_billid_date == formatted_today:
            new_billid = 'PS' + str(int(his_billid[2:]) + 1)
        else:
            new_billid = 'PS' + formatted_today + '01'
    else:
        new_billid = 'PS' + formatted_today + '01'


    billdata = {}
    billdata["name"] = "评审单号"
    billdata["billid"] = new_billid
    billdata["billtype_name"]=['订单', '备货计划', '小批送样','试产']
    billdata["billtype"]=""
    billdata["proname"] = "投产单号"
    billdata["proid"] = "暂无"
    ndformdata["billdata"]=billdata
    ndformdata["billdate"]=""

    orderdata = []
    orderdata_temp = {}
    orderdata_temp["order_name"] = '受订单号'
    orderdata_temp["order_value"] = ''
    orderdata_temp["plan_name"] = '计划单号'
    orderdata_temp["plan_value"] = ''
    orderdata_temp["cus_name"] = '客户名称'
    orderdata_temp["cus_value"] = ''
    orderdata.append(orderdata_temp)
    ndformdata["orderdata"] = orderdata

    cpdata = []
    cpkey = ['产品名称','规格型号','数量','交货日期','业务员','使用地区']
    for i in range(len(cpkey)):
        cpdata_temp = {}
        cpdata_temp["cpkey"] = cpkey[i]
        cpdata_temp["cpvalue"] = ['','']
        cpdata.append(cpdata_temp)
    ndformdata["cpdata"]=cpdata

    ndformdata["page"] = ''
    ndformdata["tsyq"] = '特殊要求：'
    ndformdata["tbgz"] = '内容'

    htyq = []
    # htyq_name = ['芯片ID','是否要求与送样产品一致','说明要求','纸箱要求','装箱要求','箱贴格式','备品','出厂检验报告','发货要求','其他']
    htyq_name = ['芯片ID','是否要求与送样产品一致','是否需要型式试验','纸箱要求','装箱要求','箱贴格式','备品','出厂检验报告','发货要求','其他']
    htyq_value = ['','保持一致','无需','','','','无需','需要','','']
    for i in range(len(htyq_name)):
        htyq_temp = {}
        htyq_temp["name"] = htyq_name[i]
        htyq_temp["value"] = [htyq_value[i]]
        htyq_temp["cltime"] = ['']
        htyq_temp["wctime"] = ['']
        htyq.append(htyq_temp)
    ndformdata["htyq"]=htyq
    ndformdata["htyqFzr"] = ''

    ndformdata["pzdata_remask"] = ['BOM', 'PCB1', 'PCB2', 'PCB3', 'PCB4']
    pzdata = []
    pzname = ['产品母配方（*）','硬件版本（*）','软件版本（*）','关键元器件清单','结构件（*）','包材','耗材','铭牌图纸','接线图纸','订单配方号']
    for i in range(len(pzname)):
        pzdata_temp = {}
        if i ==1:
            pzdata_temp["name"] = pzname[i]
            pzdata_temp["value"] = ['', '', '', '', '']
            pzdata_temp["cltime"] = ['', '', '', '', '']
            pzdata_temp["wctime"] = ['', '', '', '', '']
            pzdata.append(pzdata_temp)
        elif i ==3:
            pzdata_temp["name"] = pzname[i]
            pzdata_temp["value"] = ['见附件']
            pzdata_temp["cltime"] = ['']
            pzdata_temp["wctime"] = ['']
            pzdata.append(pzdata_temp)
        else:
            pzdata_temp["name"] = pzname[i]
            pzdata_temp["value"] = ['']
            pzdata_temp["cltime"] = ['']
            pzdata_temp["wctime"] = ['']
            pzdata.append(pzdata_temp)
    ndformdata["pzdata"] = pzdata
    ndformdata["pzFzr"] = ''

    wldata = []
    # wlname=['物料齐套','外加工','其他'] #2020.03.27 去掉外加工
    wlname=['物料齐套','其他']
    for i in range(len(wlname)):
        wldata_temp = {}
        wldata_temp["name"] = wlname[i]
        wldata_temp["value"] = ['']
        wldata_temp["cltime"] = ['']
        wldata_temp["wctime"] = ['']
        wldata.append(wldata_temp)
    ndformdata["wldata"] = wldata
    ndformdata["wlFzr"] = ''

    zldata = []
    zlname = ['检验标准', '其他']
    for i in range(len(zlname)):
        zldata_temp = {}
        zldata_temp["name"] = zlname[i]
        zldata_temp["value"] = ['']
        zldata_temp["cltime"] = ['']
        zldata_temp["wctime"] = ['']
        zldata.append(zldata_temp)
    ndformdata["zldata"] = zldata
    ndformdata["zlFzr"] = ''

    gydata = []
    gyname = ['SOP-作业指导', '工艺流程','烧录软件版本','产测软件版本','抄表软件版本','入库时间','其他']
    for i in range(len(gyname)):
        gydata_temp = {}
        gydata_temp["name"] = gyname[i]
        gydata_temp["value"] = ['']
        gydata_temp["cltime"] = ['']
        gydata_temp["wctime"] = ['']
        gydata.append(gydata_temp)
    ndformdata["gydata"] = gydata
    ndformdata["gyFzr"] = ''

    pcmdata = []
    # pcmname = ['入库时间', '其他'] # 2020.03.27 新增回板时间，计划单号
    pcmname = ['回板时间','入库时间','计划单号', '其他']
    for i in range(len(pcmname)):
        pcmdata_temp = {}
        pcmdata_temp["name"] = pcmname[i]
        pcmdata_temp["value"] = ['']
        pcmdata_temp["cltime"] = ['']
        pcmdata_temp["wctime"] = ['']
        pcmdata.append(pcmdata_temp)
    ndformdata["pcmdata"] = pcmdata
    ndformdata["pcmFzr"] = ''

    psdata = []
    name_key = ['营销中心', '项目管理部', '物控中心', '质控中心', '制造中心', '财务部']
    for i in range(len(name_key)):
        psdata_temp = {}
        psdata_temp["name_key"] = name_key[i]
        psdata_temp["name_value"] = ''
        psdata_temp["date_key"] = '日期'
        psdata_temp["date_value"] = ''
        psdata_temp["num_key"] = name_key[i]
        psdata_temp["num_value"] = ''
        psdata.append(psdata_temp)
    ndformdata["psdata"] = psdata

    # 审核信息 and 校验信息
    tmp_auditdata = []
    tmp_proofdata = []
    audit_name = ['市场部','项目管理部','物控中心','质控中心','制造中心','PMC']
    for i in range(len(audit_name)):
        # 审核信息
        auditdata_temp = {}
        auditdata_temp['name'] = audit_name[i]
        auditdata_temp['value'] = ''
        auditdata_temp['date'] = ''
        tmp_auditdata.append(auditdata_temp)
        # 校验信息
        proofdata_temp = {}
        proofdata_temp['name'] = audit_name[i]
        proofdata_temp['value'] = ''
        proofdata_temp['date'] = ''
        tmp_proofdata.append(proofdata_temp)

    # 根据各部门填写顺序设置
    auditdata,proofdata = [],[]
    for item in section_term:
        auditdata.append(tmp_auditdata[item])
        proofdata.append(tmp_proofdata[item])
    ndformdata["auditdata"] = auditdata
    ndformdata["proofdata"] = proofdata


    ndformdata["myalter"] = True # 可修改状态

    # 权限设置
    term_list = ['scpower', 'yfpower', 'wkpower', 'zkpower', 'propower',
                 'pmcpower', 'myexportword', 'myprint', 'myprooof', 'myaudit','myresetaudit','hardsoft_write']
    cur = connection.cursor()
    sql = "select * from yw_bill_power_config where user_id = %s"
    cur.execute(sql, user_id)
    cur.close()
    power_row = cur.fetchone()
    if power_row:
        for i in range(0, len(term_list)):
            if power_row[i + 1] == 'Y':
                ndformdata[term_list[i]] = True
            elif power_row[i + 1] == 'N':
                ndformdata[term_list[i]] = False
            elif power_row[i + 1] == 'All':
                ndformdata[term_list[i]] = True
            else:
                ndformdata[term_list[i]] = True
    else:
        for item in term_list:
            ndformdata[item] = False
    # 评审单新增页面，打印等权限锁定
    ndformdata["myprint"] = True #打印权限
    ndformdata["myaudit"] = False  #审核权限
    ndformdata["myresetaudit"] = False  #反审核权限
    ndformdata["myprooof"] = False  #校验权限
    ndformdata["myexportword"] = False # 导出Word权限

    ndform = {}
    ndform["ndform"] = ndformdata
    jsondata["ndforminfo"] = ndform
    jsondata["filelist"] = []
    jsondata["downfilelist"] = []

    s = json.dumps(jsondata,cls = models.JsonCustomEncoder,ensure_ascii=False)
    log.info(s)
    log.info('----------------------lqkjbill-ndformView-end---------------------------')
    return HttpResponse(s)

# 获取BOM 列表
def getBomList(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-getBomList-begin---------------------------')

    billid = reqest_body.get('billid', None)

    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }
    bomHead = [
        {
            'name': 'file_num',
            'label': '文件号',
            'width': 150
        },
        {
            'name': 'cus_name',
            'label': '客户名称',
            'width': 150
        },
        {
            'name': 'order_area',
            'label': '订单区域',
            'width': 150
        },
        {
            'name': 'order_num',
            'label': '受订单号',
            'width': 150
        },
        {
            'name': 'plan_num',
            'label': '计划号',
            'width': 150
        }
    ]
    jsondata['bomHead'] = bomHead

    bomData = []
    # 查询数据库中对应评审单已录入的 BOM
    sql = "select id,file_number,customer_name,order_area,order_number,plan_number from yw_bill_hardware_version_confirm WHERE id IN " \
          "(SELECT MAX(id) FROM yw_bill_hardware_version_confirm where head_id = %s group by head_id,file_number)"
    cursor = connection.cursor()
    cursor.execute(sql, billid)
    log.info(sql % billid)
    rows = cursor.fetchall()
    if rows:
        for item in rows:
            tmp_dict = {
                'file_num': item[1],
                'cus_name': item[2],
                'order_area': item[3],
                'order_num': item[4],
                'plan_num': item[5]
            }
            bomData.append(tmp_dict)
    jsondata['bomData'] = bomData

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------lqkjbill-getBomList-end---------------------------')
    return HttpResponse(s)

# bom页面数据
def bomView(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-bomView-begin---------------------------')

    user_id = reqest_body.get('uid', None)
    billid = reqest_body.get('billid',None)
    file_num = reqest_body.get('file_num',None)
    syncdata = reqest_body.get('syncdata',None)

    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "bominfo": {}
    }
    bomdata = {}
    # 部分初始数据根据传递的数据填写
    initdata = [syncdata["orderdata"][0]["cus_value"],syncdata["productdata"][-1]["cpvalue"][0],
                syncdata["orderdata"][0]["order_value"],syncdata["orderdata"][0]["plan_value"],
                syncdata["productdata"][-1]["cpvalue"][0],'',syncdata["productdata"][0]["cpvalue"][0],
                syncdata["productdata"][2]["cpvalue"][0]]
    # 查询数据库中是否存在对应评审单号的记录
    select_sql = "select id,file_number from yw_bill_hardware_version_confirm WHERE id IN " \
                 "(SELECT MAX(id) FROM yw_bill_hardware_version_confirm where head_id = %s group by head_id,file_number)"
    # 根据客户名称+使用地区查询历史数据作为回填的数据
    his_sql = "select * from yw_bill_hardware_version_confirm where customer_name= %s and install_area= %s order by id desc limit 1"
    # 查询BOM 文件最新信息
    sql = "select * from yw_bill_hardware_version_confirm where head_id = %s and file_number= %s order by id desc limit 1"
    # file_num 不为空时，为修改BOM 文件
    if file_num:
        cursor = connection.cursor()
        cursor.execute(sql,(billid,file_num))
        log.info(sql % (billid,file_num))
        row = cursor.fetchone()

        bomdata["billid"] = billid
        bomdata["file_number"] = file_num
        hardware_head = []
        hardware_head_name = ['客户名称','订单区域','受订单号','计划号','安装区域/用途',"技术要求"]
        for i in range(len(hardware_head_name)):
            hardware_head_temp = {}
            hardware_head_temp["name"] = hardware_head_name[i]
            hardware_head_temp["value"] = row[i+3]
            hardware_head.append(hardware_head_temp)
        bomdata["hardware_head"] = hardware_head

        product_data = []
        product_data_name = ['产品种类','订单数量','PCB版本','安装图版本','确认人','确认时间']
        for i in range(len(product_data_name)):
            product_data_temp = {}
            product_data_temp["name"] = product_data_name[i]
            product_data_temp["value"] = row[i+9]
            product_data.append(product_data_temp)
        bomdata["product_data"] = product_data
        # 软件版本确认单迁移数据
        pack_explain = {}
        pack_explain["name"] = "外观包装说明"
        pack_explain["value"] = row[16]
        bomdata["pack_explain"] = pack_explain

        silk_seal = []
        silk_seal_name = ['厂家名称', '规格型号', '资产条码', '丝印方式', 'CAD图纸']
        for i in range(len(silk_seal_name)):
            silk_seal_temp = {}
            silk_seal_temp["name"] = silk_seal_name[i]
            silk_seal_temp["value"] = row[i + 17]
            silk_seal.append(silk_seal_temp)
        bomdata["silk_seal"] = silk_seal

        pack_require = []
        pack_require_name = ['外箱尺寸', '内衬形式', '标签要求', '贴纸尺寸图纸']
        for i in range(len(pack_require_name)):
            pack_require_temp = {}
            pack_require_temp["name"] = pack_require_name[i]
            pack_require_temp["value"] = row[i + 22]
            pack_require.append(pack_require_temp)
        bomdata["pack_require"] = pack_require

        categoryID = []
        categoryID_name = ['外壳类型','芯片LOGO','芯片ID','资产条码']
        for i in range(len(categoryID_name)):
            categoryID_temp = {}
            categoryID_temp["name"] = categoryID_name[i]
            categoryID_temp["value"] = row[i+26]
            categoryID.append(categoryID_temp)
        bomdata["categoryID"] = categoryID

        #### 下方row[15]不变，
        special_msg = {}
        special_msg["name"] = '特殊物料替换'
        special_msg["value"] = row[15]
        bomdata["special_msg"] = special_msg


        LQ_confirmation = {}
        LQ_confirmation["name"] ='联桥确认人'
        LQ_confirmation["value"] = row[30]
        LQ_confirmation["date"] = row[31]
        bomdata["LQ_confirmation"] = LQ_confirmation

        receive_sign = {}
        receive_sign["name"] = '项目管理部'
        receive_sign["value"] = ''
        receive_sign["date"] = ''
        bomdata["receive_sign"] = receive_sign
    # file_num 为空时,为新增bom文件
    else:
        cursor = connection.cursor()
        cursor.execute(his_sql, (initdata[0], initdata[1]))
        log.info(his_sql % (initdata[0], initdata[1]))
        row = cursor.fetchone()

        bomdata["billid"] = billid
        hardware_head = []
        hardware_head_name = ['客户名称', '订单区域', '受订单号', '计划号', '安装区域/用途', "技术要求"]
        for i in range(len(hardware_head_name)):
            hardware_head_temp = {}
            hardware_head_temp["name"] = hardware_head_name[i]
            if row and i==5:
                hardware_head_temp["value"] = row[i + 3]
            else:
                hardware_head_temp["value"] = initdata[i]
            hardware_head.append(hardware_head_temp)
        bomdata["hardware_head"] = hardware_head

        product_data = []
        product_data_name = ['产品种类', '订单数量', 'PCB版本', '安装图版本', '确认人', '确认时间']
        for i in range(len(product_data_name)):
            product_data_temp = {}
            product_data_temp["name"] = product_data_name[i]
            if row and i<5 and i>1:
                product_data_temp["value"] = row[i + 9]
            else:
                if i == 0:
                    product_data_temp["value"] = initdata[6]
                elif i == 1:
                    product_data_temp["value"] = initdata[7]
                else:
                    product_data_temp["value"] = ''
            product_data.append(product_data_temp)
        bomdata["product_data"] = product_data
        # 软件版本确认单迁移数据
        pack_explain = {}
        pack_explain["name"] = "外观包装说明"
        if row:
            pack_explain["value"] = row[16]
        else:
            pack_explain["value"] = ''
        bomdata["pack_explain"] = pack_explain

        silk_seal = []
        silk_seal_name = ['厂家名称', '规格型号', '资产条码', '丝印方式', 'CAD图纸']
        for i in range(len(silk_seal_name)):
            silk_seal_temp = {}
            silk_seal_temp["name"] = silk_seal_name[i]
            if row:
                silk_seal_temp["value"] = row[i + 17]
            else:
                silk_seal_temp["value"] = ''
            silk_seal.append(silk_seal_temp)
        bomdata["silk_seal"] = silk_seal

        pack_require = []
        pack_require_name = ['外箱尺寸', '内衬形式', '标签要求', '贴纸尺寸图纸']
        for i in range(len(pack_require_name)):
            pack_require_temp = {}
            pack_require_temp["name"] = pack_require_name[i]
            if row:
                pack_require_temp["value"] = row[i + 22]
            else:
                pack_require_temp["value"] = ''
            pack_require.append(pack_require_temp)
        bomdata["pack_require"] = pack_require

        categoryID = []
        categoryID_name = ['外壳类型', '芯片LOGO', '芯片ID', '资产条码']
        for i in range(len(categoryID_name)):
            categoryID_temp = {}
            categoryID_temp["name"] = categoryID_name[i]
            if row:
                categoryID_temp["value"] = row[i + 26]
            else:
                categoryID_temp["value"] = ''
            categoryID.append(categoryID_temp)
        bomdata["categoryID"] = categoryID

        #### 下方row[15]不变，
        special_msg = {}
        special_msg["name"] = '特殊物料替换'
        if row:
            special_msg["value"] = row[15]
        else:
            special_msg["value"] = ''
        bomdata["special_msg"] = special_msg

        LQ_confirmation = {}
        # 查询填写人姓名
        cur = connection.cursor()
        username_sql = "select USER_NAME from sys_user where USER_ID = %s"
        cur.execute(username_sql, user_id)
        log.info(username_sql % user_id)
        row = cur.fetchone()
        username = row[0]
        cur.close()
        LQ_confirmation["name"] = '联桥确认人'
        LQ_confirmation["value"] = username
        LQ_confirmation["date"] = ''
        bomdata["LQ_confirmation"] = LQ_confirmation

        receive_sign = {}
        receive_sign["name"] = '项目管理部'
        receive_sign["value"] = ''
        receive_sign["date"] = ''
        bomdata["receive_sign"] = receive_sign

        # 生成 BOM文件号
        cur = connection.cursor()
        cur.execute(select_sql, billid)
        log.info(select_sql % billid)
        rows = cur.fetchall()
        if rows:
            his_file_num = rows[-1][-1]
            tmp_list = his_file_num.split('-')
            if len(tmp_list)==1:
                bomdata["file_number"] = his_file_num + '-01'
            else:
                num = int(tmp_list[1]) + 1
                if num<10:
                    bomdata["file_number"] = tmp_list[0] + '-0' + str(num)
                else:
                    bomdata["file_number"] = tmp_list[0] + '-' + str(num)

        else:
            # bomdata["file_number"] = 'LQYX' + billid[2:] + '-01' 2020/04/24 修改命名规则
            bomdata["file_number"] = billid + '-01'

    bomform = {}
    bomform["bomform"] = bomdata
    jsondata["bominfo"] = bomform

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------lqkjbill-bomView-end---------------------------')
    return HttpResponse(s)

# 获取Software 列表
def getSoftwareList(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-getSoftwareList-begin---------------------------')

    billid = reqest_body.get('billid', None)

    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }
    softwareHead = [
        {
            'name': 'file_num',
            'label': '文件号',
            'width': 150
        },
        {
            'name': 'cus_name',
            'label': '客户名称',
            'width': 150
        },
        {
            'name': 'order_area',
            'label': '订单区域',
            'width': 150
        },
        {
            'name': 'order_num',
            'label': '受订单号',
            'width': 150
        },
        {
            'name': 'plan_num',
            'label': '计划号',
            'width': 150
        }
    ]
    jsondata['softwareHead'] = softwareHead

    softwareData = []
    # 查询数据库中对应评审单已录入的 Software
    sql = "select id,file_number,customer_name,order_area,order_number,plan_number from yw_bill_software_version_confirm WHERE id IN " \
          "(SELECT MAX(id) FROM yw_bill_software_version_confirm where head_id = %s group by head_id,file_number)"
    cursor = connection.cursor()
    cursor.execute(sql, billid)
    log.info(sql % billid)
    rows = cursor.fetchall()
    if rows:
        for item in rows:
            tmp_dict = {
                'file_num': item[1],
                'cus_name': item[2],
                'order_area': item[3],
                'order_num': item[4],
                'plan_num': item[5]
            }
            softwareData.append(tmp_dict)
    jsondata['softwareData'] = softwareData

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------lqkjbill-getSoftwareList-end---------------------------')
    return HttpResponse(s)

# 软件版本页面数据
def softwareView(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-softwareView-begin---------------------------')

    user_id = reqest_body.get('uid', None)
    billid = reqest_body.get('billid',None)
    file_num = reqest_body.get('file_num',None)
    syncdata = reqest_body.get('syncdata',None)

    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "softwareinfo": {}
    }

    # 部分初始数据根据传递的数据填写
    initdata = [syncdata["orderdata"][0]["cus_value"], syncdata["productdata"][-1]["cpvalue"][0],
                syncdata["orderdata"][0]["order_value"], syncdata["orderdata"][0]["plan_value"],
                syncdata["productdata"][-1]["cpvalue"][0], '', syncdata["productdata"][0]["cpvalue"][0],
                syncdata["productdata"][2]["cpvalue"][0]]

    # 查询数据库中是否存在对应评审单号的记录
    select_sql = "select id,file_number from yw_bill_software_version_confirm WHERE id IN " \
                 "(SELECT MAX(id) FROM yw_bill_software_version_confirm where head_id = %s group by head_id,file_number)"
    # 根据客户名称+使用地区查询历史数据作为回填的数据
    his_sql = "select * from yw_bill_software_version_confirm where customer_name= %s and install_area= %s order by id desc limit 1"
    # 查询software最新的一条记录
    sql = "select * from yw_bill_software_version_confirm where head_id = %s and file_number= %s order by id desc limit 1"
    # 有file_num 时，为修改software
    if file_num:
        cursor = connection.cursor()
        cursor.execute(sql, (billid,file_num))
        log.info(sql % (billid,file_num))
        row = cursor.fetchone()
        cursor.close()

        softwaredata = {}
        softwaredata["billid"] = billid
        softwaredata["file_number"] = file_num

        software_head = []
        software_head_name = ['客户名称', '订单区域', '受订单号', '计划号', '安装区域/用途', '技术要求']
        for i in range(len(software_head_name)):
            software_head_temp = {}
            software_head_temp["name"] = software_head_name[i]
            software_head_temp["value"] = row[i + 3]
            software_head.append(software_head_temp)
        softwaredata["software_head"] = software_head

        product_data = []
        # product_data_name = ['产品种类', '订单数量', '软件内部版本信息', '软件外部信息', '硬件版本信息', '模块ID', '厂商代码', '芯片代码', '确认人', '确认时间'] 2020.04.13 新增外部版本日期
        product_data_name = ['产品种类', '订单数量', '软件内部版本信息', '软件外部信息', '外部版本日期','硬件版本信息', '模块ID', '厂商代码', '芯片代码', '确认人', '确认时间']
        for i in range(len(product_data_name)):
            product_data_temp = {}
            product_data_temp["name"] = product_data_name[i]
            product_data_temp["value"] = row[i + 9]
            product_data.append(product_data_temp)
        softwaredata["product_data"] = product_data

        shell_else = {}
        shell_else["name"] = '其他'
        shell_else["value"] = row[20]
        softwaredata["shell_else"] = shell_else

        LQ_confirmation = {}
        LQ_confirmation["name"] = '联桥确认人'
        LQ_confirmation["value"] = row[21]
        LQ_confirmation["date"] = row[22]
        softwaredata["LQ_confirmation"] = LQ_confirmation

        receive_sign = {}
        receive_sign["name"] = '项目管理部'
        receive_sign["value"] = ''
        receive_sign["date"] = ''
        softwaredata["receive_sign"] = receive_sign
    # 无file_num 时，为新增software
    else:
        cursor = connection.cursor()
        cursor.execute(his_sql, (initdata[0], initdata[1]))
        log.info(his_sql % (initdata[0], initdata[1]))
        row = cursor.fetchone()
        cursor.close()

        softwaredata = {}
        softwaredata["billid"] = billid
        # 生成 software 文件号
        cur = connection.cursor()
        cur.execute(select_sql, billid)
        log.info(select_sql % billid)
        rows = cur.fetchall()
        if rows:
            his_file_num = rows[-1][-1]
            tmp_list = his_file_num.split('-')
            if len(tmp_list) == 1:
                softwaredata["file_number"] = his_file_num + '-01'
            else:
                num = int(tmp_list[1]) + 1
                if num<10:
                    softwaredata["file_number"] = tmp_list[0] + '-0' + str(num)
                else:
                    softwaredata["file_number"] = tmp_list[0] + '-' + str(num)
        else:
            # softwaredata["file_number"] = 'LQYX' + billid[2:] + '-01' 2020/04/24 修改命名规则
            softwaredata["file_number"] = billid + '-01'

        software_head = []
        software_head_name = ['客户名称','订单区域','受订单号','计划号','安装区域/用途','技术要求']
        for i in range(len(software_head_name)):
            software_head_temp = {}
            software_head_temp["name"] = software_head_name[i]
            if row and i==5:
                software_head_temp["value"] = row[i+3]
            else:
                software_head_temp["value"] = initdata[i]
            software_head.append(software_head_temp)
        softwaredata["software_head"] = software_head

        product_data = []
        # product_data_name = ['产品种类','订单数量','软件内部版本信息','软件外部信息','硬件版本信息','模块ID','厂商代码','芯片代码','确认人','确认时间'] 2020.04.13 新增外部版本日期
        product_data_name = ['产品种类','订单数量','软件内部版本信息','软件外部信息','外部版本日期','硬件版本信息','模块ID','厂商代码','芯片代码','确认人','确认时间']
        for i in range(len(product_data_name)):
            product_data_temp = {}
            product_data_temp["name"] = product_data_name[i]
            if row and i<5 and i>1:
                product_data_temp["value"] = row[i+9]
            else:
                if i == 0:
                    product_data_temp["value"] = initdata[6]
                elif i == 1:
                    product_data_temp["value"] = initdata[7]
                else:
                    product_data_temp["value"] = ''
            product_data.append(product_data_temp)
        softwaredata["product_data"] = product_data


        shell_else = {}
        shell_else["name"] = '其他'
        if row:
            shell_else["value"] = row[20]
        else:
            shell_else["value"] = ''
        softwaredata["shell_else"] = shell_else

        LQ_confirmation = {}
        LQ_confirmation["name"] = '联桥确认人'
        # 查询填写人姓名
        cur = connection.cursor()
        username_sql = "select USER_NAME from sys_user where USER_ID = %s"
        cur.execute(username_sql, user_id)
        log.info(username_sql % user_id)
        row = cur.fetchone()
        username = row[0]
        cur.close()
        LQ_confirmation["value"] = username
        LQ_confirmation["date"] = ''
        softwaredata["LQ_confirmation"] = LQ_confirmation

        receive_sign = {}
        receive_sign["name"] = '项目管理部'
        receive_sign["value"] = ''
        receive_sign["date"] = ''
        softwaredata["receive_sign"] = receive_sign

    softwareform = {}
    softwareform["softwareform"] = softwaredata
    jsondata["softwareinfo"] = softwareform

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------lqkjbill-softwareView-end---------------------------')
    return HttpResponse(s)

# 提交ndform上传的数据
def uploadndform(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-uploadndform-begin---------------------------')

    user_id = reqest_body.get('uid', None)
    ndformdata = reqest_body.get('ndformdata',None)
    infoid = reqest_body.get('infoid',None)
    modelinfo = reqest_body.get('modelinfo',None)
    syncdata = reqest_body.get('syncdata', None)

    head_data, body_data = ndform_analysis(ndformdata,modelinfo)

    # # 判断body_data 是否为list 类型，不是则 研发订单配方号错误
    # if type(body_data) is not list:
    #     s = public.setrespinfo({"respcode": "900201", "respmsg": body_data})
    #     return HttpResponse(s)

    # 数据提交到数据库
    head_insert_sql = review_form_head_sql()
    head_his_insert_sql = review_form_head_his_sql()
    body_insert_sql = review_form_body_sql()
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 数据对照列表
    data_msg_sql = "SELECT column_comment FROM INFORMATION_SCHEMA.Columns WHERE table_name= 'yw_bill_review_form_head'  order by ordinal_position"
    cur = connection.cursor()  # 创建游标
    cur.execute(data_msg_sql)
    data_msg = cur.fetchall()
    cur.close()


    # 验证评审单号是否重复
    billid = head_data[1]
    if billid:
        cursor = connection.cursor()
        sql_one = "select * from  yw_bill_review_form_head where head_id = %s"
        cursor.execute(sql_one, billid)
        log.info(sql_one % billid)
        row = cursor.fetchone()
        if row and infoid=='':
            s = public.setrespinfo({"respcode": "900001", "respmsg": "评审单号重复!"})
            return HttpResponse(s)
        elif row and infoid != '':   #修改操作
            sql_two = "select column_name  from information_schema.columns where table_name='yw_bill_review_form_head' order by ordinal_position"
            cursor.execute(sql_two)
            column_name_data = cursor.fetchall()
            sql_three = "select * from  yw_bill_review_form_head where id = %s" % infoid
            cursor.execute(sql_three)
            history_data = cursor.fetchone()

            tmp_str = ''
            data_tuple = ()
            for i in range(1, len(history_data)):
                if str(head_data[i])=='':
                    s = public.setrespinfo({"respcode": "900001", "respmsg": data_msg[i][0] + "未填写!"})
                    return HttpResponse(s)
                elif str(head_data[i]) != str(history_data[i]):
                    tmp_str += "%s='%s',"
                    tmp_tuple = ()
                    tmp_tuple = column_name_data[i] + (str(head_data[i]),)
                    data_tuple += tmp_tuple
            update_sql = "update yw_bill_review_form_head set " + tmp_str + "where head_id = '%s'"
            index = update_sql.rfind(',')
            if index!=-1:
                # update_sql= update_sql[:index] +' '+ update_sql[index+1:]
                update_whole_sql = "update yw_bill_review_form_head set " + tmp_str + "insert_time='%s' where head_id = '%s'"

                data_tuple = data_tuple + (nowTime,head_data[1],)
                update_whole_sql = update_whole_sql % data_tuple

                cursor.execute(update_whole_sql)
                # 对存入历史表的纪录 时间进行修改
                tmp_head_data = list(head_data)
                tmp_head_data[3] = nowTime
                head_data = tuple(tmp_head_data)
                cursor.execute(head_his_insert_sql, head_data)  # 将该记录同时存入历史表
                log.info(update_whole_sql)
                log.info(head_his_insert_sql % head_data)
                connection.commit()
                cursor.close()
            else:
                cursor.close() #数据未做修改，不执行任何sql语句
        else:
            # 发起申请时操作
            none_count = 0
            for i in range(1, len(head_data) - 1):
                if not head_data[i]:
                    none_count += 1
                    s = public.setrespinfo({"respcode": "900001", "respmsg": data_msg[i][0] + "未填写!"})
                    return HttpResponse(s)
            if none_count != 0:
                s = public.setrespinfo({"respcode": "900001", "respmsg": "数据未填写完整!"})
                return HttpResponse(s)
            else:
                cursor = connection.cursor()
                cursor.execute(head_insert_sql, head_data)  #将数据插入原始表
                cursor.execute(head_his_insert_sql,head_data) #将该记录同时存入历史表
                log.info(head_insert_sql % head_data)
                log.info(head_his_insert_sql % head_data)
                cursor.close()
                audit_init(billid)  # 新建待审核信息表
                proof_init(billid)  # 新建待校验信息表
            #  使用模板数据时，硬件、软件 版本确认单直接查询模板数据插入
            if modelinfo:
                sql_hardmodel = "select * from yw_bill_hardware_version_confirm_model where head_id=%s and state='1'"
                sql_softmodel = "select * from yw_bill_software_version_confirm_model where head_id=%s and state='1'"
                cursor = connection.cursor()
                cursor.execute(sql_hardmodel, modelinfo)
                hardmodel,softmodel= None,None
                if cursor.fetchone():
                    hardmodel = list(cursor.fetchone())
                cursor.execute(sql_softmodel, modelinfo)
                if cursor.fetchone():
                    softmodel = list(cursor.fetchone())
                nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # file_num = 'LQYX' + billid[2:] + '-01' 2020/04/24 修改命名规则
                file_num = billid + '-01'
                # 根据订单实际数据替换模板数据
                initdata = [syncdata["orderdata"][0]["cus_value"], syncdata["productdata"][-1]["cpvalue"][0],
                            syncdata["orderdata"][0]["order_value"], syncdata["orderdata"][0]["plan_value"],
                            syncdata["productdata"][-1]["cpvalue"][0], '', syncdata["productdata"][0]["cpvalue"][0],
                            syncdata["productdata"][2]["cpvalue"][0]]

                if hardmodel:
                    # 新增一条对应的硬件版本确认单记录
                    bom_sql = hardware_version_confirm_sql()
                    hardmodel[0] = None
                    hardmodel[1] = billid
                    hardmodel[2] = file_num
                    hardmodel[14] = nowTime
                    hardmodel[31] = nowTime
                    for i in range(len(initdata)):
                        hardmodel[i + 3] = initdata[i]
                    hardmodel = tuple(hardmodel)
                    cursor.execute(bom_sql, hardmodel)
                    log.info(bom_sql % hardmodel)
                if softmodel:
                    # 新增一条对应的软件版本确认单记录
                    software_sql = software_version_confirm_sql()
                    softmodel[0] = None
                    softmodel[1] = billid
                    softmodel[2] = file_num
                    softmodel[18] = nowTime
                    softmodel[21] = nowTime
                    for i in range(len(initdata)):
                        softmodel[i + 3] = initdata[i]
                    softmodel = tuple(softmodel)
                    cursor.execute(software_sql, softmodel)
                    log.info(software_sql % softmodel)
                cursor.close()
    else:
        s = public.setrespinfo({"respcode": "900001", "respmsg": "评审单号未填写!"})
        return HttpResponse(s)
    if body_data:
        # 将PMC填写的计划单号更新到市场计划单号栏
        upd_planid_sql = "update yw_bill_review_form_head set plan_number=%s where head_id=%s"
        # body 数据提交
        cur = connection.cursor()  # 创建游标
        sql_five = "select * from  yw_bill_review_form_body where head_id = %s order by id desc limit 1"
        cur.execute(sql_five,body_data[0][1])
        his_row = cur.fetchone()
        for item in body_data:
            sql_four = "select * from  yw_bill_review_form_body where head_id = %s and name_id = %s and row_id= %s order by id desc limit 1"
            # 有历史数据时
            if his_row:
                cur.execute(sql_four,(item[1],item[2],item[3]))
                his_record = cur.fetchone()
                if his_record:
                    flag = check_same(data=item,row=his_record)
                    if flag:
                        pass # 数据未修改，不新增记录
                    else:
                        if item[2] == 5 and item[4] == '计划单号' and item[5]:
                            cur.execute(upd_planid_sql, (item[5], item[1]))
                            connection.commit()
                            log.info(upd_planid_sql % (item[5], item[1]))
                            #  更新软硬件版本确认单
                            upd_hardsoft_planid(billid=item[1],planid=item[5])
                        tmp_item = list(item)
                        tmp_item[7] = nowTime
                        item = tuple(tmp_item)
                        cur.execute(body_insert_sql,item)
                        log.info(body_insert_sql % item)
                else:
                    if item[2] == 5 and item[4] == '计划单号' and item[5]:
                        cur.execute(upd_planid_sql, (item[5], item[1]))
                        connection.commit()
                        log.info(upd_planid_sql % (item[5], item[1]))
                        #  更新软硬件版本确认单
                        upd_hardsoft_planid(billid=item[1], planid=item[5])
                    cur.execute(body_insert_sql, item)
                    log.info(body_insert_sql % item)
            # 无历史数据时
            else:
                if item[2]==5 and item[4]=='计划单号' and item[5]:
                    cur.execute(upd_planid_sql,(item[5],item[1]))
                    connection.commit()
                    log.info(upd_planid_sql % (item[5], item[1]))
                    #  更新软硬件版本确认单
                    upd_hardsoft_planid(billid=item[1], planid=item[5])
                cur.execute(body_insert_sql, item)
                log.info(body_insert_sql % item)
        cur.close()
    else:
        s = public.setrespinfo({"respcode": "900011", "respmsg": "主体数据为空，请注意是否具有操作权限!"})
        return HttpResponse(s)


    # 返回成功数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "提交成功",
        "trantype": reqest_body.get('trantype', None),
    }

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjbill-uploadndform--end---------------------------')
    return HttpResponse(s)

# 提交bom上传的数据
def uploadbomform(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-uploadbomform-begin---------------------------')

    user_id = reqest_body.get('uid', None)
    bomformdata = reqest_body.get('bomformdata',None)

    # 返回成功数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "提交成功",
        "trantype": reqest_body.get('trantype', None),
    }

    bomdata = bomform_analysis(bomformdata)

    # 查询数据库历史数据 sql
    sql = "select * from  yw_bill_hardware_version_confirm where head_id = %s order by id desc limit 1"
    # 提交数据到数据库 sql
    bom_sql = hardware_version_confirm_sql()
    # 数据对照列表
    data_msg_sql = "SELECT column_comment FROM INFORMATION_SCHEMA.Columns WHERE table_name= 'yw_bill_hardware_version_confirm' order by ordinal_position"
    cur = connection.cursor()  # 创建游标
    cur.execute(data_msg_sql)
    data_msg = cur.fetchall()
    cur.close()
    none_count = 0

    for i in range(1, len(bomdata) - 1):
        if bomdata[i] == '':
            none_count += 1
            s = public.setrespinfo({"respcode": "900001", "respmsg": data_msg[i][0]+ "未填写!"})
            return HttpResponse(s)

    if none_count != 0:
        s = public.setrespinfo({"respcode": "900001", "respmsg": "数据未填写完整!"})
        return HttpResponse(s)
    else:
        cur = connection.cursor()  # 创建游标
        # 查询数据库最新记录并对比，不相同新插入一条记录
        cur.execute(sql,bomdata[1])
        row = cur.fetchone()
        # 查询到历史数据进行对比，若不同则新增一条记录；未查询到则直接插入一条新记录
        if row:
            flag = check_same(data=bomdata,row=row)
            if flag:
                cur.close()  # 提交数据与数据库记录相同，不新插入数据
            else:
                nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                tmp_bomdata = list(bomdata)
                tmp_bomdata[14] = nowTime
                tmp_bomdata[31] = nowTime
                bomdata = tuple(tmp_bomdata)
                cur.execute(bom_sql, bomdata)
                log.info(bom_sql % bomdata)
                cur.close()
        else:
            cur.execute(bom_sql, bomdata)
            log.info(bom_sql % bomdata)
            cur.close()
    jsondata['file_num'] = bomdata[2]

    # 生成Word 文档，并同步到SVN
    CreateWord(bomdata[1],bomdata[2],'hardware')

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjbill-uploadbomform--end---------------------------')
    return HttpResponse(s)

# 提交software上传的数据
def uploadsoftwareform(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-uploadsoftwareform-begin---------------------------')

    # 返回成功数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "提交成功",
        "trantype": reqest_body.get('trantype', None),
    }

    user_id = reqest_body.get('uid', None)
    softwareformdata = reqest_body.get('softwareformdata',None)

    softwaredata = softwareform_analysis(softwareformdata)

    # 查询数据库数据 sql
    sql = "select * from  yw_bill_software_version_confirm where head_id = %s order by id desc limit 1"
    # 提交数据到数据库
    software_sql = software_version_confirm_sql()
    # 数据对照列表
    data_msg_sql = "SELECT column_comment FROM INFORMATION_SCHEMA.Columns WHERE table_name= 'yw_bill_software_version_confirm' order by ordinal_position"
    cur = connection.cursor()  # 创建游标
    cur.execute(data_msg_sql)
    data_msg = cur.fetchall()
    cur.close()
    none_count = 0
    for i in range(1, len(softwaredata) - 1):
        if softwaredata[i] == '':
            none_count += 1
            s = public.setrespinfo({"respcode": "900001", "respmsg": data_msg[i][0]+"未填写!"})
            return HttpResponse(s)

    if none_count != 0:
        s = public.setrespinfo({"respcode": "900001", "respmsg": "数据未填写完整!"})
        return HttpResponse(s)
    else:
        cur = connection.cursor()  # 创建游标
        # 查询数据库最新记录并对比，不相同新插入一条记录
        cur.execute(sql, softwaredata[1])
        row = cur.fetchone()
        # 查询到历史数据进行对比，若不同则新增一条记录；未查询到则直接插入一条新记录
        if row:
            flag = check_same(data=softwaredata, row=row)
            if flag:
                cur.close()  # 提交数据与数据库记录相同，不新插入数据
            else:
                nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                tmp_softwaredata = list(softwaredata)
                tmp_softwaredata[19] = nowTime
                tmp_softwaredata[22] = nowTime
                softwaredata = tuple(tmp_softwaredata)
                cur.execute(software_sql, softwaredata)
                log.info(software_sql % softwaredata)
                cur.close()
        else:
            cur.execute(software_sql, softwaredata)
            log.info(software_sql % softwaredata)
            cur.close()


    jsondata["file_num"] = softwaredata[2]

    # 生成Word 文档，并同步到SVN
    CreateWord(softwaredata[1], softwaredata[2], 'software')

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjbill-uploadsoftwareform--end---------------------------')
    return HttpResponse(s)

# ndform 详情页 and 修改页面
def ndformdetail(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-ndformdetail-begin---------------------------')

    # 返回成功数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
        "ndforminfo": {}
    }

    user_id = reqest_body.get('uid', None)
    billid = reqest_body.get('billid',None)
    infoid = reqest_body.get('infoid',None)
    modelinfo = reqest_body.get('modelinfo',None)
    alter = reqest_body.get('alter',None)

    cursor = connection.cursor()
    if modelinfo:
        sql_one = "SELECT * FROM yw_bill_review_form_head_model where head_id = %s and state='1'"
        cursor.execute(sql_one, modelinfo)
        log.info(sql_one % modelinfo)
        row = cursor.fetchone()
    elif infoid == '':
        sql_one = "select * from  yw_bill_review_form_head where head_id = %s order by id desc limit 1"
        cursor.execute(sql_one,billid)
        log.info(sql_one % billid)
        row = cursor.fetchone()
    else:
        sql_one = "select * from  yw_bill_review_form_head where id = %s order by id desc limit 1"
        cursor.execute(sql_one,infoid)
        log.info(sql_one % infoid)
        row = cursor.fetchone()
        billid = row[1]

    ndform = {}
    ndform["title"] = '需求评审单'
    if row:
        ndform["billdata"] = {'name': '评审单号', 'billid': billid,'proname':'投产单号','proid':row[2], 'billtype_name': ['订单', '备货计划', '小批送样','试产'],
                              'billtype': row[3]}
        ndform["billdate"] = row[4]
        ndform["orderdata"] = [
            {'order_name': '受订单号', 'order_value': row[5], 'plan_name': '计划单号', 'plan_value': row[6], 'cus_name': '客户名称',
             'cus_value': row[7]}, ]
        cpkey = ['产品名称', '规格型号', '数量', '交货日期', '业务员', '使用地区']
        tmplsit = []
        for i in range(len(cpkey)):
            tmpdict = {}
            tmpdict['cpkey'] = cpkey[i]
            tmpdict['cpvalue'] = [row[i + 8], '']
            tmplsit.append(tmpdict)
        ndform["cpdata"] = tmplsit
        ndform['tsyq'] = row[14]
        ndform['tbgz'] = row[15]
    cursor.close()
    # 主体数据
    cursor = connection.cursor()
    if modelinfo:
        sql_two = "select * from yw_bill_review_form_body_model where id in (SELECT MAX(id) as id FROM yw_bill_review_form_body_model WHERE head_id= %s " \
                  "GROUP BY head_id,name_id,row_id) ORDER BY name_id,row_id"
        cursor.execute(sql_two, modelinfo)
        log.info(sql_two % modelinfo)
        rows = cursor.fetchall()
    else:
        sql_two = "select * from yw_bill_review_form_body where id in (SELECT MAX(id) as id FROM yw_bill_review_form_body WHERE head_id= %s GROUP BY head_id,name_id,row_id) ORDER BY name_id,row_id"
        cursor.execute(sql_two,billid)
        log.info(sql_two % billid)
        rows = cursor.fetchall()

    # htyq_name = ['芯片ID', '是否要求与送样产品一致', '说明要求', '纸箱要求', '装箱要求', '箱贴格式', '备品', '出厂检验报告', '发货要求', '其他']
    htyq_name = ['芯片ID', '是否要求与送样产品一致', '是否需要型式试验', '纸箱要求', '装箱要求', '箱贴格式', '备品', '出厂检验报告', '发货要求', '其他']
    pzname = ['产品母配方（*）', '硬件版本（*）', '软件版本（*）', '关键元器件清单', '结构件（*）', '包材', '耗材', '铭牌图纸', '接线图纸', '订单配方号']
    # wlname = ['物料齐套', '外加工', '其他'] # 2020.03.27 去掉外加工
    wlname = ['物料齐套', '其他']
    zlname = ['检验标准', '其他']
    gyname = ['SOP-作业指导', '工艺流程', '烧录软件版本', '产测软件版本', '抄表软件版本', '入库时间', '其他']
    # pcmname = ['入库时间', '其他'] # 2020.03.27 增加回板时间，计划单号
    pcmname = ['回板时间','入库时间','计划单号', '其他']
    section_list = ['htyq', 'pzdata', 'wldata', 'zldata', 'gydata', 'pcmdata']
    fzr_list = ['htyqFzr', 'pzFzr', 'wlFzr', 'zlFzr', 'gyFzr', 'pcmFzr']
    section_name_list = [htyq_name, pzname, wlname, zlname, gyname, pcmname]
    temp = []
    for i in range(len(section_list)):
        temp.append([])

    temp_value = []
    temp_cltime = []
    temp_wctime = []
    if rows:
        for i in range(len(section_list)):
            for item in rows:
                if int(item[2]) == i:
                    if str(item[2]) == '1' and int(item[3]) > 0 and int(item[3]) < 6:
                        temp_value.append(item[5])
                        temp_cltime.append(item[6])
                        temp_wctime.append(item[7])
                        if str(item[3]) == '5':
                            temp[i].append({'name': item[4], 'value': temp_value, 'cltime': temp_cltime,'wctime':temp_wctime})
                            ndform[section_list[i]] = temp[i]
                            ndform[fzr_list[i]] = item[8]
                    else:
                        temp[i].append({'name': item[4], 'value': [item[5]], 'cltime': [item[6]],'wctime': [item[7]]})
                        ndform[section_list[i]] = temp[i]
                        ndform[fzr_list[i]] = item[8]

    for i in range(len(temp)):
        if len(temp[i]) == 0:
            for index, other_item in enumerate(section_name_list[i]):
                if i==0 and index == 1:
                    temp[i].append({'name': other_item, 'value': ['保持一致'], 'cltime': [''],'wctime': ['']})
                    ndform[section_list[i]] = temp[i]
                    ndform[fzr_list[i]] = ''
                elif (i==0 and index == 2) or (i==0 and index == 6):
                    temp[i].append({'name': other_item, 'value': ['无需'], 'cltime': [''],'wctime': ['']})
                    ndform[section_list[i]] = temp[i]
                    ndform[fzr_list[i]] = ''
                elif i==0 and index == 7:
                    temp[i].append({'name': other_item, 'value': ['需要'], 'cltime': [''],'wctime': ['']})
                    ndform[section_list[i]] = temp[i]
                    ndform[fzr_list[i]] = ''
                elif i==1 and index == 1:
                    temp[i].append({'name': other_item, 'value': ['', '', '', '', ''], 'cltime': ['', '', '', '', ''],'wctime': ['', '', '', '', '']})
                    ndform[section_list[i]] = temp[i]
                    ndform[fzr_list[i]] = ''
                elif i==1 and index == 3:
                    temp[i].append({'name': other_item, 'value': ['见附件'], 'cltime': [''],'wctime': ['']})
                    ndform[section_list[i]] = temp[i]
                    ndform[fzr_list[i]] = ''
                else:
                    temp[i].append({'name': other_item, 'value': [''], 'cltime': [''],'wctime': ['']})
                    ndform[section_list[i]] = temp[i]
                    ndform[fzr_list[i]] = ''
    cursor.close()
    ndform['pzdata_remask'] = ['BOM', 'PCB1', 'PCB2', 'PCB3', 'PCB4']
    psdata = []
    name_key = ['营销中心', '项目管理部', '物控中心', '质控中心', '制造中心', '财务部']
    for i in range(len(name_key)):
        psdata_temp = {}
        psdata_temp["name_key"] = name_key[i]
        psdata_temp["name_value"] = ''
        psdata_temp["date_key"] = '日期'
        psdata_temp["date_value"] = ''
        psdata_temp["num_key"] = name_key[i]
        psdata_temp["num_value"] = ''
        psdata.append(psdata_temp)
    ndform["psdata"] = psdata
    # 检查审核审批信息是否缺失，若缺失补充
    check_audit_proof(billid)

    # 不为模板渲染时
    if not modelinfo:
        # 审核信息 和 校验信息
        audit_select_sql = "select * from yw_bill_audit_info where audit_billid = %s order by section_id"
        proof_select_sql = "select * from yw_bill_proof_info where proof_billid = %s order by section_id"
        cur = connection.cursor()
        cur.execute(audit_select_sql,billid)

        audit_rows = cur.fetchall()
        cur.execute(proof_select_sql,billid)
        proof_rows = cur.fetchall()
        cur.close()
    else:
        audit_rows,proof_rows = None,None

    tmp_auditdata,tmp_proofdata = [],[]
    section_list = ['市场部','项目管理部','物控中心','质控中心','制造中心','PMC']
    if audit_rows and proof_rows:
        for i in range(len(audit_rows)):
            # 审核信息
            if audit_rows[i][6] =='0':
                auditdata_temp = {}
                auditdata_temp["name"] = audit_rows[i][3]
                auditdata_temp["value"] = ''
                auditdata_temp["date"] = ''
                tmp_auditdata.append(auditdata_temp)
            else:
                auditdata_temp = {}
                auditdata_temp["name"] = audit_rows[i][3]
                auditdata_temp["value"] = audit_rows[i][4]
                auditdata_temp["date"] = audit_rows[i][5]
                tmp_auditdata.append(auditdata_temp)
            # 校验信息
            if proof_rows[i][6] == '0':
                proofdata_temp = {}
                proofdata_temp["name"] = proof_rows[i][3]
                proofdata_temp["value"] = ''
                proofdata_temp["date"] = ''
                tmp_proofdata.append(proofdata_temp)
            else:
                proofdata_temp = {}
                proofdata_temp["name"] = proof_rows[i][3]
                proofdata_temp["value"] = proof_rows[i][4]
                proofdata_temp["date"] = proof_rows[i][5]
                tmp_proofdata.append(proofdata_temp)
    else:
        for item in section_list:
            tmp_dict = {
                'name': item,
                'value': '',
                'date': ''
            }
            tmp_auditdata.append(tmp_dict)
            tmp_proofdata.append(tmp_dict)

    # 页面审核、审批信息调整
    auditdata,proofdata = [],[]
    for item in section_term:
        auditdata.append(tmp_auditdata[item])
        proofdata.append(tmp_proofdata[item])


    ndform["auditdata"] = auditdata
    ndform["proofdata"] = proofdata

    # 权限设置
    term_list = ['scpower', 'yfpower', 'wkpower', 'zkpower', 'propower',
                 'pmcpower', 'myexportword', 'myprint', 'myprooof', 'myaudit', 'myresetaudit','hardsoft_write']
    cur = connection.cursor()
    sql = "select * from yw_bill_power_config where user_id = %s"
    cur.execute(sql, user_id)
    power_row = cur.fetchone()
    cur.close()
    if power_row:
        for i in range(0, len(term_list)):
            if power_row[i+1] == 'Y':
                ndform[term_list[i]] = True
            elif power_row[i+1] == 'N':
                ndform[term_list[i]] = False
            elif power_row[i+1] == 'All':
                ndform[term_list[i]] = True
            else:
                ndform[term_list[i]] = True
    else:
        for item in term_list:
            ndform[item] = False
    # 评审单正常
    if alter == True and row[-1]=='1':
        ndform['myalter'] = True
        # 非模板渲染时
        if not modelinfo:
            # 判断是否已审核，并赋予相应操作权限
            audit_count,myone,mytwo = 0,0,0
            flag_num = -1
            for index,i in enumerate(section_term):
                if audit_rows[i][6]=='1':
                    ndform[term_list[i]] = False
                    audit_count = audit_count + 1
                    if power_row and (power_row[11]) == 'Y':
                        myone = myone + 1
                else:
                    if power_row and (power_row[10]) == 'Y':
                        mytwo = mytwo + 1
                    flag_num = index+1
                    break

            # flag_num 代表的部门的下级部门不能填写
            if flag_num!=-1 and flag_num !=len(audit_rows):
                for i in range(flag_num,len(section_term)):
                    ndform[term_list[section_term[i]]] = False

            if audit_rows[1][6]=='1':
                ndform['hardsoft_write'] = False
            if audit_count != 6:
                # ndform['myexportword'] = False
                ndform['myprint'] = False
            if myone>0:
                ndform['myresetaudit'] = True
            if mytwo>0:
                ndform['myaudit'] = True
            if mytwo==6:
                ndform['myresetaudit'] = False
            if myone==6:
                ndform['myaudit'] = False
    # 评审单已作废
    elif row[-1]=='2':
        for i in range(len(term_list)):
            ndform[term_list[i]] = False
        ndform['myalter'] = False
    # 评审单已锁定
    else:
        for i in range(len(term_list)):
            if i!=6 and i!=7:
                ndform[term_list[i]] = False
        ndform['myalter'] = False
        audit_count = 0
        for i in range(len(audit_rows)):
            if audit_rows[i][6] == '1':
                audit_count = audit_count + 1
        if audit_count != 6:
            ndform['myprint'] = False

    ndformdata = {}
    ndformdata["ndform"] = ndform
    jsondata["ndforminfo"] = ndformdata

    # 附件信息 未使用
    filelist = []
    select_annex_sql = "select * from yw_bill_annex_info where billid=%s"
    select_annex_name="select file_name from yw_workflow_file where id=%s"
    cur = connection.cursor()
    cur.execute(select_annex_sql,billid)
    annex_row = cur.fetchone()
    if annex_row:
        if annex_row[2]:
            fileidlist = annex_row[2].split('/')
            for item in fileidlist:
                cur.execute(select_annex_name,int(item))
                name_row = cur.fetchone()
                if name_row:
                    filelist.append({
                        "name":name_row[0],
                        "fileid":item
                    })
    cur.close()
    jsondata["filelist"]=filelist
    jsondata["downfilelist"]=filelist


    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjbill-ndformdetail--end---------------------------')
    return HttpResponse(s)

# 评审单附件上传
def handfilelist(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-handfilelist-begin---------------------------')

    # 返回成功数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "上传成功",
        "trantype": reqest_body.get('trantype', None),
    }

    user_id = reqest_body.get('uid', None)
    billid = reqest_body.get('billid', None)
    filelist = reqest_body.get('filelist',[])
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    fileid_list = []
    if filelist:
        for item in filelist:
            fileid_list.append(item['fileid'])
        filestr = '/'.join(fileid_list)
    else:
        filestr = ''

    select_annex_sql = "select * from yw_bill_annex_info where billid=%s"
    intser_sql = "insert into yw_bill_annex_info(id,billid,annex,status,upload_date) value(%s,%s,%s,%s,%s)"
    select_billid_sql = "select * from yw_bill_review_form_head where head_id = %s"
    update_annex_sql = "update yw_bill_annex_info set annex=%s,status=%s,upload_date=%s where id=%s"
    cur = connection.cursor()
    cur.execute(select_annex_sql, billid)
    row_annex = cur.fetchone()
    if row_annex:
        his_filedict = eval(row_annex[3])
        tmpdict = his_filedict

        for item in fileid_list:
            tmp = his_filedict.get(str(item),None)
            if not tmp:
                tmpdict[str(item)] = 0
        for item in list(his_filedict.keys()):
            if item not in fileid_list:
                del tmpdict[str(item)]
        filedict = str(tmpdict)
        cur.execute(update_annex_sql, (filestr,filedict, nowTime, row_annex[0]))
    else:
        if filestr:
            cur.execute(select_billid_sql,billid)
            row = cur.fetchone()
            if row:
                tmpdict = {}
                for item in fileid_list:
                    tmpdict[str(item)] = 0
                filedict = str(tmpdict)
                cur.execute(intser_sql,(None,billid,filestr,filedict,nowTime))
            else:
                s = public.setrespinfo({"respcode": "900012", "respmsg": "请先提交评审单!"})
                return HttpResponse(s)
            cur.close()
        else:
            s = public.setrespinfo({"respcode": "900012", "respmsg": "请先选择文件!"})
            return HttpResponse(s)

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjbill-handfilelist--end---------------------------')
    return HttpResponse(s)

# 评审单附件下载信息
def filelist_info(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-filelist_info-begin---------------------------')

    # 返回成功数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    user_id = reqest_body.get('uid', None)
    billid = reqest_body.get('billid', None)

    # 附件信息
    filelist = []
    select_annex_sql = "select * from yw_bill_annex_info where billid=%s"
    select_annex_name = "select file_name from yw_workflow_file where id=%s"
    cur = connection.cursor()
    cur.execute(select_annex_sql, billid)
    annex_row = cur.fetchone()
    if annex_row:
        if annex_row[2]:
            fileidlist = annex_row[2].split('/')
            status = eval(annex_row[3])
            for item in fileidlist:
                cur.execute(select_annex_name, int(item))
                name_row = cur.fetchone()
                if name_row:
                    filelist.append({
                        "name": name_row[0],
                        "fileid": item,
                        "state":status[str(item)]
                    })
        else:
            s = public.setrespinfo({"respcode": "900013", "respmsg": "无上传的文件!"})
            return HttpResponse(s)
    else:
        s = public.setrespinfo({"respcode": "900013", "respmsg": "无上传的文件!"})
        return HttpResponse(s)

    cur.close()
    jsondata["downfilelist"] = filelist

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjbill-filelist_info--end---------------------------')
    return HttpResponse(s)

# ndform 审批接口
def ndformaudit(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-ndformaudit-begin---------------------------')

    # 返回成功数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "提交审批成功",
        "trantype": reqest_body.get('trantype', None),
    }

    user_id = reqest_body.get('uid', None)
    billid = reqest_body.get('billid', None)
    # 检查审核审批信息是否缺失，若缺失补充
    check_audit_proof(billid)
    # 权限配置信息查询
    cur = connection.cursor()
    sql = "select audit_power from yw_bill_power_config where user_id = %s"
    cur.execute(sql, user_id)
    power_row = cur.fetchone()
    cur.close()
    temp_list = []
    if power_row[0] == 'All':
        for i in range(6):
            temp_list.append(i)
    elif power_row[0] == 'N':
        pass
    else:
        temp_list.append(int(power_row[0]))
    if len(temp_list) !=0:
        # 获取用户姓名和当前时间
        cur = connection.cursor()
        username_sql = "select USER_NAME from sys_user where USER_ID = %s"
        cur.execute(username_sql, user_id)
        log.info(username_sql % user_id)
        row = cur.fetchone()
        username = row[0]
        nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_audit_sql = "update yw_bill_audit_info set auditor= %s,audit_date=%s,sup_audit_date=%s,audit_state='1' where audit_billid=%s and section_id = %s"
        select_sup_sql = "select audit_date from yw_bill_audit_info where audit_billid=%s and section_id = %s"
        cur = connection.cursor()
        for item in temp_list:
            if item !=0:
                index = section_term.index(int(item))-1
                section_id = section_term[index]
                # PMC 审批时，软硬件版本确认单同步SVN
                cur.execute(select_sup_sql,(billid,section_id))
                row = cur.fetchone()
                if row:
                    if row[0]:
                        sup_date = row[0]
                    else:
                        s = public.setrespinfo({"respcode": "900020", "respmsg": "提交审批失败，您的上一级无审批（历史）记录!"})
                        return HttpResponse(s)
            else:
                sup_date = None
            if item == 5:
                log.info(nowTime + '  ' + username + '审批，执行同步SVN操作')
                upd_hardsoft_svn(billid)
                log.info(nowTime+'【'+billid+'】'+'执行同步SVN完成' )
            if item ==1:
                # 查询订单配方sql
                bom_sql = "SELECT * from yw_bill_review_form_body WHERE head_id = %s " \
                          "and require_name LIKE '订单配方号' ORDER BY id desc LIMIT 1"
                # 研发订单配方号校验标志
                jhbom_flag = False
                cur.execute(bom_sql,billid)
                row = cur.fetchone()
                if row:
                    jhbom = row[5]
                    if jhbom:
                        jhbom_flag = checkJHBom(jhbom)
                    # 订单配方号校验失败时 body_data 返回字符串形式以供调用他的函数判断
                    if not jhbom_flag:
                        s = public.setrespinfo({"respcode": "900050", "respmsg": "提交审批失败，NPI订单配方未完成!"})
                        return HttpResponse(s)



            tmp_data = (username,nowTime,sup_date,billid,item)
            cur.execute(update_audit_sql,tmp_data)
            connection.commit()
        cur.close()
    else:
        s = public.setrespinfo({"respcode": "900009", "respmsg": "没有操作权限!"})
        return HttpResponse(s)

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjbill-ndformaudit--end---------------------------')
    return HttpResponse(s)

# 重置审核状态接口
def reset_audit(request,reqest_body):
    log = public.logger
    log.info('----------------------Button-lockndform-begin---------------------------')

    billid = reqest_body.get('billid')
    uid = reqest_body.get('uid')
    checksum = reqest_body.get('checksum')

    # 先模拟返回数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "重置成功",
        "trantype": reqest_body.get('trantype', None),
    }
    # 权限配置信息查询
    cur = connection.cursor()
    sql = "select reaudit_power from yw_bill_power_config where user_id = %s"
    cur.execute(sql, uid)
    power_row = cur.fetchone()
    cur.close()
    temp_list = []
    if power_row[0] == 'All':
        for i in range(6):
            temp_list.append(i)
    elif power_row[0] == 'N':
        pass
    else:
        temp_list.append(int(power_row[0]))
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

# ndform 校验接口
def ndformproof(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-ndformproof-begin---------------------------')

    # 返回成功数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "校验成功",
        "trantype": reqest_body.get('trantype', None),
    }

    user_id = reqest_body.get('uid', None)
    billid = reqest_body.get('billid', None)
    modelinfo = reqest_body.get('modelinfo', None)
    # 检查审核审批信息是否缺失，若缺失补充
    check_audit_proof(billid)
    # 权限配置信息查询
    cur = connection.cursor()
    sql = "select proof_power from yw_bill_power_config where user_id = %s"
    cur.execute(sql, user_id)
    power_row = cur.fetchone()
    cur.close()
    temp_list = []
    if power_row[0] == 'All':
        for i in range(6):
            temp_list.append(i)
    elif power_row[0] == 'N':
        pass
    else:
        temp_list.append(int(power_row[0]))
    if len(temp_list) !=0:
        # 获取用户姓名和当前时间
        cur = connection.cursor()
        username_sql = "select USER_NAME from sys_user where USER_ID = %s"
        cur.execute(username_sql, user_id)
        log.info(username_sql % user_id)
        row = cur.fetchone()
        username = row[0]
        nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_proof_sql = "update yw_bill_proof_info set proof_people= %s,proof_date=%s,proof_state='1' where proof_billid=%s and section_id = %s"
        cur = connection.cursor()
        for item in temp_list:
            tmp_data = (username,nowTime,billid,item)
            cur.execute(update_proof_sql,tmp_data)
            connection.commit()
        cur.close()

    # 审核信息 和 校验信息
    audit_select_sql = "select * from yw_bill_audit_info where audit_billid = %s order by section_id"
    proof_select_sql = "select * from yw_bill_proof_info where proof_billid = %s order by section_id"
    cur = connection.cursor()
    cur.execute(audit_select_sql, billid)

    audit_rows = cur.fetchall()
    cur.execute(proof_select_sql, billid)
    proof_rows = cur.fetchall()
    cur.close()

    auditdata, proofdata = [], []
    if audit_rows and proof_rows:
        for i in range(len(audit_rows)):
            # 审核信息
            if audit_rows[i][6] == '0':
                auditdata_temp = {}
                auditdata_temp["name"] = audit_rows[i][3]
                auditdata_temp["value"] = ''
                auditdata_temp["date"] = ''
                auditdata.append(auditdata_temp)
            else:
                auditdata_temp = {}
                auditdata_temp["name"] = audit_rows[i][3]
                auditdata_temp["value"] = audit_rows[i][4]
                auditdata_temp["date"] = audit_rows[i][5]
                auditdata.append(auditdata_temp)
            # 校验信息
            if proof_rows[i][6] == '0':
                proofdata_temp = {}
                proofdata_temp["name"] = proof_rows[i][3]
                proofdata_temp["value"] = ''
                proofdata_temp["date"] = ''
                proofdata.append(proofdata_temp)
            else:
                proofdata_temp = {}
                proofdata_temp["name"] = proof_rows[i][3]
                proofdata_temp["value"] = proof_rows[i][4]
                proofdata_temp["date"] = proof_rows[i][5]
                proofdata.append(proofdata_temp)
    jsondata['auditdata'] = auditdata
    jsondata['proofdata'] = proofdata

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjbill-ndformproof--end---------------------------')
    return HttpResponse(s)

# doprint 打印接口
def doprint(request,reqest_body):
    log = public.logger
    log.info('----------------------lqkjbill-doprint-begin---------------------------')

    # 返回成功数据
    jsondata = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    user_id = reqest_body.get('uid', None)
    billid = reqest_body.get('billid', None)

    # cursor = connection.cursor()
    # select_audit_sql = "select * from yw_bill_audit_info where audit_billid = %s and audit_state = '0'"
    # cursor.execute(select_audit_sql, billid)
    # audit_rows = cursor.fetchone()
    # cursor.close()
    # if audit_rows:
    #     s = public.setrespinfo({"respcode": "900010", "respmsg": audit_rows[3] + "未审核,操作失败!"})
    #     return HttpResponse(s)

    s = json.dumps(jsondata, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)

    log.info('----------------------lqkjbill-doprint--end---------------------------')
    return HttpResponse(s)

# 审核信息表 插入数据
def audit_init(billid):
    log = public.logger
    # sql 语句
    audit_insert_sql = "insert into yw_bill_audit_info(id,section_id,audit_billid,audit_section,auditor,audit_date,audit_state) " \
                       "values(%s,%s,%s,%s,%s,%s,%s)"
    audit_name = ['市场部', '项目管理部', '物控中心', '质控中心', '制造中心', 'PMC']
    cur = connection.cursor()
    for i in range(len(audit_name)):
        tmp_tuple = (None,i,billid,audit_name[i],None,None,'0')
        cur.execute(audit_insert_sql,tmp_tuple)
        log.info(audit_insert_sql % tmp_tuple)
    connection.commit()
    cur.close()

# 校验信息表 插入数据
def proof_init(billid):
    log = public.logger
    # sql 语句
    proof_insert_sql = "insert into yw_bill_proof_info(id,section_id,proof_billid,proof_section,proof_people,proof_date,proof_state) " \
                       "values(%s,%s,%s,%s,%s,%s,%s)"
    proof_name = ['市场部', '项目管理部', '物控中心', '质控中心', '制造中心', 'PMC']
    cur = connection.cursor()
    for i in range(len(proof_name)):
        tmp_tuple = (None,i,billid,proof_name[i],None,None,'0')
        cur.execute(proof_insert_sql,tmp_tuple)
        log.info(proof_insert_sql%tmp_tuple)
    connection.commit()
    cur.close()

# 评审单ndformdata解析
def ndform_analysis(ndformdata,modelinfo):
    body_data_list = []
    body_fzr_list = []
    billdata = ndformdata["billdata"]
    orderdata = ndformdata["orderdata"]
    cpdata = ndformdata["cpdata"]
    tsyq = ndformdata["tsyq"]
    tbgz = ndformdata["tbgz"]

    htyq = ndformdata["htyq"]
    body_data_list.append(htyq)
    htyqFzr = ndformdata["htyqFzr"]
    body_fzr_list.append(htyqFzr)
    pzdata = ndformdata["pzdata"]
    body_data_list.append(pzdata)
    pzFzr = ndformdata["pzFzr"]
    body_fzr_list.append(pzFzr)
    wldata = ndformdata["wldata"]
    body_data_list.append(wldata)
    wlFzr = ndformdata["wlFzr"]
    body_fzr_list.append(wlFzr)
    zldata = ndformdata["zldata"]
    body_data_list.append(zldata)
    zlFzr = ndformdata["zlFzr"]
    body_fzr_list.append(zlFzr)
    gydata = ndformdata["gydata"]
    body_data_list.append(gydata)
    gyFzr = ndformdata["gyFzr"]
    body_fzr_list.append(gyFzr)
    pcmdata = ndformdata["pcmdata"]
    body_data_list.append(pcmdata)
    pcmFzr = ndformdata["pcmFzr"]
    body_fzr_list.append(pcmFzr)

    # htyqwctime = ndformdata["htyqwctime"]
    # pzwctime = ndformdata["pzwctime"]
    # wlwctime = ndformdata["wlwctime"]
    # zlwctime = ndformdata["zlwctime"]
    # gywctime = ndformdata["gywctime"]
    # pcmwctime = ndformdata["pcmwctime"]
    # wctimelist = [htyqwctime,pzwctime,wlwctime,zlwctime,gywctime,pcmwctime]

    billid = billdata["billid"]
    billtype = billdata["billtype"]
    proid = billdata["proid"]
    billdate = ndformdata["billdate"]
    order_value = orderdata[0]["order_value"]
    plan_value = orderdata[0]["plan_value"]
    cus_value = orderdata[0]["cus_value"]

    power_list = []
    scpower = ndformdata["scpower"]
    power_list.append(scpower)
    yfpower = ndformdata["yfpower"]
    power_list.append(yfpower)
    wkpower = ndformdata["wkpower"]
    power_list.append(wkpower)
    zkpower = ndformdata["zkpower"]
    power_list.append(zkpower)
    propower = ndformdata["propower"]
    power_list.append(propower)
    pmcpower = ndformdata["pmcpower"]
    power_list.append(pmcpower)
    # 判断是否为模板渲染，若为模板渲染：解析时power_list所有项为false;
    # 不为模板渲染时，不做修改
    if modelinfo:
        for i in range(len(power_list)):
            power_list[i] = True



    product_msg = []
    for i in range(len(cpdata)):
        product_msg.append(cpdata[i]["cpvalue"][0])

    product_tuple = ()
    for item in product_msg:
        protuple = (item,)
        product_tuple = product_tuple + protuple

    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not billdate:
        billdate = nowTime
    # 评审单主体数据
    head_data = (None, billid, proid, billtype, billdate, order_value, plan_value, cus_value) + product_tuple + (tsyq, tbgz, '1')

    body_data = []  # 评审单明细数据
    for i in range(len(power_list)):
        if power_list[i] == True:
            count = 0
            for index,item in enumerate(body_data_list[i]):
                for j in range(len(item["value"])):
                    if not item["cltime"][j] and not item["value"][j]:
                        item["cltime"][j] = None
                        item["wctime"][j] = None
                    else:
                        if not item["cltime"][j]:
                            item["cltime"][j] = None
                        if not item["wctime"][j]:
                            item["wctime"][j] = nowTime
                    temp_tuple = (None, billid, i, count, item["name"], item["value"][j], item["cltime"][j], item["wctime"][j], body_fzr_list[i])
                    body_data.append(temp_tuple)
                    count = count + 1
    #                 # 研发订单配方号校验标志
    #                 jhbom_flag = True
    #                 if i==1 and ("订单配方号" in temp_tuple[4]):
    #                     jhbom = temp_tuple[5]
    #                     if jhbom:
    #                         jhbom_flag = checkJHBom(jhbom)
    #                     else:
    #                         jhbom_flag = False
    #                 body_data.append(temp_tuple)
    #                 count = count + 1
    # # 订单配方号校验失败时 body_data 返回字符串形式以供调用他的函数判断
    # if not jhbom_flag:
    #     body_data = "订单配方未完成！"
    return head_data,body_data

# BOM bomformdata解析
def bomform_analysis(bomformdata):
    bomdata = []
    billid = bomformdata["billid"]
    file_number = bomformdata["file_number"]
    hardware_head = bomformdata["hardware_head"]
    product_data = bomformdata["product_data"]
    pack_explain = bomformdata["pack_explain"]
    silk_seal = bomformdata["silk_seal"]
    pack_require = bomformdata["pack_require"]
    categoryID = bomformdata["categoryID"]
    special_msg = bomformdata["special_msg"]
    LQ_confirmation = bomformdata["LQ_confirmation"]
    receive_sign = bomformdata["receive_sign"]

    bomdata.append(billid)
    bomdata.append(file_number)

    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if product_data[-1]["value"]=='':
        product_data[-1]["value"] = nowTime


    list = [hardware_head, product_data,]
    for i in range(len(list)):
        for j in range(len(list[i])):
            bomdata.append(list[i][j]["value"])
    bomdata.append(special_msg["value"])
    bomdata.append(pack_explain["value"])
    lists = [silk_seal,pack_require,categoryID]
    for i in range(len(lists)):
        for j in range(len(lists[i])):
            bomdata.append(lists[i][j]["value"])

    if LQ_confirmation["date"] == '':
        LQ_confirmation["date"] = nowTime


    bomdata.append(LQ_confirmation["value"])
    bomdata.append(LQ_confirmation["date"])

    valuedata = (None,)
    for item in bomdata:
        tmptuple = (item,)
        valuedata = valuedata + tmptuple

    data = valuedata + ('1',)

    return data

# software softwareformdata解析
def softwareform_analysis(softwareformdata):
    billid = softwareformdata["billid"]
    file_number = softwareformdata["file_number"]
    software_head = softwareformdata["software_head"]
    product_data = softwareformdata["product_data"]
    shell_else = softwareformdata["shell_else"]
    LQ_confirmation = softwareformdata["LQ_confirmation"]
    receive_sign = softwareformdata["receive_sign"]

    softwaredata = [billid, file_number]
    nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if product_data[-1]["value"] == '':
        product_data[-1]["value"] = nowTime

    list = [software_head, product_data]
    for i in range(len(list)):
        for j in range(len(list[i])):
            softwaredata.append(list[i][j]["value"])
    softwaredata.append(shell_else["value"])

    if LQ_confirmation["date"] == '':
        LQ_confirmation["date"] = nowTime
    softwaredata.append(LQ_confirmation["value"])
    softwaredata.append(LQ_confirmation["date"])

    valuedata = (None,)
    for item in softwaredata:
        tmptuple = (item,)
        valuedata = valuedata + tmptuple

    data = valuedata + ('1',)
    return data

# 提取yw_bill_review_form_head insert语句
def review_form_head_sql():
    sql_one = "select column_name  from information_schema.columns where table_name='yw_bill_review_form_head' order by ordinal_position"
    cursor = connection.cursor()  # 创建游标
    cursor.execute(sql_one)
    data_two = cursor.fetchall()
    new_str = "INSERT INTO yw_bill_review_form_head(%s) values(%s)"
    valuelist = ''
    valuedata = ''
    for i in range(len(data_two)):
        temp_value = str(data_two[i][0])
        if i == 0:
            valuelist  = temp_value
            valuedata = '%s'
        else:
            valuelist = valuelist + ',' + temp_value
            valuedata = valuedata + ',' + '%s'
    sql = new_str %(valuelist,valuedata)

    cursor.close()
    return sql

# 提取yw_bill_review_form_head_his insert语句
def review_form_head_his_sql():
    sql_one = "select column_name  from information_schema.columns where table_name='yw_bill_review_form_head_his' order by ordinal_position"
    cursor = connection.cursor()  # 创建游标
    cursor.execute(sql_one)
    data_two = cursor.fetchall()
    new_str = "INSERT INTO yw_bill_review_form_head_his(%s) values(%s)"
    valuelist = ''
    valuedata = ''
    for i in range(len(data_two)):
        temp_value = str(data_two[i][0])
        if i == 0:
            valuelist  = temp_value
            valuedata = '%s'
        else:
            valuelist = valuelist + ',' + temp_value
            valuedata = valuedata + ',' + '%s'
    sql = new_str %(valuelist,valuedata)

    cursor.close()
    return sql

# 提取yw_bill_review_form_body insert语句
def review_form_body_sql():
    sql_one = "select column_name  from information_schema.columns where table_name='yw_bill_review_form_body' order by ordinal_position"
    cursor = connection.cursor()  # 创建游标
    cursor.execute(sql_one)
    data_two = cursor.fetchall()
    new_str = "INSERT INTO yw_bill_review_form_body(%s) values(%s)"
    valuelist = ''
    valuedata = ''
    for i in range(len(data_two)):
        temp_value = str(data_two[i][0])
        if i == 0:
            valuelist = temp_value
            valuedata = '%s'
        else:
            valuelist = valuelist + ',' + temp_value
            valuedata = valuedata + ',' + '%s'
    sql = new_str % (valuelist, valuedata)
    cursor.close()
    return sql

# 提取yw_bill_hardware_version_confirm insert语句
def hardware_version_confirm_sql():
    sql_three = "select column_name from information_schema.columns where table_name='yw_bill_hardware_version_confirm' order by ordinal_position"
    cursor = connection.cursor()  # 创建游标
    cursor.execute(sql_three)
    data_two = cursor.fetchall()
    new_str = "INSERT INTO yw_bill_hardware_version_confirm(%s) values(%s)"
    valuelist = ''
    valuedata = ''
    for i in range(len(data_two)):
        temp_value = str(data_two[i][0])
        if i == 0:
            valuelist = temp_value
            valuedata = '%s'
        else:
            valuelist = valuelist + ',' + temp_value
            valuedata = valuedata + ',' + '%s'
    sql = new_str % (valuelist, valuedata)
    cursor.close()
    return sql

# 提取yw_bill_software_version_confirm insert语句
def software_version_confirm_sql():
    sql_four = "select column_name  from information_schema.columns where table_name='yw_bill_software_version_confirm' order by ordinal_position"
    cursor = connection.cursor()  # 创建游标
    cursor.execute(sql_four)
    data_two = cursor.fetchall()
    new_str = "INSERT INTO yw_bill_software_version_confirm(%s) values(%s)"
    valuelist = ''
    valuedata = ''
    for i in range(len(data_two)):
        temp_value = str(data_two[i][0])
        if i == 0:
            valuelist = temp_value
            valuedata = '%s'
        else:
            valuelist = valuelist + ',' + temp_value
            valuedata = valuedata + ',' + '%s'
    sql = new_str % (valuelist, valuedata)
    cursor.close()
    return sql

# 检查提交数据与数据库数据是否相同  相同返回 True,不相同返回 False
def check_same(data,row):
    # 利用MD5加密 提交数据 和 数据库数据，并对加密后的数据做比较(md5加密未使用)
    hand_data = []
    for i in range(1,len(data)):
        hand_data.append(str(data[i]))
    # hand_data = str(hand_data)
    historical_data = []
    for i in range(1,len(row)):
        historical_data.append(str(row[i]))
    # historical_data = str(historical_data)
    # hash_hand_data = hashlib.md5(hand_data.encode(encoding='UTF-8')).hexdigest()
    # hash_historical_data = hashlib.md5(historical_data.encode(encoding='UTF-8')).hexdigest()

    if hand_data == historical_data:
        return True
    else:
        return False

# 单个评审单进度信息
def sched_one(billid):
    cur = connection.cursor()
    # head 表信息sql
    heal_scsql = "select * from yw_bill_review_form_head where head_id=%s"

    # body 表信息 sql (统计对应部门的填写)
    section_scsql = "SELECT * FROM yw_bill_review_form_body WHERE head_id = %s and name_id=%s and require_value !='' " \
                    "GROUP BY head_id,name_id,row_id"

    # 硬件版本确认单 sql
    bom_scsql = "select * FROM yw_bill_hardware_version_confirm WHERE head_id = %s"

    # 软件版本确认单 sql
    software_scsql = "select * FROM yw_bill_software_version_confirm WHERE head_id = %s"

    # 审核信息 sql
    proof_scsql = "SELECT DISTINCT proof_state,proof_date,id FROM yw_bill_proof_info WHERE proof_billid = %s ORDER BY section_id limit 0,6"

    # 审批信息 sql
    audit_scsql = "SELECT DISTINCT audit_state,id FROM yw_bill_audit_info WHERE audit_billid = %s ORDER BY section_id limit 0,6"

    # 检查审核审批信息是否缺失，若缺失补充
    check_audit_proof(billid)
    # 各部门填写进度信息
    section_truenum = [10, 14, 3, 2, 7, 2]  # 各部门应填数量对照
    section_sc = []  # 各部门应填进度数组 未填写：-1 部分填写：0 填写完成：1
    section_scstatus = []  # 各部门对应填进度数组 前段页面步骤条 状态 wait:未填写  process：填写中 success:填写完成
    for i in range(6):
        cur.execute(section_scsql, (billid, i))
        section_scrows = cur.fetchall()
        tmp_len1 = len(section_scrows)
        if tmp_len1 == 0:
            section_sc.append('未填写')
            section_scstatus.append('wait')
        elif tmp_len1 == section_truenum[i] and section_scrows[0][-1]!='':
            section_sc.append('填写完成')
            section_scstatus.append('success')
        else:
            section_sc.append('填写中')
            section_scstatus.append('process')

    # 单独处理市场部填写进度
    cur.execute(heal_scsql,billid)
    head_row = cur.fetchone()  # head信息
    for item in head_row:
        if item == '暂无' or item == ' ':
            section_sc[0] = '填写中'
            section_scstatus[0] = 'process'
    # 单独处理研发部填写进度
    cur.execute(bom_scsql,billid)
    bom_row = cur.fetchall()
    cur.execute(software_scsql,billid)
    software_row = cur.fetchall()
    if bom_row and software_row:
        if section_scstatus[1] == 'wait':
            section_scstatus[1] = 'process'
            section_sc[1] = '填写中'
    elif bom_row:
        if section_scstatus[1] == 'wait':
            section_scstatus[1] = 'process'
            section_sc[1] = '填写中'
    elif software_row:
        if section_scstatus[1] == 'wait':
            section_scstatus[1] = 'process'
            section_sc[1] = '填写中'

    # 各部门审核进度
    cur.execute(proof_scsql,billid)
    proof_rows = cur.fetchall()
    proof_sc = []
    proof_scstatus = []
    for index,item in enumerate(proof_rows):
        if item[0] == '1':
            proof_sc.append('已审核')
            section_sc[index] = section_sc[index]+ '：['+str(item[1])+']'
            proof_scstatus.append('success')
        else:
            proof_sc.append('未审核')
            proof_scstatus.append('wait')

    # 各部门审批进度
    cur.execute(audit_scsql,billid)
    audit_rows = cur.fetchall()
    audit_sc = []
    audit_scstatus = []
    for item in audit_rows:
        if item[0] == '1':
            audit_sc.append('已审批')
            audit_scstatus.append('success')
        else:
            audit_sc.append('未审批')
            audit_scstatus.append('wait')
    active_list = []
    for i in range(len(proof_scstatus)):
        if section_scstatus[i] == 'success':
            if audit_scstatus[i] == 'success':
                active_list.append(3)
            else:
                active_list.append(1)
        elif section_scstatus[i] == 'wait':
            active_list.append(0)
        else:
            active_list.append(1)

    allschedule = []
    allsection_sc = []
    allsection_scstatus = []
    for i in range(len(section_scstatus)):
        if section_scstatus[i] == 'wait':
            allsection_sc.append('未填写')
            allsection_scstatus.append('wait')
        elif audit_scstatus[i] != 'success':
            allsection_sc.append('填写中')
            allsection_scstatus.append('process')
        elif audit_scstatus[i] == 'success':
            allsection_sc.append('填写完成')
            allsection_scstatus.append('success')
    if head_row[5] == '暂无':
        allsection_sc.append('未下计划')
        allsection_scstatus.append('wait')
    else:
        allsection_sc.append('已下计划')
        allsection_scstatus.append('success')
    allactive = 0
    for index,item in enumerate(section_term):
        if audit_scstatus[item] != 'success':
            allactive = index
            break
    # 根据各部门排序索引，控制显示
    tmp_tile_list = ['市场部', '项目管理部', '物控中心', '质控中心', '制造中心', 'PMC']
    title_list,true_allsection_sc,true_allsection_scstatus = [],[],[]
    for item in section_term:
        title_list.append(tmp_tile_list[item])
        true_allsection_sc.append(allsection_sc[item])
        true_allsection_scstatus.append(allsection_scstatus[item])
    title_list.append('PMC下计划')
    true_allsection_sc.append(allsection_sc[6])
    true_allsection_scstatus.append(allsection_scstatus[6])
    all_dict = {
        'name': '总进度',
        'title': title_list,
        'description': true_allsection_sc,
        'status': true_allsection_scstatus,
        'active': allactive,
    }
    allschedule.append(all_dict)
    # 根据各部门排序索引，控制显示
    name_list = ['市场部', '项目管理部', '物控中心', '质控中心', '制造中心', 'PMC']
    for i in section_term:
        tmp_dict = {
            'name': name_list[i],
            'title': ['填写', '审核', '审批'],
            'description': [section_sc[i], proof_sc[i], audit_sc[i]],
            'status': [section_scstatus[i], proof_scstatus[i], audit_scstatus[i]],
            'active': active_list[i],
        }
        allschedule.append(tmp_dict)

    cur.close()
    return allschedule

# 查询评审单审核审批数据是否缺失，缺失时补充
# 查询评审单审核审批数据是否多余，多余时少出id小的记录
def check_audit_proof(billid):
    cur = connection.cursor()
    audit_sql = "SELECT * from yw_bill_audit_info where audit_billid = %s"
    del_audit_sql = "delete from yw_bill_audit_info where id = %s"
    proof_sql = "SELECT * from yw_bill_proof_info where proof_billid = %s"
    del_proof_sql = "delete from yw_bill_proof_info where id = %s"
    # 检查审核表
    cur.execute(audit_sql,billid)
    audit_rows = cur.fetchall()
    if len(audit_rows)>6:
        for i in range(6,len(audit_rows)):
            cur.execute(del_audit_sql,audit_rows[i][0])
    else:
        if not audit_rows:
            audit_init(billid)
    # 检查审批表
    cur.execute(proof_sql, billid)
    proof_rows = cur.fetchall()
    if len(proof_rows)>6:
        for i in range(6, len(proof_rows)):
            cur.execute(del_proof_sql, proof_rows[i][0])
    else:
        if not proof_rows:
            proof_init(billid)

# 软硬件版本确认单 生成word文档
def CreateWord(billid,filenum,type):
    log = public.logger
    # 生成word
    data_dic = {}
    if filenum and type == 'hardware':
        file_name = "硬件版本确认单_" + filenum + ".docx"
        temp_path = os.path.join(public.localhome, 'hardware_software_temp', 'hardware.docx')
        cursor = connection.cursor()
        key_sql = "select column_name from information_schema.columns where table_name='yw_bill_hardware_version_confirm' order by ordinal_position"
        cursor.execute(key_sql)
        keys_rows = cursor.fetchall()
        value_sql = "select * from yw_bill_hardware_version_confirm where file_number= %s order by id desc limit 1"
        cursor.execute(value_sql, filenum)
        value_row = cursor.fetchone()
        for i in range(2, len(keys_rows) - 1):
            data_dic[keys_rows[i][0]] = value_row[i]
    elif filenum and type == 'software':
        file_name = "软件版本确认单_" + filenum + ".docx"
        temp_path = os.path.join(public.localhome, 'hardware_software_temp', 'software.docx')
        cursor = connection.cursor()
        key_sql = "select column_name from information_schema.columns where table_name='yw_bill_software_version_confirm' order by ordinal_position"
        cursor.execute(key_sql)
        keys_rows = cursor.fetchall()
        value_sql = "select * from yw_bill_software_version_confirm where file_number= %s order by id desc limit 1"
        cursor.execute(value_sql, filenum)
        value_row = cursor.fetchone()
        for i in range(2, len(keys_rows) - 1):
            data_dic[keys_rows[i][0]] = value_row[i]
    else:
        s = public.setrespinfo({"respcode": "900031", "respmsg": "请求信息有误!"})
        return HttpResponse(s)

    so = SvnOpera()
    root = '/home/admin/lqkj_admin/SVN/项目外来文件'
    year, month = getPsYearMonth(billid)
    # save_path = '%s/%s年订单目录/%s月订单详情/%s/未审核/' % (root, year, month, billid)
    save_path = '%s/%s年订单目录/%s月订单详情/%s/' % (root, year, month, billid)

    # save_path=getPsFileUri(billid)
    if not os.path.exists(save_path):  # 如果路径不存在
        os.makedirs(save_path)

    save_path = save_path + file_name

    doc = DocxTemplate(temp_path)  # 加载模板文件
    doc.render(data_dic)  # 填充数据
    doc.save(save_path)  # 保存目标文件

    file = open(save_path, 'rb')
    # 如果有计划号，移动文件到计划号文件夹
    plan_id = getPlanidByPsid(billid)
    if plan_id[0:2] != 'JH':
        plan_id = None
    if plan_id:
        movePs2Plan(log, plan_id, billid)
    # 更新svn
    so.svnUp()
    so.update()
    return file

# #根据评审单号获取文件路径
# def getPsFileUri(ps_id):
#     year = '20%s' % ps_id[2:4]
#     month = ps_id[4:6].lstrip('0')
#     # 保存文件到本地文件上传目录
#     filepath = public.localhome + 'SVN/项目外来文件/合同评审单/%s年%s月/%s/未审核/' % (year, month, ps_id)
#     return filepath

# 各部门单个评审单完成所用时间
def count_time(billid):
    # 查询历史表，获取评审单发起时间
    his_sql = "SELECT insert_time FROM yw_bill_review_form_head_his WHERE head_id = %s ORDER BY id  LIMIT 1"
    # 查询审核表信息，计算部门的用时
    check_audit_proof(billid)
    audit_sql = "SELECT * FROM yw_bill_audit_info WHERE audit_billid = %s ORDER BY id,section_id"
    cur = connection.cursor()
    cur.execute(his_sql,billid)
    create_time = cur.fetchone()[0]
    cur.execute(audit_sql,billid)
    rows = cur.fetchall()
    time_list = []
    for index,item in enumerate(rows):
        if item[6] =='1':
            delta = item[5] - create_time
            total_hours = delta.days * 24 + delta.seconds / 3600
            if total_hours<0.01:
                total_hours = round(total_hours, 4)
            else:
                total_hours = round(total_hours, 2)
            time_list.append(total_hours)
        else:
            time_list.append(0)

    return time_list

# 各部门单个评审单完成所用时间,第二版
def count_time2(log,billid):
    # 查询历史表，获取评审单发起时间
    his_sql = "SELECT insert_time FROM yw_bill_review_form_head_his WHERE head_id = %s ORDER BY id  LIMIT 1"
    now_sql = "SELECT insert_time FROM yw_bill_review_form_head WHERE head_id = %s"
    # 查询审核表信息，计算部门的用时
    check_audit_proof(billid)
    audit_sql = "SELECT * FROM yw_bill_audit_info WHERE audit_billid = %s ORDER BY id,section_id"
    cur = connection.cursor()
    cur.execute(his_sql,billid)
    his_row = cur.fetchone()
    try:
        if his_row:
            create_time = his_row[0]
        else:
            cur.execute(now_sql,billid)
            create_time = cur.fetchone()[0]
    except Exception as e:
        log.info('报错billid=',billid)
    cur.execute(audit_sql,billid)
    rows = cur.fetchall()
    time_list = []
    for index,item in enumerate(rows):
        if index ==0 and item[6] =='1':
            delta = item[5] - create_time
            total_hours = delta.days * 24 + delta.seconds / 3600
            if total_hours<0.01:
                total_hours = round(total_hours, 4)
            else:
                total_hours = round(total_hours, 2)
            time_list.append(total_hours)
        elif item[6] =='1' and index > 0:
            delta = item[5] - item[7]
            total_hours = delta.days * 24 + delta.seconds / 3600
            if total_hours < 0.01:
                total_hours = round(total_hours, 4)
            else:
                total_hours = round(total_hours, 2)
            time_list.append(total_hours)
        else:
            time_list.append(0)

    return time_list

# 软硬件版本确认单同步计划单号
def upd_hardsoft_planid(billid,planid):
    hard_sql = "select id,file_number from yw_bill_hardware_version_confirm WHERE id IN " \
               "(SELECT MAX(id) FROM yw_bill_hardware_version_confirm where head_id = %s group by head_id,file_number)"
    soft_sql = "select id,file_number from yw_bill_software_version_confirm WHERE id IN " \
               "(SELECT MAX(id) FROM yw_bill_software_version_confirm where head_id = %s group by head_id,file_number)"
    upd_hard_sql = "UPDATE yw_bill_hardware_version_confirm SET plan_number = %s where id=%s "
    upd_soft_sql = "UPDATE yw_bill_software_version_confirm SET plan_number = %s where id=%s "

    cur = connection.cursor()
    # 更新硬件版本确认单计划号
    cur.execute(hard_sql,billid)
    hard_rows = cur.fetchall()
    if hard_rows:
        for hard in hard_rows:
            cur.execute(upd_hard_sql,(planid,hard[0]))
            connection.commit()

    # 更新软件版本确认单计划号
    cur.execute(soft_sql,billid)
    soft_rows = cur.fetchall()
    if soft_rows:
        for soft in soft_rows:
            cur.execute(upd_soft_sql,(planid,soft[0]))
            connection.commit()
    cur.close()

# PMC 审批时，软硬件版本确认单重新生成并同步SVN
def upd_hardsoft_svn(billid):
    hard_sql = "select id,file_number from yw_bill_hardware_version_confirm WHERE id IN " \
               "(SELECT MAX(id) FROM yw_bill_hardware_version_confirm where head_id = %s group by head_id,file_number)"
    soft_sql = "select id,file_number from yw_bill_software_version_confirm WHERE id IN " \
               "(SELECT MAX(id) FROM yw_bill_software_version_confirm where head_id = %s group by head_id,file_number)"
    cur = connection.cursor()
    # 硬件版本确认单重新生成并同步SVN
    cur.execute(hard_sql, billid)
    hard_rows = cur.fetchall()
    if hard_rows:
        for hard in hard_rows:
            CreateWord(billid,hard[1],'hardware')

    # 更新软件版本确认单重新生成并同步SVN
    cur.execute(soft_sql, billid)
    soft_rows = cur.fetchall()
    if soft_rows:
        for soft in soft_rows:
            CreateWord(billid, soft[1], 'software')

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
    log.info('new_path=%s'%new_path)
    for pid in ps_ids:
        old_path = '%s/%s年订单目录/%s月订单详情/%s/' % (root, year, month, pid)
        movePath(old_path[:-1],new_path[:-1])

#根据ps_id获取附件路径
def getPathByPsid(ps_id):
    root = '/home/admin/lqkj_admin/SVN/项目外来文件'
    year, month = getPsYearMonth(ps_id)
    plan_id = getPlanidByPsid(ps_id)
    if plan_id[0:2]!='JH':
        # filepath = '%s/%s年订单目录/%s月订单详情/%s/未审核/' % (root, year, month, ps_id)
        filepath = '%s/%s年订单目录/%s月订单详情/%s/' % (root, year, month, ps_id)
    else:
        # filepath = '%s/%s年订单目录/%s月订单详情/%s/未审核/' % (root, year, month, plan_id)
        filepath = '%s/%s年订单目录/%s月订单详情/%s/' % (root, year, month, plan_id)
    return filepath

class SvnOpera:
    def __init__(self, path='/home/admin/lqkj_admin/SVN/项目外来文件'):
        self.path = path

    def svnUp(self):
        os.chdir(self.path)
        os.system('svn up')

    def update(self):
        os.chdir(self.path)
        res = os.popen('svn status')
        for item in res:
            if item.find('?') != -1:
                uri = item.replace('?', '').strip()
                os.system('svn add %s' % uri)
            elif item.find('!') != -1:
                uri = item.replace('!', '').strip()
                os.system('svn delete %s' % uri)
        os.system("svn ci -m 'OASystem Add'")


#检查订单BOM是否有效
def checkJHBom( jhbom ):
    #根据最新要求(关欣刘晓民)，不再检查订单BOM, 20200628
    return True

    #
    # try:
    #     sqlserver_conn = pymssql.connect(server='192.168.2.18', user='sa', password='luyao123KEJI',
    #                                      database="db_18",
    #                                      timeout=20, autocommit=True)  # 获取连接  #sqlserver数据库链接句柄
    # except Exception as ex:
    #     pass
    #     # log.info(str(ex))
    #
    # cursor = sqlserver_conn.cursor()  # 获取光标
    # selsql = "select JH_NO from TF_JH where ID_NO='%s'" % jhbom
    # # log.info(selsql)
    # cursor.execute(selsql)
    # row = cursor.fetchone()
    # if not row:
    #     #订单配方未完成
    #     cursor.close()
    #     sqlserver_conn.close()
    #     return False
    # else:
    #     cursor.close()
    #     sqlserver_conn.close()
    #     return True



