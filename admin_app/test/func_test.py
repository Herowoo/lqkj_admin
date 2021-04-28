# coding:utf-8
# -*- coding: utf-8 -*-
# cython: language_level=3

import datetime


def onwork_days_seconds(start_s, end_s, overtime=False):
    """
    input start time, end time, as standard time str.

    """
    fmt_str = "%Y-%m-%d %H:%M:%S"
    try:
        t1 = datetime.datetime.strptime(start_s, fmt_str)
        t2 = datetime.datetime.strptime(end_s, fmt_str)
    except ValueError:
        print('时间参数无效')
        return -1, -1
    else:
        # 间隔时间
        if t1 < t2:
            dt = t2 - t1
        else:
            dt = t1 - t2
        am_start = datetime.datetime.strptime("%s %s" % (end_s[:10], "08:30:00"), fmt_str)
        am_end = datetime.datetime.strptime("%s %s" % (end_s[:10], "11:30:00"), fmt_str)
        pm_start = datetime.datetime.strptime("%s %s" % (end_s[:10], "13:00:00"), fmt_str)
        pm_end = datetime.datetime.strptime("%s %s" % (end_s[:10], "18:00:00"), fmt_str)
        # 加班天数
        cnt_day = 0
        t_acc = t1
        flag = (t_acc.day < t2.day)
        # 获取加班天数
        while (flag):
            # 工作日
            if not overtime and not (
                    # t_acc.weekday() == 5 or
                    t_acc.weekday() == 6
            ):
                # should read database about saturday.
                # saturday and sunday not counted.
                cnt_day += 1
            t_acc = t_acc + datetime.timedelta(days=1)
            flag = bool(t_acc.day < t2.day)
        # end while loop
        if overtime:
            seconds = dt.seconds
        if t2 < am_start:
            cnt_day -= 1
            t2 = pm_end
        if t_acc < am_start:
            t_acc = am_start
        if am_end < t_acc < pm_start:
            t_acc = am_end
        if pm_end < t2:
            t2 = pm_end
        if am_end < t2 < pm_start:
            t2 = pm_start
        # noon rest
        if not (t_acc <= t2):
            seconds = 0
        else:
            dt = t2 - t1
            if (t_acc <= am_start and pm_end <= t2):
                cnt_day += 1
                seconds = 0
            else:
                if (t_acc <= am_end and pm_start <= t2):
                    seconds = dt.seconds - 5400
                else:
                    seconds = dt.seconds
        return cnt_day, seconds


# a, b = onwork_days_seconds('2021-03-06 08:00:00', '2021-03-08 12:00:00')
#
# print(a, b)

tempdict = {}
tempdict["model_type"] = '001'
tempdict["model_typename"] = '名称'
print(tempdict)
