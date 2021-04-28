import requests as r
import json
import datetime
import time
import calendar

# api='http://127.0.0.1:8000/api/lqkjbuy'
api='http://192.168.2.174/api/lqkjbuy'

def get_excel_data():
    data={
        'trantype':'get_excel_data',
        "MENU_ID": "10",
        "uid": "38",
        "checksum": "11223355",
        'end_date':'2020-01-21 00:11:00'
    }
    res=r.post(api,data=json.dumps(data))
    print(res.text)

get_excel_data()

# date_str = '2019-09-11 09:46:00'
# fmt = '%Y-%m-%d %H:%M:%S'
# time_tuple = time.strptime(date_str, fmt)
# date = datetime.datetime(*time_tuple[:6])
# print(date, type(date))

# date = datetime.date(2019, 1, 23) # 年，月，日
# first_day = datetime.date(date.year, date.month, 1)#当月第一天
# days_num = calendar.monthrange(first_day.year, first_day.month)[1]  # 获取当前月有多少天
# #求下个月的第一天
# first_day_of_next_month = first_day + datetime.timedelta(days = days_num)
# next_month_days = calendar.monthrange(first_day_of_next_month.year, first_day_of_next_month.month)[1]  # 获取下个月有多少天
# next_month = first_day_of_next_month + datetime.timedelta(days = next_month_days - 1)
# print('下个月最后一天:' + str(next_month))