import hashlib

import requests
from django.shortcuts import render, redirect, HttpResponse
from django.db import connection, transaction
from django.forms.models import model_to_dict
import json
from admin_app import public
from admin_app import models
from admin_app import texcfg
import datetime
import time


# 获取短信验证码
def GetMsgCode(request):
    log = public.logger
    log.info('----------------------Admin-GetMsgCode-begin---------------------------')

    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)

    qttime = reqest_body['time']
    qtip = request.META['REMOTE_ADDR']

    mobile = reqest_body['phone_number']

    outtime = datetime.datetime.now()
    outtime = outtime - datetime.timedelta(minutes=10)  # 获取十分钟之前的时间
    # log.info('获取十分钟之前的时间:'+outtime.strftime('%b %d %Y %H:%M:%S') )

    cur = connection.cursor()
    try:
        sql = "select count(1) from irs_server_mobilemessage where mobile='%s' and trandatetime>='%s' and msgstate='1'" \
              % (mobile, outtime.strftime('%b %d %Y %H:%M:%S'))
        cur.execute(sql)
        row = cur.fetchone()
        if row and row[0] >= 6:
            s = public.setrespinfo({"respcode": "220011", "respmsg": "操作过于频繁，请稍后再试!"})
            return HttpResponse(s)
    except Exception as e:
        s = public.setrespinfo({"respcode": "220011", "respmsg": "数据库错误:" + str(e)})
        return HttpResponse(s)

    checkcode = public.getintrandom(6)
    messageinfo = '爱如生科技-商户后台管理系统登陆验证码:' + checkcode + ',有效时间三分钟!'

    try:
        sql = "insert into irs_server_mobilemessage(trandatetime,trantype,qtdatetime,qtip,mobile,checkcode,msginfo,msgstate) " \
              "values('%s','%s','%s','%s','%s','%s','%s','%s')" \
              % (
              datetime.datetime.now().strftime('%b %d %Y %H:%M:%S'), 'getmessagecode', qttime, qtip, mobile, checkcode,
              messageinfo, '1')
        cur.execute(sql)
    except Exception as e:
        s = public.setrespinfo({"respcode": "220011", "respmsg": "数据库错误:" + str(e)})
        return HttpResponse(s)

    info_json = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": "getmessagecode",
        # "messagecode": messagecode
    }

    s = json.dumps(info_json, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-GetMsgCode-end---------------------------')
    return HttpResponse(s)


# 退出登陆
def UserLoginOut(request):
    log = public.logger
    log.info('----------------------Admin-UserLoginOut-begin---------------------------')

    del request.session["uid"]  # 删除session
    del request.session["checksum"]  # 删除session

    info_json = {
        "respcode": "000000",
        "respmsg": "交易成功"
    }

    s = json.dumps(info_json, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-UserLoginOut-end---------------------------')
    return HttpResponse(s)


# 获取微信登陆二维码
def GetQRCode(request):
    log = public.logger
    log.info('----------------------Admin-GetQRCode-begin---------------------------')

    url = 'https://open.weixin.qq.com/connect/qrconnect?appid=wx755f9eeb4022a481&redirect_uri=https%3A%2F%2Fwww.irusheng.com%2FAdminLogin&response_type=code&scope=snsapi_login&state=3d6be0a4035d839573b04816624a415e#wechat_redirect'
    info_json = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": "getQRcode",
        "url": url
    }

    s = json.dumps(info_json, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info(s)
    log.info('----------------------Admin-GetQRCode-end---------------------------')
    return HttpResponse(s)


# 用户手机短信登陆
def UserLogin(request):
    log = public.logger
    log.info('----------------------Admin-UserLogin-begin---------------------------')

    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)

    qttime = reqest_body.get('time', None)
    qtip = request.META['REMOTE_ADDR']
    mobile = reqest_body.get('phone_number', None)
    checkcode = reqest_body.get('code', None)

    testcode = '112233'
    m = hashlib.md5()
    m.update(testcode.encode('utf-8'))
    checksum = m.hexdigest()
    log.info('checksum=' + checksum)
    if checkcode == checksum:
        # 模拟测试成功
        pass
    else:
        if checkcode == None or checkcode == '':
            s = public.setrespinfo({"respcode": "220020", "respmsg": "验证码不可为空"})
            return HttpResponse(s)

        if mobile == None or mobile == '':
            s = public.setrespinfo({"respcode": "220020", "respmsg": "手机号码不可为空"})
            return HttpResponse(s)

        outtime = datetime.datetime.now()
        outtime = outtime - datetime.timedelta(minutes=3)  # 获取三分钟之前的时间
        outtime = outtime.strftime('%b %d %Y %H:%M:%S')
        # log.info('获取三分钟之前的时间:'+ outtime )

        cur = connection.cursor()
        try:
            sql = "select count(1) from irs_server_mobilemessage where mobile='%s' and trandatetime>='%s' and msgstate='1'" \
                  % (mobile, outtime)
            cur.execute(sql)
            row = cur.fetchone()
            if row and row[0] >= 6:
                s = public.setrespinfo({"respcode": "220011", "respmsg": "操作过于频繁，请稍后再试!"})
                return HttpResponse(s)
        except Exception as e:
            s = public.setrespinfo({"respcode": "220011", "respmsg": "数据库错误:" + str(e)})
            return HttpResponse(s)

        try:
            mobilemsgTable = models.IrsServerMobilemessage.objects.filter(mobile=mobile, trandatetime__gte=outtime,
                                                                          msgstate='1')
        except models.IrsServerMobilemessage.DoesNotExist:
            mobilemsgTable = None
            s = public.setrespinfo({"respcode": "220021", "respmsg": "验证码错误或已过期"})
            return HttpResponse(s)
        if mobilemsgTable.count() == 0:
            s = public.setrespinfo({"respcode": "220021", "respmsg": "验证码错误或已过期"})
            return HttpResponse(s)

        try:
            mobilemsgTable = models.IrsServerMobilemessage.objects.filter(mobile=mobile, trandatetime__gte=outtime,
                                                                          msgstate='1', checkcode=checkcode)
        except models.IrsServerMobilemessage.DoesNotExist:
            mobilemsgTable = None
            s = public.setrespinfo({"respcode": "220022", "respmsg": "验证码错误"})
            return HttpResponse(s)
        if mobilemsgTable.count() == 0:
            s = public.setrespinfo({"respcode": "220022", "respmsg": "验证码错误"})
            return HttpResponse(s)

        mobilemsgTable.update(msgstate='2')

    # 查找管理台用户信息表权限
    try:
        AdminUser = models.IrsadminUser.objects.get(tel=mobile)
    except models.IrsadminUser.DoesNotExist:  # 新用户，直接赋值vip0角色，插入用户表一条记录
        AdminUser = models.IrsadminUser(
            user_id=mobile,
            org_id='mobile01',
            station='新短信登陆用户',
            status='1',
            tel=mobile,
            create_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        AdminUser.save()
        log.info("插入IrsadminUser表成功:[%s]" % mobile)
        AdminUserRole = models.IrsadminUserRule(
            user_id=mobile,
            role_id='vip0',  # 角色ID
        )
        AdminUserRole.save()
        log.info("插入AdminUserRole表成功:[%s]" % mobile)

    if AdminUser.uid == None:
        AdminUser.uid = AdminUser.user_id

    # session赋值
    request.session['uid'] = AdminUser.uid
    request.session['user_id'] = AdminUser.user_id
    request.session['checksum'] = checkcode
    request.session['logintype'] = 'msgcode'  # password-密码, qrcode-二维码,msgcode-短信

    # 跳转到登陆成功后的管理台页面
    newurl = 'https://admin.irusheng.com?uid=' + str(request.session['uid']) + '&checksum=' + str(
        request.session['checksum'])
    log.info('跳转到登陆成功后的管理台页面  ' + newurl)
    info_json = {
        "respcode": "000000",
        "respmsg": "登陆成功",
        "trantype": "login",
        "url": newurl
    }

    s = json.dumps(info_json, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info('----------------------Admin-UserLogin-end---------------------------')
    return HttpResponse(s)


# 使用用户名密码登陆
def LoginByPass(request):
    log = public.logger
    log.info('----------------------Admin-LoginByPass-begin---------------------------')

    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)

    qttime = reqest_body.get('time', None)
    qtip = request.META['REMOTE_ADDR']
    userid = reqest_body.get('userid', None)
    password = reqest_body.get('password', None)

    # 查找管理台用户信息表权限
    try:
        AdminUser = models.IrsadminUser.objects.get(user_id=userid, passwd=password)
    except models.IrsadminUser.DoesNotExist:  # 新用户，直接赋值vip0角色，插入用户表一条记录
        # 找不到时，有可能使用手机号登陆的
        try:
            AdminUser = models.IrsadminUser.objects.get(tel=userid, passwd=password)
        except models.IrsadminUser.DoesNotExist:  # 新用户，直接赋值vip0角色，插入用户表一条记录
            s = public.setrespinfo({"respcode": "220025", "respmsg": "用户名或必码错误!"})
            return HttpResponse(s)

    # if AdminUser.uid==None:
    AdminUser.uid = AdminUser.user_id

    checkstr = str(AdminUser.user_id) + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    m = hashlib.md5()
    m.update(checkstr.encode('utf-8'))
    checksum = m.hexdigest()
    log.info('checksum=' + checksum)

    # session赋值
    request.session['uid'] = AdminUser.uid
    request.session['user_id'] = AdminUser.user_id
    request.session['checksum'] = checksum
    request.session['logintype'] = 'password'  # password-密码, qrcode-二维码,msgcode-短信

    # 跳转到登陆成功后的管理台页面
    log.info('REMOTE_ADDR=' + request.META['REMOTE_ADDR'])
    referer = request.META['HTTP_REFERER']
    # if request.META['REMOTE_ADDR'] in public.DevIpList:
    # public.localurl='http://admin.zeyidawulian.com/'
    # public.localurl='http://localhost:8080/'

    for item in request.META:
        print('登陆信息：', item, request.META[item])

    if referer == 'http://localhost:8080/':
        newurl = referer + '?uid=' + str(request.session['uid']) + '&checksum=' + str(
            request.session['checksum'])
    else:
        # newurl = public.localurl + '?uid=' + str(request.session['uid']) + '&checksum=' + str( request.session['checksum'])
        newurl = request.META['HTTP_ORIGIN'] + '?uid=' + str(request.session['uid']) + '&checksum=' + str(
            request.session['checksum'])

    log.info('跳转到登陆成功后的管理台页面  ' + newurl)
    info_json = {
        "respcode": "000000",
        "respmsg": "登陆成功",
        "trantype": reqest_body.get('trantype', None),
        "url": newurl
    }

    s = json.dumps(info_json, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info('----------------------Admin-LoginByPass-end---------------------------')
    return HttpResponse(s)


# 修改用户登陆密码
def modifypass(request):
    log = public.logger
    log.info('----------------------Admin-modifypass-begin---------------------------')

    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)

    qttime = reqest_body.get('time', None)
    qtip = request.META['REMOTE_ADDR']
    userid = request.session.get('user_id', None)
    oldpassword = reqest_body.get('oldpassword', None)
    newpassword = reqest_body.get('newpassword', None)

    print('userid=', userid, ',oldpassword=', oldpassword)
    # 查找管理台用户信息表权限
    try:
        AdminUser = models.IrsadminUser.objects.get(user_id=userid, passwd=oldpassword)
    except models.IrsadminUser.DoesNotExist:
        s = public.setrespinfo({"respcode": "220025", "respmsg": "用户不存在!"})
        return HttpResponse(s)

    models.IrsadminUser.objects.filter(user_id=userid, passwd=oldpassword).update(
        old_passwd=oldpassword,
        passwd=newpassword
    )

    info_json = {
        "respcode": "000000",
        "respmsg": "交易成功",
        "trantype": reqest_body.get('trantype', None),
    }

    s = json.dumps(info_json, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info('----------------------Admin-modifypass-end---------------------------')
    return HttpResponse(s)


# 用户扫码登陆
def UserLogin_Qrcode(request):
    log = public.logger
    log.info('----------------------Admin-UserLogin_Qrcode-begin---------------------------')

    # 获取code,根据code得到openid
    code = request.GET.get('code', None)  # 微信授权返回的code

    # 根据code得到unionid
    # 获取微信开放平台的appid和appsecret
    appid = 'wx755f9eeb4022a481'
    appsecret = '34d726c0473859fed4239ecc7491c33d'
    appid = '11111'
    url = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid=' + appid + '&secret=' + appsecret
    url = url + '&code=' + code + '&grant_type=authorization_code'
    log.info(url)
    conn = requests.post(url)
    jsondata = json.loads(conn.text)
    log.info("根据code获取openid:[%s]" % jsondata)
    try:
        openid = jsondata['openid']
        unionid = jsondata['unionid']
        access_token = jsondata['access_token']
        # 更加openid异步获取用户信息 插入或更新到CONSUMER表里
        # pass
    except:
        log.info("已过期:[%s]" % jsondata)
        return HttpResponse('wxcode已过期，请重新使用微信客户端登陆!')

    # 根据unionid获取用户信息
    log.info('unionid=' + unionid + ',public.appname=' + public.appname)
    try:
        CustomerInfo = models.IrsServerConsumer.objects.get(union_id=unionid, wx_gzh=public.appname)
    except models.IrsServerConsumer.DoesNotExist:
        CustomerInfo = None
        info_json = {
            "respcode": "658821",
            "respmsg": "请先关注微信公众号[" + public.appnamedesc + "]!",
        }
        s = json.dumps(info_json, cls=models.JsonCustomEncoder, ensure_ascii=False)
        return HttpResponse(s)

    TokenModel = models.IrsServerToken.objects.get(app_name=public.appname)
    access_token = TokenModel.access_token
    url = 'https://api.weixin.qq.com/cgi-bin/user/info?access_token=' + access_token + '&openid=' + CustomerInfo.wx_open_id + '&lang=zh_CN'
    log.info(url)
    try:
        conn = requests.post(url)
        # 推送返回数据
        recvdata = conn.text
    except Exception:
        log.error("消息发送失败", exc_info=True)
    log.info(recvdata)
    jsondata = json.loads(recvdata)

    # 必须关注公众号
    if str(jsondata.get('subscribe', '0')) == '1':
        log.info('已关注微信公众号')
        models.IrsServerConsumer.objects.filter(id=CustomerInfo.id).update(
            head_imgurl=jsondata['headimgurl'],
            union_id=jsondata['unionid'],
            nick_name=jsondata['nickname'],
            user_sex=jsondata['sex'],
            user_address=jsondata['city'],
        )
    # else:
    #     info_json = {
    #         "respcode": "658821",
    #         "respmsg": "请先关注微信公众号[" + public.appnamedesc + "]!",
    #     }
    #     s = json.dumps(info_json, cls=models.JsonCustomEncoder, ensure_ascii=False)
    #     return HttpResponse(s)

    uid = CustomerInfo.id
    log.info("根据union_id获取uid:[%s]" % uid)

    # 查找管理台用户信息表权限
    try:
        AdminUser = models.IrsadminUser.objects.get(uid=uid)
    except models.IrsadminUser.DoesNotExist:  # 新用户，直接赋值vip0角色，插入用户表一条记录
        AdminUser = models.IrsadminUser(
            user_id=uid,
            user_name=jsondata['nickname'],
            org_id='wx0000',
            station='新扫码登陆用户',
            sex=jsondata['sex'],
            address=jsondata['city'],
            status='1',
            uid=uid,
            create_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        AdminUser.save()
        log.info("插入IrsadminUser表成功:[%s]" % uid)
        AdminUserRole = models.IrsadminUserRule(
            user_id=uid,
            role_id='vip0',  # 角色ID
        )
        AdminUserRole.save()
        log.info("插入AdminUserRole表成功:[%s]" % uid)

    # 根据code生成checksum
    m = hashlib.md5()
    m.update(code.encode('utf-8'))
    checksum = m.hexdigest()

    # session赋值，便于以后验证
    request.session['uid'] = uid
    request.session['user_id'] = AdminUser.user_id
    request.session['checksum'] = checksum
    request.session['logintype'] = 'qrcode'  # password-密码, qrcode-二维码,msgcode-短信

    newurl = 'https://admin.irusheng.com?uid=' + str(uid) + '&checksum=' + str(checksum)
    log.info("新url:[%s]" % newurl)
    log.info('----------------------Admin-UserLogin_Qrcode-end---------------------------')
    return redirect(newurl)


# 跳转登陆后获取用户名称、头像、登陆方式等信息
def GetUserInfo(request):
    log = public.logger
    log.info('----------------------Admin-GetUserInfo-begin---------------------------')

    tmp = request.body
    tmp = tmp.decode(encoding='utf-8')
    reqest_body = json.loads(tmp)

    qttime = reqest_body.get('time', None)
    qtip = request.META['REMOTE_ADDR']
    userid = request.session.get('user_id', None)
    time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 查找管理台用户信息表权限
    cur = connection.cursor()
    sql = "select user_name,uid,head_imgurl,status from irsadmin_user where user_id='%s'" % (userid)
    cur.execute(sql)
    row = cur.fetchone()
    if row:
        username = row[0]
        uid = row[1]
        headimgurl = row[2]
    else:
        log.info("查询用户信息:" + sql)
        s = public.setrespinfo({"respcode": "220125", "respmsg": "查询用户信息失败!"})
        return HttpResponse(s)

    # if uid==None or len(uid)==0:
    #     uid=userid

    if headimgurl == None or len(headimgurl) < 5:
        headimgurl = request.META['HTTP_ORIGIN'] + '/' + 'static/images/headdefimg.gif'  # 默认头像

    info_json = {
        "respcode": "000000",
        "respmsg": "登陆成功",
        "trantype": reqest_body.get('trantype', None),
        "logintype": request.session.get('logintype', 'password'),  # password-密码, qrcode-二维码,msgcode-短信
        "userid": userid,
        "username": username,
        "headimgurl": headimgurl,
    }

    s = json.dumps(info_json, cls=models.JsonCustomEncoder, ensure_ascii=False)
    log.info('----------------------Admin-GetUserInfo-end---------------------------')
    return HttpResponse(s)
