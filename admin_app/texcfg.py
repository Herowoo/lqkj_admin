
from admin_app import models


#特殊处理部分,用户管理，角色管理
def getrolepurv(data, reqest_body):

    try:
        roleid=reqest_body['data'].get('ROLE_ID',None)
    except:
        roleid=None
    # print('roleid=',roleid)
    # if not roleid:
    #     s = public.setrespinfo({"respcode": "310013", "respmsg": "角色编号必输!"})
    #     return HttpResponse(s)

    rightdata=[]
    try:
        RoleProvTable=models.IrsadminRolePurv.objects.filter(role_id=roleid)
    except models.IrsadminRolePurv.DoesNotExist:
        RoleProvTable=None

    for item in RoleProvTable:
        rightdata.append(item.menu_id)
    # print('rightdata=',rightdata)
    data['left_title'] = '未分配功能菜单'
    data['right_title'] = '已分配功能菜单'
    menuTable = models.IrsadminMenu.objects.filter(is_run_menu='Y')
    for item in menuTable:
        if str(item.menu_id) in rightdata:
            # print('找到数据:', item.menu_id)
            data['left_data'].append({"key": item.menu_id, "label": item.menu_name})
            data['right_data'].append(item.menu_id)
        else:
            data['left_data'].append({"key":item.menu_id,"label":item.menu_name})

    return data

#获取用户角色的穿梭框
def getuserrole(data, reqest_body):

    try:
        userid=reqest_body['data'].get('USER_ID',None)
    except:
        userid=None
    # print('userid=',userid)
    # if not userid:
    #     s = public.setrespinfo({"respcode": "310014", "respmsg": "用户编号必输!"})
    #     return HttpResponse(s)

    rightdata=[]
    try:
        UserRoleTable=models.IrsadminUserRule.objects.filter(user_id=userid)
    except models.IrsadminUserRule.DoesNotExist:
        UserRoleTable=None

    for item in UserRoleTable:
        rightdata.append(item.role_id)
    # print('rightdata=',rightdata)
    data['left_title'] = '未分配用户角色'
    data['right_title'] = '已分配用户角色'
    RoleTable = models.IrsadminRole.objects.all()
    for item in RoleTable:
        if str(item.role_id) in rightdata:
            # print('找到数据:', item.menu_id)
            data['left_data'].append({"key": item.role_id, "label": item.role_name})
            data['right_data'].append(item.role_id)
        else:
            data['left_data'].append({"key":item.role_id,"label":item.role_name})

    return data

#获取用户所属社区机构的穿梭框
def getuserorg(data, reqest_body):

    try:
        userid=reqest_body['data'].get('USER_ID',None)
    except:
        userid=None

    rightdata=[]
    try:
        UserRoleTable=models.IrsadminUserRule.objects.filter(user_id=userid)
    except models.IrsadminUserRule.DoesNotExist:
        UserRoleTable=None

    for item in UserRoleTable:
        rightdata.append(item.role_id)
    # print('rightdata=',rightdata)
    data['left_title'] = '未分配社区'
    data['right_title'] = '已分配社区'
    RoleTable = models.IrsadminRole.objects.all()
    for item in RoleTable:
        if str(item.role_id) in rightdata:
            # print('找到数据:', item.menu_id)
            data['left_data'].append({"key": item.role_id, "label": item.role_name})
            data['right_data'].append(item.role_id)
        else:
            data['left_data'].append({"key":item.role_id,"label":item.role_name})

    return data
