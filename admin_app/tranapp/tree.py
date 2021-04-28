import sys
from django.db import connection
from admin_app.sys import public
from admin_app.sys import public_db
from django.shortcuts import HttpResponse

###########################################################################################################
#树结构数据处理函数
#add by litz, 2020.05.14
#
###########################################################################################################


#获取机构列表-配置时使用
def get_org_list( request ):
    log = public.logger
    body = public.req_body
    # 获取菜单角色列表,--菜单配置时使用
    def GetCfgOrgTreeData( above_org_id ):
        log = public.logger
        OrgTreeData = []

        sql = "select org_id, org_name from sys_org where above_org_id='%s' and org_state='1' "  % ( above_org_id )
        # log.info("获取机构信息列表:" + sql, extra={'ptlsh': public.req_seq})
        cur.execute(sql)
        rows = cur.fetchall()
        for item in rows:
            orginfo = {}
            org_id = str(item[0])
            orginfo['id'] = org_id
            orginfo['label'] = item[1]

            tempchild = GetCfgOrgTreeData(org_id)
            if len(tempchild) > 0:
                orginfo['children'] = tempchild

            OrgTreeData.append(orginfo)

        # log.info("OrgTreeData" + str(OrgTreeData))
        # 返回结果
        return OrgTreeData

    try:
        cur = connection.cursor()
        orglist = GetCfgOrgTreeData( 'root' )
        orgselect=[]
        form_data=body.get('form_data')
        if form_data:
            userid = form_data.get('user_id')
        else:
            userid = ''
        #获取用户已经拥有的机构
        sql=" select org_id from sys_user_org where user_id='%s' " % userid
        log.info(sql)
        cur.execute(sql)
        rows=cur.fetchall()
        for item in rows:
            orgselect.append(item[0])
        cur.close()

    except Exception as ex:
        log.error("交易失败!"+str(ex), exc_info=True, extra={'ptlsh':public.req_seq})
        public.exc_type, public.exc_value, public.exc_traceback = sys.exc_info()
        public.respcode, public.respmsg = "300200", "交易失败!" + str(ex)
        public.respinfo = HttpResponse( public.setrespinfo() )
        return '' ''

    return orglist, orgselect

