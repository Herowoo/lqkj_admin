import sys
from django.shortcuts import render,redirect,HttpResponse
from django.db import connection, transaction
import json
from admin_app.sys import public
import datetime
import pymssql

###########################################################################################################
#MES系统数据同步到ERP系统处理函数
#add by litz, 2021.01.25
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
        # # 回滚事务
        # transaction.savepoint_rollback(sid)
    return public.respinfo

#生产领料单
def material_packing( request ):
    log = public.logger
    body = public.req_body

    def SqlServer_Conn():
        sqlserver_conn = None
        try:
            sqlserver_conn = pymssql.connect(server='10.10.1.250', user='sa', password='luyao123KEJI',
                                             database="db_18",
                                             timeout=20, autocommit=False)  # 获取连接  #sqlserver数据库链接句柄
        except Exception as ex:
            log.info(str(ex))

        return sqlserver_conn

    try:
        sqlserver_conn = SqlServer_Conn()  # 连接erp数据库
        cursor = sqlserver_conn.cursor()  # 获取光标
        if isinstance(body, dict):
            body=[body]
        for bodyitm in body:
            mo_no = bodyitm.get('MO_NO')
            # est_itm = body.get('EST_ITM')
            prd_no = bodyitm.get('PRD_NO')
            qty = bodyitm.get('QTY')

            if not mo_no: #不是工单发料，暂不同步
                # 事务回滚
                sqlserver_conn.rollback()
                sqlserver_conn.close()

                log.info("不是工单发料，暂不同步!", extra={'ptlsh':public.req_seq})
                public.respcode, public.respmsg = "680006", "不是工单发料!"
                public.respinfo = HttpResponse( public.setrespinfo() )
                return public.respinfo

            # 查询原数据信息
            sql = "SELECT MRP_NO,ID_NO, BAT_NO FROM MF_MO WHERE MO_NO='%s' " % mo_no
            log.info(sql)
            cursor.execute(sql)
            row = cursor.fetchone()
            if not row:
                # 事务回滚
                sqlserver_conn.rollback()
                sqlserver_conn.close()
                log.error("制令单号不存在!", exc_info=True, extra={'ptlsh':public.req_seq})
                public.respcode, public.respmsg = "680001", "制令单号不存在!"
                public.respinfo = HttpResponse( public.setrespinfo() )
                return public.respinfo
            mrp_no=row[0]
            id_no=row[1]
            bat_no = row[2]
            mrp_prd_name = ''
            nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            #查询表头是否已经领过料, 增加 ML_DD， 不然领料跨天会造成负库存
            sql = "select ML_NO from MF_ML where ML_DD='%s 00:00:00.000' and ML_NO like 'ML%%M%%' and MO_NO='%s' " \
                  "and MLID='ML' and ML_ID='1'  order by sys_date desc" % (nowtime[0:10], mo_no)
            log.info(sql)
            cursor.execute(sql)
            row = cursor.fetchone()
            if not row or not row[0]: #重新生成一个制令单号
                newflag = True
                sql = "select max(ML_NO) from MF_ML where ML_NO like 'ML%sM%%' " % datetime.datetime.now().strftime('%y%m')
                log.info(sql)
                cursor.execute(sql)
                row = cursor.fetchone()
                if not row or not row[0]:
                    ml_no = 'ML%sM001' % datetime.datetime.now().strftime('%y%m')
                else:
                    ml_no = 'ML%sM' % datetime.datetime.now().strftime('%y%m') + "%03d" % ( int(row[0][-3:])+1 )
            else:
                newflag = False
                ml_no = row[0]

            if newflag: #新数据，插入操作
                sql = "INSERT INTO MF_ML(MLID,ML_NO,ML_DD,ML_ID, FIX_CST, MO_NO, MRP_NO, UNIT, DEP, USR, " \
                      "CHK_MAN, CLS_DATE, ID_NO, BIL_TYPE, SYS_DATE, FIX_CST1, PRD_NAME, BAT_NO, PRT_SW,TASK_ID ) " \
                      "VALUES('ML', '%s', '%s 00:00:00.000', '1', '1', '%s','%s', '1', 'MT', '011', " \
                      "'', '', '%s', '08', '%s.000', '1', '%s','%s','N','0' )" \
                      % (ml_no, nowtime[0:10], mo_no, mrp_no, id_no, nowtime, mrp_prd_name, bat_no )
                log.info(sql)
                cursor.execute(sql)
            else:
                pass #放在后边更新了，避免锁表

            #查询制令单表身数据
            sql = "select itm, prd_no, prd_name, wh, usein_no, (QTY_RSV+QTY_LOST), CST, QTY_STD  from TF_MO " \
                  "where MO_NO='%s' and prd_no='%s'" % (mo_no, prd_no)
            log.info(sql)
            cursor.execute(sql)
            row = cursor.fetchone()
            if not row:
                # 事务回滚
                sqlserver_conn.rollback()
                sqlserver_conn.close()
                log.error("制令单明细中此料号不存在!", exc_info=True, extra={'ptlsh':public.req_seq})
                public.respcode, public.respmsg = "680002", "制令单明细中此料号不存在!"
                public.respinfo = HttpResponse( public.setrespinfo() )
                return public.respinfo
            est_itm = row[0]
            prd_name = row[2]
            wh =  row[3]
            if row[4]:
                usein_no = row[4]
            else:
                usein_no = ''
            qty_rsv = row[5]
            cst = row[6]
            if row[7]:
                qty_std = row[7]
            else:
                qty_std = 0.00

            # 查询表身是否已经领过料
            sql = "select itm, QTY from TF_ML where ML_NO='%s' and MLID='ML' and ML_ID='1' and PRD_NO='%s'" % (ml_no, prd_no)
            log.info(sql)
            cursor.execute(sql)
            row = cursor.fetchone()
            log.info("查询表身是否已经领过料:"+str(row))
            if not row or not row[0]:  # 重新生成一个制令单号
                itmnewflag = True
                sql = "select ISNULL(max(ITM),0)+1 from TF_ML where ML_NO='%s' " % (ml_no)
                cursor.execute(sql)
                itmrow = cursor.fetchone()
                nowitm = itmrow[0]
            else:
                itmnewflag = False
                nowitm = row[0]

            nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if itmnewflag:  # 新数据，插入操作
                sql = "INSERT INTO TF_ML(MLID, ML_NO, ITM, ML_DD, ML_ID, PRD_NO, PRD_NAME, MO_NO, UNIT, " \
                      "QTY, WH, PRE_ITM, EST_ITM, FIX_CST1, USEIN_NO, QTY_RSV, QTY_STD ) " \
                      "VALUES('ML', '%s', '%s','%s 00:00:00.000', '1',  '%s','%s', '%s', '1', " \
                      "%s, '%s', '%s', '%s', '1', '%s','%s', %s )" \
                      % (ml_no, nowitm, nowtime[0:10], prd_no, prd_name, mo_no,
                         int(qty), wh, nowitm, est_itm, usein_no, qty_rsv, qty_std)
            else:
                sql = "UPDATE TF_ML set ML_DD='%s 00:00:00.000', qty=qty+%s where ml_no='%s' and prd_no='%s' and itm='%s'" \
                      % (nowtime[0:10], int(qty), ml_no, prd_no, nowitm)
            log.info(sql)
            cursor.execute(sql)
            # log.info("影响行数:[%s]", cursor.rowcount)


            # # 修改制令单表身数据,实发数和未领料量
            # sql = "UPDATE TF_MO set QTY = ISNULL(QTY, 0)+%s  WHERE MO_NO='%s' and prd_no='%s'" % (int(qty), mo_no, prd_no)
            # log.info(sql)
            # cursor.execute(sql)
            # log.info("修改制令单表身数据,影响行数:[%s]", cursor.rowcount)

            sql = "update a set a.qty = b.total from TF_MO a, (select tmp.mo_no, tmp.prd_no, sum(tmp.qty) as total from " \
                  "( select mo_no, prd_no, case when ml_id ='2' then -1*qty  else qty end as qty from TF_ML where mo_no='%s' " \
                  ") tmp group by tmp.mo_no, tmp.prd_no) b where a.mo_no=b.mo_no and a.prd_no=b.prd_no and a.MO_NO='%s' " % (mo_no, mo_no)
            log.info(sql, extra={'ptlsh':public.req_seq})
            cursor.execute(sql)
            log.info("修改制令单表身数据,影响行数:[%s]" % cursor.rowcount, extra={'ptlsh': public.req_seq})
            
            if not newflag: #更新领料单为未审核状态
                sql = "UPDATE MF_ML set MODIFY_DD='%s.000', CHK_MAN='', CLS_DATE= '%s 00:00:00.000' where ml_no='%s'" % (nowtime, nowtime[0:10], ml_no)
                cursor.execute(sql)
                sqlserver_conn.commit()

        sqlserver_conn.commit()
        cursor.close()
        sqlserver_conn.close()

    except Exception as ex:
        log.error("生成数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "生成数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )

        #事务回滚
        sqlserver_conn.rollback()
        sqlserver_conn.close()
        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {}
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

#生产退料单
def material_return( request ):
    log = public.logger
    body = public.req_body

    def SqlServer_Conn():
        sqlserver_conn = None
        try:
            sqlserver_conn = pymssql.connect(server='10.10.1.250', user='sa', password='luyao123KEJI',
                                             database="db_18",
                                             timeout=20, autocommit=False)  # 获取连接  #sqlserver数据库链接句柄
        except Exception as ex:
            log.info(str(ex))

        return sqlserver_conn

    try:
        if isinstance(body, dict):
            body=[body]

        for bodyitm in body:
            mo_no = bodyitm.get('MO_NO')
            # est_itm = bodyitm.get('EST_ITM')
            prd_no = bodyitm.get('PRD_NO')
            qty = bodyitm.get('QTY')

            if not mo_no: #不是工单发料，暂不同步
                log.info("不是工单发料，暂不同步!", extra={'ptlsh':public.req_seq})
                public.respcode, public.respmsg = "000000", "交易成功!"
                public.respinfo = HttpResponse( public.setrespinfo() )
                return public.respinfo

            sqlserver_conn = SqlServer_Conn()
            cursor = sqlserver_conn.cursor()  # 获取光标

            #查询表头是否已经领过料
            sql = "select ML_NO, MRP_NO,ID_NO,PRD_NAME, BAT_NO from MF_ML " \
                  "where MLID='ML' and ML_ID='1' and MO_NO='%s' order by cls_date desc" % mo_no
            log.info(sql)
            cursor.execute(sql)
            row = cursor.fetchone()
            if not row:
                sqlserver_conn.rollback()
                sqlserver_conn.close()
                public.respcode, public.respmsg = "680003", "该工单未发过料!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            mrp_no = row[1]
            id_no = row[2]
            mrp_prd_name = row[3]
            bat_no = row[4]

            # 查询表身是否已经领过料
            sql = "select ML_NO, itm, QTY, PRD_NAME,WH, EST_ITM, USEIN_NO, QTY_STD from TF_ML " \
                  "where MO_NO='%s' and MLID='ML' and ML_ID='1' and PRD_NO='%s'" % (mo_no, prd_no)
            log.info(sql)
            cursor.execute(sql)
            row = cursor.fetchone()
            if not row or not row[0]:  # 没领过料
                sqlserver_conn.rollback()
                sqlserver_conn.close()
                public.respcode, public.respmsg = "680004", "该料未发!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo
            db_qty = int(row[2])
            prd_name = row[3]
            wh = row[4]
            est_itm = row[5]
            usein_no = row[6]
            if row[7]:
                qty_std = row[7]
            else:
                qty_std = 0.00

            # 查询表身是否已经领过料
            sql = "select sum(QTY) from TF_ML " \
                  "where MO_NO='%s' and MLID='ML' and ML_ID='1' and PRD_NO='%s'" % (mo_no, prd_no)
            log.info(sql)
            cursor.execute(sql)
            row = cursor.fetchone()
            db_qty = row[0]
            if db_qty < qty:
                sqlserver_conn.rollback()
                sqlserver_conn.close()
                public.respcode, public.respmsg = "680005", "实际发料数量小于当前退料数量!"
                public.respinfo = HttpResponse(public.setrespinfo())
                return public.respinfo

            nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # 查询表头是否已经退过料, 获取退料单号
            sql = "select ML_NO from MF_ML where ML_DD='%s 00:00:00.000' and ML_NO like 'M2%%M%%' and MO_NO='%s' " \
                  "and MLID='M2' and ML_ID='2' order by cls_date desc" % (nowtime[0:10], mo_no)
            log.info(sql)
            cursor.execute(sql)
            row = cursor.fetchone()
            if not row or not row[0]:  # 重新生成一个退料单号
                newflag = True
                sql = "select max(ML_NO) from MF_ML where ML_NO like 'M2%sM%%' " % datetime.datetime.now().strftime('%y%m')
                log.info(sql)
                cursor.execute(sql)
                row = cursor.fetchone()
                if not row or not row[0]:
                    ml_no = 'M2%sM001' % datetime.datetime.now().strftime('%y%m')
                else:
                    ml_no = 'M2%sM' % datetime.datetime.now().strftime('%y%m') + "%03d" % (int(row[0][-3:]) + 1)
            else:
                newflag = False
                ml_no = row[0]

            if newflag: #新数据，插入退料单一条新记录
                sql = "INSERT INTO MF_ML(MLID,ML_NO,ML_DD,ML_ID, FIX_CST, MO_NO, MRP_NO, UNIT, DEP, USR, " \
                      "CHK_MAN, CLS_DATE, ID_NO, BIL_TYPE, SYS_DATE, FIX_CST1, PRD_NAME, BAT_NO, PRT_SW,TASK_ID ) " \
                      "VALUES('M2', '%s', '%s 00:00:00.000', '2', '1', '%s','%s', '1', 'MT', '011', " \
                      "'', '', '%s', '08', '%s.000', '1', '%s','%s','N','0' )" \
                      % (ml_no, nowtime[0:10], mo_no, mrp_no, id_no, nowtime, mrp_prd_name, bat_no )
                log.info(sql)
                cursor.execute(sql)
            else:
                pass #放在后边更新了，避免锁表

            # 插入或更新退料明细表
            # 查询表身是否已经退过料
            sql = "select itm, QTY from TF_ML where ML_NO='%s' and MLID='M2' and ML_ID='2' and PRD_NO='%s'" % (ml_no, prd_no)
            log.info(sql)
            cursor.execute(sql)
            row = cursor.fetchone()
            if not row or not row[0]:
                itmnewflag = True # 重新生成一条明细
                sql = "select ISNULL(max(ITM),0)+1 from TF_ML where ML_NO='%s' " % (ml_no)
                cursor.execute(sql)
                itmrow = cursor.fetchone()
                nowitm = itmrow[0]
            else:
                itmnewflag = False
                nowitm = row[0]

            nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if itmnewflag:  # 新数据，插入操作
                sql = "INSERT INTO TF_ML(MLID,ML_NO,ITM, ML_DD, ML_ID, PRD_NO, PRD_NAME, MO_NO, UNIT, " \
                      "QTY, WH, PRE_ITM, EST_ITM, FIX_CST1, USEIN_NO,QTY_STD ) " \
                      "VALUES('M2', '%s', '%s','%s 00:00:00.000', '2',  '%s','%s', '%s', '1', " \
                      "%s, '%s', '%s', '%s', '1', '%s', %s )" \
                      % ( ml_no, nowitm, nowtime[0:10], prd_no, prd_name, mo_no,
                          int(qty), wh, nowitm, est_itm, usein_no, qty_std )
            else:
                sql = "UPDATE TF_ML set ML_DD='%s 00:00:00.000', qty=qty+%s  where ml_no='%s' and prd_no='%s'" % (nowtime[0:10], int(qty), ml_no, prd_no)
            log.info(sql)
            cursor.execute(sql)

            # 修改制令单表身数据,实发数和未领料量
            # sql = "UPDATE TF_MO set QTY=QTY-%s WHERE MO_NO='%s' and prd_no='%s'" % (int(qty), mo_no, prd_no)
            sql = "update a set a.qty = b.total from TF_MO a, (select tmp.mo_no, tmp.prd_no, sum(tmp.qty) as total from " \
                  "( select mo_no, prd_no, case when ml_id ='2' then -1*qty  else qty end as qty from TF_ML where mo_no='%s' " \
                  ") tmp group by tmp.mo_no, tmp.prd_no) b where a.mo_no=b.mo_no and a.prd_no=b.prd_no and a.MO_NO='%s' " % (mo_no, mo_no)
            log.info(sql, extra={'ptlsh':public.req_seq})
            cursor.execute(sql)
            log.info("修改制令单表身数据,影响行数:[%s]" % cursor.rowcount, extra={'ptlsh':public.req_seq})

            if not newflag:  # 更新领料单为未审核状态
                sql = "UPDATE MF_ML set MODIFY_DD='%s.000', CHK_MAN='', CLS_DATE= '%s 00:00:00.000' where ml_no='%s'" % (
                nowtime, nowtime[0:10], ml_no)
                cursor.execute(sql)

        sqlserver_conn.commit()
        cursor.close()
        sqlserver_conn.close()

    except Exception as ex:
        log.error("生成数据失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300010", "生成数据失败!"+str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        #事务回滚
        sqlserver_conn.rollback()
        sqlserver_conn.close()

        return public.respinfo

    public.respcode, public.respmsg = "000000", "交易成功!"
    json_data = {
        "HEAD": public.resphead_setvalue(),
        "BODY": {}
    }
    s = json.dumps(json_data, cls=public.JsonCustomEncoder, ensure_ascii=False)
    public.respinfo = HttpResponse(s)
    return public.respinfo

