from django.db import connection
import datetime
from admin_app import public
from admin_app.sys import public as pb
###########################################################################################################
# 数据库公共操作流程
# add by litz, 20200509
#
###########################################################################################################

# 根据用户ID获取用户名称
def get_username(userid):
    # 根据user_id获取user_name
    sql = "select user_name from sys_user where user_id=%s"
    cur = connection.cursor()  # 创建游标
    cur.execute(sql, userid)
    row = cur.fetchone()
    cur.close()
    if row:
        return row[0]
    else:
        return ''


# 根据用户ID获取所属部门
def get_department(userid):
    # 根据user_id获取user_name
    sql = "SELECT so.ORG_SPELL from sys_user_org uo,sys_org so where uo.ORG_ID =  so.ORG_ID and  user_id = %s"
    cur = connection.cursor()  # 创建游标
    cur.execute(sql, userid)
    row = cur.fetchone()
    cur.close()
    if row:
        return row[0]
    else:
        return ''


# 根据用户ID获取所属公司
def get_company(userid):
    # 根据user_id获取user_name
    sql = """SELECT com.ORG_SPELL from (SELECT org_id,ABOVE_ORG_ID,ORG_SPELL from sys_org where ORG_TYPE='company') com,
            (SELECT org_id,ABOVE_ORG_ID,ORG_SPELL from sys_org where ORG_TYPE='depart') dep,
            sys_user_org uo where dep.ABOVE_ORG_ID = com.org_id and uo.org_id = dep.org_id 
            and uo.user_id = %s"""
    cur = connection.cursor()  # 创建游标
    cur.execute(sql, userid)
    row = cur.fetchone()
    cur.close()
    if row:
        return row[0]
    else:
        return ''


# 根据配置获取序列号
def Get_SeqNo(seqname):
    cur = connection.cursor()  # 创建游标

    sql = "select current_val, curval_len, expression from sys_sequence where seq_name=%s for update"
    cur.execute(sql, seqname)
    row = cur.fetchone()

    if not row:
        connection.commit()
        cur.close()
        return None

    curval = row[0]
    curvallen = row[1]
    express = row[2]
    sql = "update sys_sequence set current_val = current_val + increment_val where seq_name = %s"
    cur.execute(sql, seqname)
    cur.close()

    ret = express
    if '[YYYY]' in ret:
        ret = ret.replace('[YYYY]', datetime.datetime.now().strftime('%Y'))
    if '[YYYYMM]' in ret:
        ret = ret.replace('[YYYYMM]', datetime.datetime.now().strftime('%Y%m'))
    if '[YYYYMMDD]' in ret:
        ret = ret.replace('[YYYYMMDD]', datetime.datetime.now().strftime('%Y%m%d'))
    if '[yy.mm]' in ret:
        ret = ret.replace('[yy.mm]', datetime.datetime.now().strftime('%y.%m'))
    if '[yymm]' in ret:
        ret = ret.replace('[yymm]', datetime.datetime.now().strftime('%y%m'))
    if '[COM]' in ret:
        ret = ret.replace('[COM]', get_company(pb.user_id))
    if '[DEP]' in ret:
        ret = ret.replace('[DEP]', get_department(pb.user_id))
    if '[SEQNO]' in ret:
        strcurval = str(curval)
        if curvallen:
            strcurval = strcurval.rjust(curvallen, '0')
        ret = ret.replace('[SEQNO]', strcurval)
    return ret


# 根据连接和sql语句,获取查询结果放在list结构体中 key:sql中的字段名, value：对应查询结果。
def GetSelData(cur, sql, param=None):
    # cur = connection.cursor()  # 创建游标
    if param:
        cur.execute(sql, param)
    else:
        cur.execute(sql)
    rows = cur.fetchall()
    col_result = cur.description  # 获取sql语句的字段描述
    result = []
    for item in rows:
        dateitem = {}
        for i in range(len(col_result)):
            dateitem[col_result[i][0]] = item[i]  # 获取字段名，以数据字典的形式保存数据
        result.append(dateitem)
    return result


def insert_or_update_table(cur, tablename, **param):
    """根据表名更新或插入数据"""
    log = public.logger
    log.info("================= INSERT_OR_UPDATE_TABLE START =================")
    if not tablename:
        return None, '表名不能为空'
    try:
        # cur = connection.cursor()
        # 根据表名查询字段和数据类型
        sql = "SELECT COLUMN_NAME,data_type FROM INFORMATION_SCHEMA.Columns WHERE table_name= %s AND " \
              "table_schema= %s "
        sql_value = (tablename, 'lqkj_db')
        cur.execute(sql, sql_value)
        rows = cur.fetchall()
        if not rows:
            return None, '表名不正确'
        columns = map(lambda x: x[0], rows)
        column_dct = [{'column_name': cn, 'data_type': dd} for cn, dd in rows]
        if isinstance(param, dict):
            rp = set(param.keys()) & set(columns)
            # 过滤数据
            temp_var = {k: (v if v else '') for k, v in param.items()}
            # 根据id判断更新还是插入
            if 'id' in rp and param.get('id'):
                rp.remove('id')
                sql = "select 1 from %s where id = %d" % (tablename, param.get('id'))
                cur.execute(sql)
                row = cur.fetchone()
                if row:
                    # update
                    sql = "update " + tablename + " set "
                    for k in rp:
                        sql += "%s='%s'," % (k, str(temp_var.get(k)))
                    sql = sql[:-1]
                    sql += " where id=%d" % param.get('id')
                else:
                    # insert
                    sql = "insert into " + tablename
                    sql += ' ' + str(tuple(rp))
                    sql = sql.replace("'", '')
                    sql += ' values ' + str(tuple(map(lambda x: temp_var.get(x), list(rp))))
            else:
                # insert
                rp.remove('id')
                sql = "insert into " + tablename
                sql += ' ' + str(tuple(rp))
                sql = sql.replace("'", '')
                sql += ' values ' + str(tuple(map(lambda x: temp_var.get(x), list(rp))))
        else:
            return None, '传入数据体格式有误'
        # excute
        log.info("SQL: " + sql)
        return cur.execute(sql), 'OK'
    except Exception as ex:
        log.info(ex.__str__())
        return None, ex.__str__()
    finally:
        log.info("================= INSERT_OR_UPDATE_TABLE END=================")
