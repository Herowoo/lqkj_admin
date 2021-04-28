from django.shortcuts import render,redirect,HttpResponse
from django.db import connection, transaction
import json
from admin_app import public
import datetime
from admin_app import menucfg
from admin_app import crudcfg
from admin_app import tablecfg
from admin_app import userrole
from admin_app import useract
from admin_app import filecfg
from admin_app import buttontran
from admin_app import lqkjsmpd
from admin_app import lqkjoa
from admin_app import lqkjmes
from admin_app import lqkjerp
from admin_app import lqkjbill
from admin_app import lqkjsetform
from admin_app import lqkjprod
from admin_app import fileup
from admin_app import form_config
from admin_app import lqkjmarket
from admin_app import lqkjbuy
from admin_app import lqkjrece
import os

# Create your views here.
def admin(request):
    try:
        starttime=datetime.datetime.now()
        #获取访问路径
        if request.path[-1] == '/':
            param1 = request.path.rsplit('/')[-2]
        else:
            param1 = request.path.rsplit('/')[-1]
        logmsg = 'param1=[' + param1 + ']'
        #初始化日志
        global log
        if param1:
            log, fh = public.loger_init(param1)
        else:
            log, fh=public.loger_init('Admin')
        #print('public.logger.handlers',public.logger.handlers)
        log.info('----------------------Admin-begin---------------------------')
        log.info("请求:[%s]" % request)
        log.info("请求path:[%s]" % request.path)
        log.info("请求method:[%s]"  %  request.method)
        log.info("请求GET:[%s]"  %  request.GET)

        global  location_href
        location_href='https://localhost:8000'+request.get_full_path()
        log.info("请求full_path:[%s]" % location_href )

        global respinfo
        respinfo = None

        if param1 not in ['useraction', 'filedue']: #上传文件的日志太大了，不再记录
            log.info("请求body:[%s]"  % request.body)
            log.info("请求POST:[%s]" % request.POST)

        #校验session
        if param1 not in ['useraction','buttontran','filedue', 'made']:
            #sesession校验
            if public.checksession(request) == False:
                s = public.setrespinfo({"respcode": "100001", "respmsg": "请重新登陆"})
                respinfo = HttpResponse(s)
                return respinfo

        #记录交易处理开始的时间点
        mysavepoint = transaction.savepoint()
        if  param1=='crudcfg':
            #管理台配置接口
            respinfo=admin_crudcfg(request)
            return respinfo
        elif  param1=='getdata':
            #管理台数据查询接口
            respinfo=admin_tabledata(request)
            return respinfo
        elif param1 == 'filedue':
            # 管理台文件处理接口
            respinfo = filecfg.admin(request)
            return respinfo
        elif param1 == 'useraction':
            # 管理台用户登陆退出等接口
            log.info("请求body:[%s]" % request.body)
            respinfo = admin_useraction(request, log)
            return respinfo
        elif param1 == 'buttontran':
            # 管理台用户登陆退出等接口
            respinfo = buttontran.tran_main(request)
            return respinfo
        elif param1 == 'lqkjsmpd':
            # 工装扫码配对模块接口
            respinfo = lqkjsmpd.main(request)
            return respinfo
        elif param1 == 'lqkjoa':
            # 联桥科技oa接口
            respinfo = lqkjoa.main(request)
            return respinfo
        elif param1 == 'lqkjmes':
            # 联桥科技oa接口
            respinfo = lqkjmes.main(request)
            return respinfo
        elif param1 == 'lqkjerp':
            # 联桥科技erp数据接口
            respinfo = lqkjerp.main(request)
            return respinfo
        elif param1 == 'lqkjbill':
            # 联桥科技评审单接口
            respinfo = lqkjbill.main(request)
            return respinfo
        elif param1 == 'lqkjsetform':
            # 联桥科技评审单接口
            respinfo = lqkjsetform.main(request)
            return respinfo
        elif param1 == 'made':
            # 联桥科技，产测、抄表等工装数据上传。
            respinfo = lqkjprod.main(request)
            return respinfo
        elif param1 == 'fileup':
            # 联桥科技，产测、抄表等工装数据上传。
            respinfo = fileup.main(request)
            return respinfo
        elif param1 == 'form_config':
            # 表单配置接口
            respinfo = form_config.main(request)
            return respinfo
        elif param1 == 'lqkjmarket':
            # 表单配置接口
            respinfo = lqkjmarket.main(request)
            return respinfo
        elif param1 == 'lqkjbuy':
            # 表单配置接口
            respinfo = lqkjbuy.main(request)
            return respinfo
        elif param1 == 'lqkjrece':
            # 销售票据录入接口
            respinfo = lqkjrece.main(request)
            return respinfo
        else:
            print('返回主页')
            respinfo=render(request, 'index.html')
            return respinfo
    except Exception as e :
        log.error('程序运行错误', exc_info = True)
        try:
            transaction.savepoint_rollback(mysavepoint)
        except:
            pass

        s = public.setrespinfo({"respcode": "999999", "respmsg": "系统错误:"+str(e)})
        respinfo=HttpResponse(s)
        # log.info(respinfo.getvalue().decode(encoding='utf-8'))
        # log.info('----------------------Admin-end---------------------------')
        # if fh:
        #     fh.close()
        #     log.removeHandler(fh)
        # return respinfo
    finally:
        #print(respinfo)
        try:
            transaction.savepoint_rollback(mysavepoint)
        except:
            pass
        if not respinfo: #如果返回信息为空
            s = public.setrespinfo({"respcode": "999999", "respmsg": "系统错误[返回数据异常]"})
            respinfo=HttpResponse(s)
    
        try:
            if len(str(respinfo)) < 1024:
                log.info(respinfo)
                log.info(respinfo.getvalue().decode(encoding='utf-8'))
        except:
            pass
        log.info('----------------------Admin-end---------------------------')
        log.info('交易处理时间: %s' %  str(datetime.datetime.now()-starttime) )
        if fh:
            fh.close()
            log.removeHandler(fh)
        return respinfo

def admin_crudcfg(request):
    if request.method == "POST":
        #请求body转为json
        tmp=request.body
        tmp=tmp.decode(encoding='utf-8')
        reqest_body=json.loads(tmp)

        trantype=reqest_body['trantype']
        # print('-'*20,trantype,'-'*20)
        log.info('trantype=[%s]' % trantype)
        if trantype == 'gettablename':  #获取数据库表名列表
            resp = crudcfg.GetTableList(request)
        elif trantype == 'gettablefield':  #获取表字段信息
            resp = crudcfg.GetTableInfo(request)
        elif trantype == 'addcrud': #新增增删改查配置
            resp = crudcfg.AddCrud(request)
        elif trantype == 'addmenu': #新增菜单
            resp = menucfg.AddMenu(request)
        elif trantype == 'updmenu': #更新菜单
            resp = menucfg.UpdMenu(request)
        elif trantype == 'delmenu': #删除菜单
            resp = menucfg.DelMenu(request)
        elif trantype == 'getmenulist': #获取菜单列表,用户登陆成功后获取所拥有权限的菜单
            resp = menucfg.GetMenuList(request)
        elif trantype == 'getmenucfg': #获取菜单配置列表--所有菜单信息
            resp = menucfg.GetMenuCfg(request)
        elif trantype == 'getmenuinfo': #获取菜单配置详细
            resp = menucfg.GetMenuInfo(request)
        elif trantype == 'getuserrole': #获取用户角色
            resp = userrole.GetUserRole(request)
        elif trantype == 'getrolepurv': #获取角色权限
            resp = userrole.GetRolePurv(request)

        else:
            s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
            resp = HttpResponse(s)
    elif request.method == "GET":
        s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
        resp = HttpResponse(s)

    return resp

def admin_tabledata(request):
    if request.method == "POST": #POST请求
        #请求body转为json
        tmp=request.body
        tmp=tmp.decode(encoding='utf-8')
        reqest_body=json.loads(tmp)

        trantype=reqest_body['trantype']
        # print('-' * 20, trantype, '-' * 20)
        log.info('trantype=[%s]' % trantype)
        if  trantype == 'selecttablehead':  #获取表头
            resp = tablecfg.selectTableHead(request)
        elif trantype == 'selecttabledata': #获取表数据
            resp = tablecfg.selectTableData(request)
        elif trantype == 'getlistdata':  #获取表配置的下拉列表数据元素
            resp = tablecfg.GetListData(request)
        elif trantype == 'gettransferdata':  # 获取穿梭框数据信息
            resp = tablecfg.GetTransferData(request)
        elif trantype == 'addtabledata':  #新增数据
            resp = tablecfg.AddTableData(request)
        elif trantype == 'updtabledata':  #更新数据
            resp = tablecfg.UpdTableData(request)
        elif trantype == 'deltabledata':  #删除数据
            resp = tablecfg.DelTableData(request)
        else:
            s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
            resp = HttpResponse(s)
    elif request.method == "GET": #GET请求
        s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
        resp = HttpResponse(s)

    return resp

##用户登陆退出等操作
def admin_useraction(request, log):
    if request.method == "POST":
        #请求body转为json
        tmp=request.body
        tmp=tmp.decode(encoding='utf-8')
        reqest_body=json.loads(tmp)

        trantype=reqest_body['trantype']
        # print('-'*20,trantype,'-'*20)
        log.info('trantype=[%s]' % trantype)
        if trantype == 'getmessagecode':  #获取短信验证码
            resp = useract.GetMsgCode(request)
        elif trantype == 'getQRcode':  #获取微信登陆二维码
            resp = useract.GetQRCode(request)
        elif trantype == 'login':  #用户登陆,手机短信验证码登陆
            resp = useract.UserLogin(request)
        elif trantype == 'loginbypass':  #使用用户名密码登陆
            resp = useract.LoginByPass(request)
        elif trantype == 'GetUserInfo':  # 获取用户信息
            resp = useract.GetUserInfo(request)
        elif trantype == 'modifypass':  #修改用户登陆密码
            resp = useract.modifypass(request)
        elif trantype == 'loginout':  # 用户退出登陆
            resp = useract.UserLoginOut(request)
        else:
            s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
            resp = HttpResponse(s)
    elif request.method == "GET":
        s = public.setrespinfo({"respcode": "100000", "respmsg": "api error"})
        resp = HttpResponse(s)

    return resp

#用户扫二维码登陆
def AdminLogin(request):
    try:
        starttime=datetime.datetime.now()
        global log
        log, fh=public.loger_init('Admin')
        #print('public.logger.handlers',public.logger.handlers)
        log.info('----------------------Admin-begin---------------------------')
        log.info("请求:[%s]" % request)
        log.info("请求path:[%s]" % request.path)
        log.info("请求method:[%s]"  %  request.method)
        log.info("请求GET:[%s]"  %  request.GET)
        log.info("请求body:[%s]"  % request.body)
        log.info("请求POST:[%s]" % request.POST)

        respinfo=None
        respinfo=useract.UserLogin_Qrcode(request)  #用户扫码登陆处理主流程

    except Exception as e :
        log.warning('程序运行错误', exc_info = True)
        s = public.setrespinfo({"respcode": "999999", "respmsg": "系统错误:"+str(e)})
        respinfo=HttpResponse(s)
        log.info(respinfo.getvalue().decode(encoding='utf-8'))
        log.info('----------------------Admin-end---------------------------')
        if fh:
            fh.close()
            log.removeHandler(fh)
        return respinfo
    finally:
        if not respinfo: #如果返回信息为空
            s = public.setrespinfo({"respcode": "999999", "respmsg": "系统错误"})
            respinfo=HttpResponse(s)
        try:
            log.info(respinfo)
            log.info(respinfo.getvalue().decode(encoding='utf-8'))
        except:
            pass
        log.info('----------------------Admin-end---------------------------')
        print('处理时间:', datetime.datetime.now()-starttime)
        if fh:
            fh.close()
            log.removeHandler(fh)
        return respinfo

#xyhapi
def xyhapi(request):

    url = 'https://xyh.irusheng.com' + request.get_full_path()
    print('xyhapi', url)
    return redirect(url)
