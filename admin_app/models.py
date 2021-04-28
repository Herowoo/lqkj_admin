
# Create your models here.
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
import json
from datetime import datetime,date
import decimal

class IrsadminDbTranList(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    app_id = models.CharField(db_column='APP_ID', max_length=10)  # Field name made lowercase.
    tran_id = models.CharField(db_column='TRAN_ID', max_length=30, blank=True, null=True)  # Field name made lowercase.
    field_id = models.CharField(db_column='FIELD_ID', max_length=30)  # Field name made lowercase.
    field_name = models.CharField(db_column='FIELD_NAME', max_length=30, blank=True, null=True)  # Field name made lowercase.
    state = models.CharField(db_column='STATE', max_length=1, blank=True, null=True)  # Field name made lowercase.
    data_type = models.CharField(db_column='DATA_TYPE', max_length=30, blank=True, null=True)  # Field name made lowercase.
    field_length = models.IntegerField(db_column='FIELD_LENGTH', blank=True, null=True)  # Field name made lowercase.
    max_length = models.IntegerField(db_column='MAX_LENGTH', blank=True, null=True)  # Field name made lowercase.
    ui_type = models.CharField(db_column='UI_TYPE', max_length=30, blank=True, null=True)  # Field name made lowercase.
    allow_blank = models.CharField(db_column='ALLOW_BLANK', max_length=1, blank=True, null=True)  # Field name made lowercase.
    is_key = models.CharField(db_column='IS_KEY', max_length=1, blank=True, null=True)  # Field name made lowercase.
    search_type = models.CharField(db_column='SEARCH_TYPE', max_length=10, blank=True, null=True)  # Field name made lowercase.
    search_exts = models.CharField(db_column='SEARCH_EXTS', max_length=254, blank=True, null=True)  # Field name made lowercase.
    edit_able = models.CharField(db_column='EDIT_ABLE', max_length=1, blank=True, null=True)  # Field name made lowercase.
    def_value = models.CharField(db_column='DEF_VALUE', max_length=254, blank=True, null=True)  # Field name made lowercase.
    order_id = models.IntegerField(db_column='ORDER_ID', blank=True, null=True)  # Field name made lowercase.
    snote = models.CharField(db_column='SNOTE', max_length=90, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'IRSADMIN_DB_TRAN_LIST'
        unique_together = (('app_id', 'field_id'),)


class IrsadminDbTranReg(models.Model):
    app_id = models.AutoField(db_column='APP_ID', primary_key=True)  # Field name made lowercase.
    tran_id = models.CharField(db_column='TRAN_ID', max_length=100, blank=True, null=True)  # Field name made lowercase.
    tran_desc = models.CharField(db_column='TRAN_DESC', max_length=100, blank=True)  # Field name made lowercase.
    where_ctrl = models.CharField(db_column='WHERE_CTRL', max_length=200, blank=True, null=True)  # Field name made lowercase.
    order_ctrl = models.CharField(db_column='ORDER_CTRL', max_length=200, blank=True, null=True)  # Field name made lowercase.
    group_ctrl = models.CharField(db_column='GROUP_CTRL', max_length=200, blank=True, null=True)  # Field name made lowercase.
    table_name = models.CharField(db_column='TABLE_NAME', max_length=30, blank=True, null=True)  # Field name made lowercase.
    data_source = models.CharField(db_column='DATA_SOURCE', max_length=20, blank=True, null=True)  # Field name made lowercase.
    main_control = models.CharField(db_column='MAIN_CONTROL', max_length=50, blank=True, null=True)  # Field name made lowercase.
    select_able = models.CharField(db_column='SELECT_ABLE', max_length=1, blank=True, null=True)  # Field name made lowercase.
    insert_able = models.CharField(db_column='INSERT_ABLE', max_length=1, blank=True, null=True)  # Field name made lowercase.
    update_able = models.CharField(db_column='UPDATE_ABLE', max_length=1, blank=True, null=True)  # Field name made lowercase.
    delete_able = models.CharField(db_column='DELETE_ABLE', max_length=1, blank=True, null=True)  # Field name made lowercase.
    export_able = models.CharField(db_column='EXPORT_ABLE', max_length=1, blank=True, null=True)  # Field name made lowercase.
    plugins = models.CharField(db_column='PLUGINS', max_length=254, blank=True, null=True)  # Field name made lowercase.
    snote = models.CharField(db_column='SNOTE', max_length=90, blank=True, null=True)  # Field name made lowercase.
    create_time = models.DateTimeField(db_column='CREATE_TIME', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'IRSADMIN_DB_TRAN_REG'

class IrsadminDbTranferCfg(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    left_title = models.CharField(db_column='LEFT_TITLE', max_length=20)  # Field name made lowercase.
    left_sql = models.CharField(db_column='LEFT_SQL', max_length=300)  # Field name made lowercase.
    right_title = models.CharField(db_column='RIGHT_TITLE', max_length=20)  # Field name made lowercase.
    right_sql = models.CharField(db_column='RIGHT_SQL', max_length=300)  # Field name made lowercase.
    insert_sql = models.CharField(db_column='INSERT_SQL', max_length=300)  # Field name made lowercase.
    delete_sql = models.CharField(db_column='DELETE_SQL', max_length=300)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'irsadmin_db_tranfer_cfg'

class IrsadminTranCfg(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    button_name = models.CharField(db_column='BUTTON_NAME', max_length=20)  # Field name made lowercase.
    button_type = models.CharField(db_column='BUTTON_TYPE', max_length=30)  # Field name made lowercase.
    button_color = models.CharField(db_column='BUTTON_COLOR', max_length=30, blank=True, null=True)  # Field name made lowercase.
    button_length = models.IntegerField(db_column='BUTTON_LENGTH', blank=True, null=True)  # Field name made lowercase.
    button_trantype = models.CharField(db_column='BUTTON_TRANTYPE', max_length=30)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'irsadmin_tran_cfg'


class IrsadminMenu(models.Model):
    menu_id = models.AutoField(db_column='MENU_ID', primary_key=True)  # Field name made lowercase.
    above_menu_id = models.CharField(db_column='ABOVE_MENU_ID', max_length=20, blank=True, null=True)  # Field name made lowercase.
    menu_deep = models.IntegerField(db_column='MENU_DEEP', blank=True, null=True)  # Field name made lowercase.
    menu_name = models.CharField(db_column='MENU_NAME', max_length=30, blank=True, null=True)  # Field name made lowercase.
    menu_desc = models.CharField(db_column='MENU_DESC', max_length=50, blank=True, null=True)  # Field name made lowercase.
    is_run_menu = models.CharField(db_column='IS_RUN_MENU', max_length=1, blank=True, null=True)  # Field name made lowercase.
    app_id = models.IntegerField(db_column='APP_ID', blank=True, null=True)  # Field name made lowercase.
    tran_id = models.CharField(db_column='TRAN_ID', max_length=20, blank=True, null=True)  # Field name made lowercase.
    is_enable = models.CharField(db_column='IS_ENABLE', max_length=1, blank=True, null=True)  # Field name made lowercase.
    order_id = models.CharField(db_column='ORDER_ID', max_length=10, blank=True, null=True)  # Field name made lowercase.
    menu_path = models.CharField(db_column='MENU_PATH', max_length=50, blank=True, null=True)  # Field name made lowercase.
    system_id = models.CharField(db_column='SYSTEM_ID', max_length=10, blank=True, null=True)  # Field name made lowercase.
    snote = models.CharField(db_column='SNOTE', max_length=90, blank=True, null=True)  # Field name made lowercase.
    create_time = models.DateTimeField(db_column='CREATE_TIME', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'IRSADMIN_MENU'


class IrsadminRole(models.Model):
    role_id = models.CharField(db_column='ROLE_ID', primary_key=True, max_length=20)  # Field name made lowercase.
    role_name = models.CharField(db_column='ROLE_NAME', max_length=30, blank=True, null=True)  # Field name made lowercase.
    role_desc = models.CharField(db_column='ROLE_DESC', max_length=90, blank=True, null=True)  # Field name made lowercase.
    snote = models.CharField(db_column='SNOTE', max_length=90, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'IRSADMIN_ROLE'


class IrsadminRolePurv(models.Model):
    role_id = models.CharField(db_column='ROLE_ID', primary_key=True, max_length=20)  # Field name made lowercase.
    menu_id = models.CharField(db_column='MENU_ID', max_length=30, blank=True, null=True)  # Field name made lowercase.
    delete_able = models.CharField(db_column='DELETE_ABLE', max_length=1, blank=True, null=True)  # Field name made lowercase.
    insert_able = models.CharField(db_column='INSERT_ABLE', max_length=1, blank=True, null=True)  # Field name made lowercase.
    update_able = models.CharField(db_column='UPDATE_ABLE', max_length=1, blank=True, null=True)  # Field name made lowercase.
    export_able = models.CharField(db_column='EXPORT_ABLE', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'IRSADMIN_ROLE_PURV'


class IrsadminUser(models.Model):
    user_id = models.AutoField(db_column='USER_ID', primary_key=True)
    user_name = models.CharField(db_column='USER_NAME', max_length=30, blank=True, null=True)  # Field name made lowercase.
    org_id = models.CharField(db_column='ORG_ID', max_length=20, blank=True, null=True)  # Field name made lowercase.
    passwd = models.CharField(db_column='PASSWD', max_length=32, blank=True, null=True)  # Field name made lowercase.
    old_passwd = models.CharField(db_column='OLD_PASSWD', max_length=32, blank=True, null=True)  # Field name made lowercase.
    station = models.CharField(db_column='STATION', max_length=60, blank=True, null=True)  # Field name made lowercase.
    certi_type = models.CharField(db_column='CERTI_TYPE', max_length=2, blank=True, null=True)  # Field name made lowercase.
    certi = models.CharField(db_column='CERTI', max_length=18, blank=True, null=True)  # Field name made lowercase.
    sex = models.CharField(db_column='SEX', max_length=1, blank=True, null=True)  # Field name made lowercase.
    address = models.CharField(db_column='ADDRESS', max_length=200, blank=True, null=True)  # Field name made lowercase.
    tel = models.CharField(db_column='TEL', max_length=25, blank=True, null=True)  # Field name made lowercase.
    email = models.CharField(db_column='EMAIL', max_length=50, blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.
    uid = models.CharField(db_column='UID', max_length=90, blank=True, null=True)  # Field name made lowercase.
    head_imgurl = models.CharField(db_column='HEAD_IMGURL', max_length=300, blank=True, null=True)  # Field name made lowercase.
    create_user = models.IntegerField(db_column='CREATE_USER', blank=True, null=True)  # Field name made lowercase.
    create_time = models.DateTimeField(db_column='CREATE_TIME', blank=True, null=True)  # Field name made lowercase.
    update_time = models.DateTimeField(db_column='UPDATE_TIME', blank=True, null=True)  # Field name made lowercase.
    delete_time = models.DateTimeField(db_column='DELETE_TIME', blank=True, null=True)  # Field name made lowercase.
    snote = models.CharField(db_column='SNOTE', max_length=90, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'IRSADMIN_USER'


class IrsadminUserRule(models.Model):
    user_id = models.CharField(db_column='USER_ID', primary_key=True, max_length=20)  # Field name made lowercase.
    role_id = models.CharField(db_column='ROLE_ID', max_length=20, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'IRSADMIN_USER_RULE'

class IrsYwtyDict(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    dict_name = models.CharField(db_column='DICT_NAME', max_length=50)  # Field name made lowercase.
    dict_code = models.CharField(db_column='DICT_CODE', max_length=50)  # Field name made lowercase.
    dict_target = models.CharField(db_column='DICT_TARGET', max_length=50, blank=True, null=True)  # Field name made lowercase.
    dict_default = models.CharField(db_column='DICT_DEFAULT', max_length=1, blank=True, null=True)  # Field name made lowercase.
    dict_snote = models.CharField(db_column='DICT_SNOTE', max_length=200, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'IRS_YWTY_DICT'
        unique_together = (('dict_name', 'dict_code'),)

class IrsServerMobilemessage(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    trandatetime = models.DateTimeField(blank=True, null=True)
    trantype = models.CharField(max_length=20, blank=True, null=True)
    qtdatetime = models.DateTimeField(blank=True, null=True)
    qtip = models.CharField(max_length=27, blank=True, null=True)
    mobile = models.CharField(max_length=11, blank=True, null=True)
    checkcode = models.CharField(max_length=6, blank=True, null=True)
    msginfo = models.CharField(max_length=100, blank=True, null=True)
    msgstate = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'irs_server_mobilemessage'

#将date datetime decimal类型转换为json
class JsonCustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(o, date):
            return o.strftime("%Y-%m-%d")
        elif isinstance(o,decimal.Decimal):
            return float(o)
        else:
            return json.JSONEncoder.default(self, o)

#用户信息表
class IrsServerConsumer(models.Model):
    id = models.IntegerField(db_column='ID', primary_key=True)  # Field name made lowercase.
    head_imgurl = models.CharField(db_column='HEAD_IMGURL', max_length=300, blank=True, null=True)  # Field name made lowercase.
    nick_name = models.CharField(db_column='NICK_NAME', max_length=60, blank=True, null=True)  # Field name made lowercase.
    mobile_phone = models.CharField(db_column='MOBILE_PHONE', max_length=11, blank=True, null=True)  # Field name made lowercase.
    wx_gzh = models.CharField(db_column='WX_GZH', max_length=20, blank=True, null=True)  # Field name made lowercase.
    wx_open_id = models.CharField(db_column='WX_OPEN_ID', max_length=64, blank=True, null=True)  # Field name made lowercase.
    union_id = models.CharField(db_column='UNION_ID', unique=True, max_length=64)  # Field name made lowercase.
    user_name = models.CharField(db_column='USER_NAME', max_length=50, blank=True, null=True)  # Field name made lowercase.
    user_sex = models.CharField(db_column='USER_SEX', max_length=50, blank=True, null=True)  # Field name made lowercase.
    certificate_id = models.CharField(db_column='CERTIFICATE_ID', max_length=18, blank=True, null=True)  # Field name made lowercase.
    #register_date = models.DateField(db_column='REGISTER_DATE', blank=True, null=True)  # Field name made lowercase.
    register_date = models.DateTimeField(u'REGISTER_DATE', auto_now_add=True)
    user_address = models.CharField(db_column='USER_ADDRESS', max_length=200, blank=True, null=True)  # Field name made lowercase.
    user_status = models.CharField(db_column='USER_STATUS', max_length=1, blank=True, null=True)  # Field name made lowercase.
    vip_flag = models.CharField(db_column='VIP_FLAG', max_length=10, blank=True, null=True)  # Field name made lowercase.
    mobile_flag = models.CharField(db_column='MOBILE_FLAG', max_length=1, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'IRS_SERVER_CONSUMER'


class IrsServerToken(models.Model):
    app_name = models.CharField(db_column='APP_NAME', primary_key=True, max_length=10)  # Field name made lowercase.
    appid = models.CharField(db_column='APPID', max_length=20, blank=True, null=True)  # Field name made lowercase.
    appsecret = models.CharField(db_column='APPSECRET', max_length=32, blank=True, null=True)  # Field name made lowercase.
    encodingaeskey = models.CharField(db_column='EncodingAESKey', max_length=60, blank=True, null=True)  # Field name made lowercase.
    token = models.CharField(db_column='TOKEN', max_length=60, blank=True, null=True)  # Field name made lowercase.
    access_token = models.CharField(max_length=512, blank=True, null=True)
    expire_in = models.IntegerField(blank=True, null=True)
    access_token_gettime = models.DateTimeField(blank=True, null=True)
    access_token_url = models.CharField(max_length=200, blank=True, null=True)
    state = models.CharField(db_column='STATE', max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'IRS_SERVER_TOKEN'

#管理台文件上传登记表
class IrsadminUnfileInfo(models.Model):
    file_id = models.AutoField(db_column='FILE_ID', primary_key=True)  # Field name made lowercase.
    user_id = models.CharField(db_column='USER_ID', max_length=20)  # Field name made lowercase.
    sheet_name = models.CharField(db_column='SHEET_NAME', max_length=60, blank=True, null=True)  # Field name made lowercase.
    ip = models.CharField(db_column='IP', max_length=20, blank=True, null=True)  # Field name made lowercase.
    tran_time = models.DateTimeField(db_column='TRAN_TIME')  # Field name made lowercase.
    menu_id = models.IntegerField(db_column='MENU_ID', blank=True, null=True)  # Field name made lowercase.
    file_path = models.CharField(db_column='FILE_PATH', max_length=200)  # Field name made lowercase.
    file_name = models.CharField(db_column='FILE_NAME', max_length=120)  # Field name made lowercase.
    file_rows = models.IntegerField(db_column='FILE_ROWS', blank=True, null=True)  # Field name made lowercase.
    deal_num = models.IntegerField(db_column='DEAL_NUM', blank=True, null=True)  # Field name made lowercase.
    repeat_num = models.IntegerField(db_column='REPEAT_NUM', blank=True, null=True)  # Field name made lowercase.
    error_num = models.IntegerField(db_column='ERROR_NUM', blank=True, null=True)  # Field name made lowercase.
    deal_type = models.CharField(db_column='DEAL_TYPE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    resp_time = models.DateTimeField(db_column='RESP_TIME')  # Field name made lowercase.
    resp_code = models.CharField(db_column='RESP_CODE', max_length=10, blank=True, null=True)  # Field name made lowercase.
    resp_msg = models.CharField(db_column='RESP_MSG', max_length=120, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'irsadmin_db_unfile_info'

#前端敏捷开发组件登记表
class IrsServerVueComponents(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    user_id = models.IntegerField(db_column='USER_ID')  # Field name made lowercase.
    create_time = models.DateTimeField(db_column='CREATE_TIME')  # Field name made lowercase.
    update_time = models.DateTimeField(db_column='UPDATE_TIME', blank=True, null=True)  # Field name made lowercase.
    comp_name = models.CharField(db_column='COMP_NAME', max_length=100)  # Field name made lowercase.
    comp_path = models.CharField(db_column='COMP_PATH', max_length=100)  # Field name made lowercase.
    comp_tag = models.CharField(db_column='COMP_TAG', max_length=100, blank=True, null=True)  # Field name made lowercase.
    status = models.CharField(db_column='STATUS', max_length=1)  # Field name made lowercase.
    notes = models.CharField(db_column='NOTES', max_length=200, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'irs_server_vue_components'


class SysWorkflowNodeCfg(models.Model):
    wf_id = models.AutoField(primary_key=True)
    form_id = models.IntegerField()
    wf_type = models.CharField(max_length=20, blank=True, null=True)
    wf_prev = models.IntegerField(blank=True, null=True)
    wf_next = models.IntegerField(blank=True, null=True)
    wf_cfg = models.TextField(blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
    wf_state = models.CharField(max_length=1, blank=True, null=True)
    wf_notes = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sys_workflow_node_cfg'
        unique_together = (('wf_id', 'form_id'),)
