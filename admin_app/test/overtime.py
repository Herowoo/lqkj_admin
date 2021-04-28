import datetime
from django.db import connection, transaction

fmt_str = "%Y-%m-%d %H:%M:%S"
dic_holidays = ['2021-04-03', '2021-04-04', '2021-04-05', '2021-05-01', '2021-05-02', '2021-05-03', '2021-05-04',
                '2021-05-05', '2021-06-12', '2021-06-13', '2021-06-14', '2021-09-19', '2021-09-20', '2021-09-21'
                , '2021-10-01', '2021-10-02', '2021-10-03', '2021-10-04', '2021-10-05', '2021-10-06', '2021-10-07']
dic_work = ['2021-04-25', '2021-05-08', '2021-09-18', '2021-09-26', '2021-10-09']


def day_second_dif(st_time, end_time):
    "计算加班时长（单位：秒）与加班天数"
    fmt_str = "%Y-%m-%d %H:%M:%S"
    # 跨天
    if datetime.strptime(end_time, fmt_str).day - datetime.strptime(st_time, fmt_str).day > 1:
        end_time = datetime.strptime(end_time,fmt_str) + datetime.timedelta(days=-1)
        total = day_second_dif(st_time, datetime.strptime("%s %s" % (st_time[:10], "23:59:59"), fmt_str))
        total += 0
    overtime_am = (datetime.strptime('00:00:00', '%H:%M:%S'), datetime.strptime('08:30:00', '%H:%M:%S'))
    overtime_pm = (datetime.strptime('18:00:00', '%H:%M:%S'), datetime.strptime('23:59:59', '%H:%M:%S'))
    tup_lanch = (datetime.strptime('11:30:00', '%H:%M:%S'), datetime.strptime('13:00:00', '%H:%M:%S'))
    dt_st_time = datetime.strptime(st_time[11:], '%H:%M:%S')
    dt_end_time = datetime.strptime(end_time[11:], '%H:%M:%S')


    # 工作日
    if real_time(st_time):
        # 加班起始时间在加班范围内，则使用传入时间，否则使用上午上班时间
        if overtime_am[1] > dt_st_time > overtime_am[0] \
                or overtime_pm[1] > dt_st_time > overtime_pm[0]:
            real_st_time = dt_st_time
        else:
            real_st_time = overtime_am[1]

        # 加班结束时间如果在加班范围内，则使用传入时间，否则使用上午上班时间
        if overtime_am[1] > dt_end_time > overtime_am[0] \
                or overtime_pm[1] > dt_end_time > overtime_pm[0]:
            real_end_time = dt_end_time
        else:
            real_end_time = overtime_am[1]

        # 加班时长
        if real_st_time <= overtime_am[1] and real_end_time >= overtime_pm[0]:
            total = real_end_time - overtime_pm[0]
            total += overtime_am[1] - real_st_time
        else:
            total = real_end_time - real_st_time
    # 节假日
    else:
        # 加班起始时间在加班范围内，则使用传入时间，否则使用午餐开始时间
        if tup_lanch[0] > dt_st_time  \
                or dt_st_time > tup_lanch[1]:
            real_st_time = dt_st_time
        else:
            real_st_time = tup_lanch[0]

        # 加班结束时间如果在加班范围内，则使用传入时间，否则使用午餐开始时间
        if tup_lanch[0] > dt_end_time \
                or dt_end_time > tup_lanch[1]:
            real_end_time = dt_end_time
        else:
            real_end_time = tup_lanch[0]
        # 加班时长
        if real_st_time <= tup_lanch[0] and real_end_time >= tup_lanch[1]:
            total = tup_lanch[0] - real_st_time
            total += real_end_time - tup_lanch[1]
        else:
            total = real_end_time - real_st_time

    return total
    # real_start_time,real_end_time = '',''
    # if datetime.strptime(st_time,fmt_str)<normal_time.get('am_start'):

    # if datetime.strptime(st_time,fmt_str).day == datetime.strptime(end_time, fmt_str).day:

    # print(normal_time.get('am_start').hour,normal_time.get(('am_start')).minute, st_time)


def real_time(str_dt):
    dt = datetime.strptime(str_dt, fmt_str)
    if dic_work.count(str_dt[:10]) > 0:
        return str_dt
    elif dic_holidays.count(str_dt[:10]) > 0:
        return None
    elif dt.weekday() == 6:
        return None
    else:
        return str_dt


def time_dif(start, end):
    if end > start:
        return end - start
    else:
        return end - end

# aa = real_time('2021-05-01 12:00:00')
# if aa:
#     print('工作日')
# else:
#     print('节假日')
# print(aa)

tt = day_second_dif('2021-05-01 11:30:00', '2021-05-01 13:01:00')
print(tt)
