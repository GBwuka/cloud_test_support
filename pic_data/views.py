import xlwt
from io import StringIO, BytesIO

import datetime
from itertools import groupby
from functools import reduce

from datetime import datetime
from datetime import timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.db.models import Avg, Max, Min, Count, Sum
import pandas as pd
from pandas import DataFrame

from .models import PicData
from .utils import data_score, efficiency_score, accuracy_score, proficiency_score, score, dif_modal, send_util, download_image, custom_avg

@csrf_exempt
@login_required
def display_commonuser(request):
    if request.is_ajax():
        return dif_modal(request)
    else:
        if request.user.is_superuser:
            return render(request, 'login.html')
        else:
            try:
                date_begin = request.GET.get('date_begin')
                date_end = request.GET.get('date_end')
                time_delta = request.GET.get('time_delta')
                date_begin_sql = PicData.objects.values('created_date').distinct().order_by('created_date').first()['created_date'].strftime("%Y-%m-%d")
                date_end_sql = PicData.objects.values('created_date').distinct().order_by('created_date').last()['created_date'].strftime("%Y-%m-%d")
                if date_begin == "" and date_end == "":
                    if time_delta:
                        now = datetime.now()
                        now_delta = now + timedelta(days=-(int(time_delta)-1))
                        data = PicData.objects.filter(created_date__gte=now_delta).filter(created_date__lte=now)\
                        .filter(username=request.user.username).order_by('created_date')
                    else:
                        data = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end_sql)\
                        .filter(username=request.user.username).order_by('created_date')
                elif date_begin == "":
                    data = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end)\
                    .filter(username=request.user.username).order_by('created_date')
                elif date_end == "":
                    data = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end_sql)\
                    .filter(username=request.user.username).order_by('created_date')
                else:
                    data = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end)\
                    .filter(username=request.user.username).order_by('created_date')
                user_list = []
                user_list.append(request.user.username)
                date_list = []
                total_data_list = []
                efficiency_data_list = []
                rr = []
                for d in data:
                    r = {}
                    date_list.append(d.created_date.strftime("%Y-%m-%d"))
                    total_data_list.append(d.total_data)
                    efficiency_data_list.append(d.efficiency)
                    if d.is_on_duty:
                        is_on_duty = "是"
                    else:
                        is_on_duty = "否"
                    r = {
                        'id': d.id,
                        'created_date': d.created_date.strftime("%Y-%m-%d"),
                        'total_data': d.total_data,
                        'spend_time': d.spend_time,
                        'efficiency': d.efficiency,
                        'is_on_duty': is_on_duty,
                        'remark': d.remark,
                        'username': d.username
                    }
                    rr.append(r)
                rr.reverse()
                paginator = Paginator(rr,10)
                page = request.GET.get('page')
                try:
                    table_data = paginator.page(page)
                except PageNotAnInteger:
                    table_data = paginator.page(1)
                except EmptyPage:
                    table_data = paginator.page(paginator.num_pages)
                return render(request, 'display_commonuser_data.html', {'username': request.user.username, 'data': table_data, 
                    'user_list': user_list, 'date_list': date_list, 'total_data_list': total_data_list, 
                    'efficiency_data_list': efficiency_data_list, 'time_delta': time_delta, 'date_begin': date_begin, 'date_end': date_end})
            except Exception as e:
                return render(request, 'display_commonuser_data.html', {'username': request.user.username})

@csrf_exempt
@login_required
def display_superuser(request):
    if request.is_ajax():
        return dif_modal(request)
    else:
        if request.user.is_superuser:
            try:
                date_range = []
                date_begin = request.GET.get('date_begin')
                date_end = request.GET.get('date_end')
                time_delta = request.GET.get('time_delta')
                date_begin_sql = PicData.objects.values('created_date').distinct().order_by('created_date').first()['created_date'].strftime("%Y-%m-%d")
                date_end_sql = PicData.objects.values('created_date').distinct().order_by('created_date').last()['created_date'].strftime("%Y-%m-%d")
                if date_begin == "" and date_end == "":
                    if time_delta:
                        now = datetime.now()
                        now_delta = now + timedelta(days=-(int(time_delta)-1))
                        data = PicData.objects.filter(created_date__gte=now_delta).filter(created_date__lte=now)\
                        .order_by('username', 'created_date').values_list("id", "username", "created_date", "total_data", "spend_time", "efficiency")
                        table_data = PicData.objects.filter(created_date__gte=now_delta).filter(created_date__lte=now)\
                        .order_by('created_date')
                        data_bar = PicData.objects.filter(created_date__gte=now_delta).filter(created_date__lte=now)
                        date_range.append(now_delta.strftime("%Y-%m-%d") + "-----" + now.strftime("%Y-%m-%d"))
                    else:
                        data = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end_sql)\
                        .order_by('username', 'created_date').values_list("id", "username", "created_date", "total_data", "spend_time", "efficiency")
                        table_data = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end_sql)\
                        .order_by('created_date')
                        data_bar = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end_sql)
                        date_range.append(date_begin_sql + "-----" + date_end_sql)
                elif date_begin == "":
                    data = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end)\
                    .order_by('username', 'created_date').values_list("id", "username", "created_date", "total_data", "spend_time", "efficiency")
                    table_data = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end)\
                    .order_by('created_date')
                    data_bar = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end)
                    date_range.append(date_begin_sql + "-----" + date_end)
                elif date_end == "":
                    data = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end_sql)\
                    .order_by('username', 'created_date').values_list("id", "username", "created_date", "total_data", "spend_time", "efficiency")
                    table_data = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end_sql)\
                    .order_by('created_date')
                    data_bar = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end_sql)
                    date_range.append(date_begin + "-----" + date_end_sql)
                else:
                    data = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end)\
                    .order_by('username', 'created_date').values_list("id", "username", "created_date", "total_data", "spend_time", "efficiency")
                    table_data = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end)\
                    .order_by('created_date')
                    data_bar = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end)
                    date_range.append(date_begin + "-----" + date_end)

                res = {}
                for username, value in groupby(data, key=lambda x: x[1]):
                    res[str(username)] = list(value)

                users = res.keys()
                dfs = []
                for username, value in res.items():
                    d = list(zip(*value)) or [[]] * 6

                    key_total_data = "total_data_%s" % username
                    key_spend_time = "spend_time_%s" % username
                    key_efficiency = "efficiency_%s" % username

                    r = {
                        "c_date": list(d[2]),
                        key_total_data: list(d[3]),
                        key_spend_time: list(d[4]),
                        key_efficiency: list(d[5])
                    }

                    df = DataFrame(r)
                    df.index = df["c_date"]
                    df.index = pd.to_datetime(df.index)
                    df = df.drop(["c_date"], 1)
                    dfs.append(df)

                try:
                    df = reduce(lambda x, y: pd.merge(x, y, left_index=True, right_index=True, how="outer"), dfs).fillna(0)
                except TypeError as e:
                    return render(request, 'display_superuser_data.html', {'username': request.user.username, 'table_data': [], 'data': [], 
                    'user': [], 'dates': [], 'date_range': [], 'user_list_bar': [], 'time_delta': ""})

                dates = list(df.index.map(lambda x: x.strftime("%Y-%m-%d")))
                ret = {}
                for u in users:
                    key_total_data = "total_data_%s" % u
                    key_spend_time = "spend_time_%s" % u
                    key_efficiency = "efficiency_%s" % u

                    ret[str(u)] = {
                        "total_data": list(df[key_total_data]),
                        "spend_time": list(df[key_spend_time]),
                        "efficiency": list(df[key_efficiency])
                    }

                total_bar = {}
                sorted_user_total_data_list = []
                sorted_user_efficiency_list = []
                sorted_user_avg_total_data_list = []
                user_total_data_bar = []
                user_efficiency_bar = []
                user_avg_total_data_bar = []
                for u in users:
                    total_data_bar_dict = ()
                    efficiency_bar_dict = ()
                    avg_total_data_bar_dict = ()
                    total_data_bar = data_bar.filter(username=u).aggregate(Sum('total_data'))['total_data__sum']
                    spend_time_bar = data_bar.filter(username=u).aggregate(Sum('spend_time'))['spend_time__sum']
                    avg_total_data_temp = data_bar.filter(username=u).values_list('total_data')
                    avg_total_data_list = []
                    for i in avg_total_data_temp:
                        avg_total_data_list.append(i[0])
                    avg_total_data_list.sort()
                    avg_total_data_bar = custom_avg(avg_total_data_list)
                    if spend_time_bar:
                        efficiency_bar = float('%.2f' % (int(total_data_bar)/float(spend_time_bar)))
                    else:
                        efficiency_bar = 0
                    total_bar[str(u)] = {
                        'total_data': [total_data_bar],
                        'spend_time': [spend_time_bar],
                        'efficiency': [efficiency_bar],
                        'avg_total_data': [avg_total_data_bar]
                    }
                    total_data_bar_dict = str(u), total_data_bar
                    efficiency_bar_dict = str(u), efficiency_bar
                    avg_total_data_bar_dict = str(u), avg_total_data_bar
                    user_total_data_bar.append(total_data_bar_dict)
                    user_efficiency_bar.append(efficiency_bar_dict)
                    user_avg_total_data_bar.append(avg_total_data_bar_dict)
                sorted_user_total_data_bar = sorted(user_total_data_bar, key=lambda d: d[1])
                sorted_user_efficiency_bar = sorted(user_efficiency_bar, key=lambda d: d[1])
                sorted_user_avg_total_data_bar = sorted(user_avg_total_data_bar, key=lambda d: d[1])
                for i in sorted_user_total_data_bar:
                    sorted_user_total_data_list.append(i[0])
                for i in sorted_user_efficiency_bar:
                    sorted_user_efficiency_list.append(i[0])
                for i in sorted_user_avg_total_data_bar:
                    sorted_user_avg_total_data_list.append(i[0])
                # print(sorted_user_total_data_list)
                # print(sorted_user_efficiency_list)
                # print(sorted_user_avg_total_data_list)
                spend_time_dict = {}
                for u in users:
                    spend_time_date_dict = {}
                    for d in dates:
                        try:
                            spend_time_date_dict[str(d)] = data_bar.filter(created_date=d,username=u).values('spend_time').first()['spend_time']
                        except Exception as e:
                            spend_time_date_dict[str(d)] = ""
                        spend_time_dict[str(u)] = spend_time_date_dict

                flag_dict = {}
                for u in users:
                    flag_date_dict = {}
                    for d in dates:
                        try:
                            flag_date_dict[str(d)] = data_bar.filter(created_date=d,username=u).values('remark_flag').first()['remark_flag']
                        except Exception as e:
                            flag_date_dict[str(d)] = ""
                        flag_dict[str(u)] = flag_date_dict

                remark_dict = {}
                for u in users:
                    remark_date_dict = {}
                    for d in dates:
                        try:
                            remark_date_dict[str(d)] = data_bar.filter(created_date=d,username=u).values('remark').first()['remark']
                        except Exception as e:
                            remark_date_dict[str(d)] = ""
                        remark_dict[str(u)] = remark_date_dict

                rr = []
                for d in table_data:
                    r = {}
                    r = {
                        'id': d.id,
                        'created_date': d.created_date.strftime("%Y-%m-%d"),
                        'total_data': d.total_data,
                        'spend_time': d.spend_time,
                        'efficiency': d.efficiency,
                        'username': d.username
                    }
                    rr.append(r)
                rr.reverse()
                return render(request, 'display_superuser_data.html', {'username': request.user.username, 'table_data': rr, 'data': ret, 
                    'user': list(users), 'user_total_data': sorted_user_total_data_list, 'user_efficiency': sorted_user_efficiency_list, 
                    'user_avg_total_data': sorted_user_avg_total_data_list, 'dates': dates , 'date_range': date_range, 'total_bar': total_bar, 
                    'time_delta': time_delta, 'date_begin': date_begin, 'date_end': date_end, 'spend_time_dict': spend_time_dict, 
                    'flag_dict': flag_dict, 'remark_dict': remark_dict})
            except Exception as e:
                return render(request, 'display_superuser_data.html', {'username': request.user.username})
        else:
            return render(request, 'login.html')

@csrf_exempt
@login_required
def display_total(request):
    if request.is_ajax():
        return dif_modal(request)
    else:
        if request.user.is_superuser:
            try:
                date_begin = request.GET.get('date_begin')
                date_end = request.GET.get('date_end')
                time_delta = request.GET.get('time_delta')
                date_begin_sql = PicData.objects.values('created_date').distinct().order_by('created_date').first()['created_date'].strftime("%Y-%m-%d")
                date_end_sql = PicData.objects.values('created_date').distinct().order_by('created_date').last()['created_date'].strftime("%Y-%m-%d")
                if date_begin == "" and date_end == "":
                    if time_delta:
                        now = datetime.now()
                        now_delta = now + timedelta(days=-(int(time_delta)-1))
                        data = PicData.objects.filter(created_date__gte=now_delta).filter(created_date__lte=now)\
                        .values('created_date').distinct().order_by('created_date')
                    else:
                        data = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end_sql)\
                        .values('created_date').distinct().order_by('created_date')
                elif date_begin == "":
                    data = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end)\
                    .values('created_date').distinct().order_by('created_date')
                elif date_end == "":
                    data = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end_sql)\
                    .values('created_date').distinct().order_by('created_date')
                else:
                    data = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end)\
                    .values('created_date').distinct().order_by('created_date')
                user_list = []
                user_list.append('总体')
                date_list = []
                total_data_list = []
                avg_total_data_list = []
                spend_time_list = []
                spend_time_dict = {}
                efficiency_data_list = []
                avg_efficiency_data_list = []
                rr = []
                for d in data:
                    date_list.append(d['created_date'].strftime("%Y-%m-%d"))
                for date in date_list:
                    r = {}
                    total_data = PicData.objects.filter(created_date=date).aggregate(Sum('total_data'))['total_data__sum']
                    total_data_list.append(total_data)
                    avg_total_data_list.append(total_data)
                    spend_time = PicData.objects.filter(created_date=date).aggregate(Sum('spend_time'))['spend_time__sum']
                    spend_time_list.append(spend_time)
                    spend_time_dict[date] = spend_time
                    if spend_time:
                        efficiency = float('%.2f' % (int(total_data)/float(spend_time)))
                    else:
                        efficiency = 0
                    efficiency_data_list.append(efficiency)
                    avg_efficiency_data_list.append(efficiency)
                    r = {
                        'created_date': date,
                        'total_data': total_data,
                        'spend_time': spend_time,
                        'efficiency': efficiency,
                    }
                    rr.append(r)
                rr.reverse()
                avg_total_data_list.sort()
                avg_total_data = custom_avg(avg_total_data_list)
                avg_efficiency_data_list.sort()
                avg_efficiency_data = custom_avg(avg_efficiency_data_list)

                return render(request, 'display_total_data.html', {'username': request.user.username, 'data': rr, 'user_list': user_list, 'date_list': date_list, 
                    'total_data_list': total_data_list, 'spend_time_list': spend_time_list, 'efficiency_data_list':efficiency_data_list,
                    'time_delta': time_delta, 'date_begin': date_begin, 'date_end': date_end, 'spend_time_dict': spend_time_dict,
                    'avg_total_data': avg_total_data, 'avg_efficiency_data':avg_efficiency_data})
            except Exception as e:
                return render(request, 'display_total_data.html', {'username': request.user.username})
        else:
            return render(request, 'login.html')

@csrf_exempt
@login_required
def display_score(request):
    if request.is_ajax():
        return dif_modal(request)
    else:
        if request.user.is_superuser:
            try:
                date_range = []
                date_begin = request.GET.get('date_begin')
                date_end = request.GET.get('date_end')
                time_delta = request.GET.get('time_delta')
                date_begin_sql = PicData.objects.values('created_date').distinct().order_by('created_date').first()['created_date'].strftime("%Y-%m-%d")
                date_end_sql = PicData.objects.values('created_date').distinct().order_by('created_date').last()['created_date'].strftime("%Y-%m-%d")
                if date_begin == "" and date_end == "":
                    if time_delta:
                        now = datetime.now()
                        now_delta = now + timedelta(days=-(int(time_delta)-1))
                        data = PicData.objects.filter(created_date__gte=now_delta).filter(created_date__lte=now)\
                        .order_by('username', 'created_date').values_list("id", "username", "created_date", "total_data", "spend_time", "efficiency",
                            "label_score")
                        table_data = PicData.objects.filter(created_date__gte=now_delta).filter(created_date__lte=now)\
                        .order_by('created_date')
                        data_bar = PicData.objects.filter(created_date__gte=now_delta).filter(created_date__lte=now)
                        date_range.append(now_delta.strftime("%Y-%m-%d") + "-----" + now.strftime("%Y-%m-%d"))
                    else:
                        data = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end_sql)\
                        .order_by('username', 'created_date').values_list("id", "username", "created_date", "total_data", "spend_time", "efficiency",
                            "label_score")
                        table_data = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end_sql)\
                        .order_by('created_date')
                        data_bar = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end_sql)
                        date_range.append(date_begin_sql + "-----" + date_end_sql)
                elif date_begin == "":
                    data = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end)\
                    .order_by('username', 'created_date').values_list("id", "username", "created_date", "total_data", "spend_time", "efficiency",
                        "label_score")
                    table_data = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end)\
                    .order_by('created_date')
                    data_bar = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end)
                    date_range.append(date_begin_sql + "-----" + date_end)
                elif date_end == "":
                    data = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end_sql)\
                    .order_by('username', 'created_date').values_list("id", "username", "created_date", "total_data", "spend_time", "efficiency",
                        "label_score")
                    table_data = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end_sql)\
                    .order_by('created_date')
                    data_bar = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end_sql)
                    date_range.append(date_begin + "-----" + date_end_sql)
                else:
                    data = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end)\
                    .order_by('username', 'created_date').values_list("id", "username", "created_date", "total_data", "spend_time", "efficiency",
                        "label_score")
                    table_data = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end)\
                    .order_by('created_date')
                    data_bar = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end)
                    date_range.append(date_begin + "-----" + date_end)

                res = {}
                for username, value in groupby(data, key=lambda x: x[1]):
                    res[str(username)] = list(value)

                users = res.keys()
                dfs = []
                for username, value in res.items():
                    d = list(zip(*value)) or [[]] * 6

                    key_total_data = "total_data_%s" % username
                    key_spend_time = "spend_time_%s" % username
                    key_efficiency = "efficiency_%s" % username
                    # key_previous_total_data = "previous_total_data_%s" % username
                    key_label_score = "label_score_%s" % username

                    r = {
                        "c_date": list(d[2]),
                        key_total_data: list(d[3]),
                        key_spend_time: list(d[4]),
                        key_efficiency: list(d[5]),
                        # key_previous_total_data: list(d[6]),
                        key_label_score: list(d[6])
                    }

                    df = DataFrame(r)
                    df.index = df["c_date"]
                    df.index = pd.to_datetime(df.index)
                    df = df.drop(["c_date"], 1)
                    dfs.append(df)

                try:
                    df = reduce(lambda x, y: pd.merge(x, y, left_index=True, right_index=True, how="outer"), dfs).fillna(0)
                except TypeError as e:
                    return render(request, 'display_score.html', {'username': request.user.username, 'table_data': [], 'data': [], 
                    'user': [], 'dates': [], 'date_range': [], 'user_list_bar': [], 'time_delta': ""})

                dates = list(df.index.map(lambda x: x.strftime("%Y-%m-%d")))
                ret = {}
                for u in users:
                    key_total_data = "total_data_%s" % u
                    key_spend_time = "spend_time_%s" % u
                    key_efficiency = "efficiency_%s" % u
                    key_label_score = "label_score_%s" % u

                    ret[str(u)] = {
                        "total_data": list(df[key_total_data]),
                        "spend_time": list(df[key_spend_time]),
                        "efficiency": list(df[key_efficiency]),
                        "label_score": list(df[key_label_score])
                    }

                total_bar = {}
                sorted_user_avg_score_list = []
                user_avg_score_bar = []
                for u in users:
                    avg_score_bar_dict = ()
                    total_data_bar = data_bar.filter(username=u).aggregate(Sum('total_data'))['total_data__sum']
                    spend_time_bar = data_bar.filter(username=u).aggregate(Sum('spend_time'))['spend_time__sum']
                    avg_label_score_bar = float('%.2f' % (data_bar.filter(username=u)\
                        .aggregate(Avg('label_score'))['label_score__avg']))
                    if spend_time_bar:
                        efficiency_bar = float('%.2f' % (int(total_data_bar)/float(spend_time_bar)))
                    else:
                        efficiency_bar = 0
                    total_bar[str(u)] = {
                        'total_data': [total_data_bar],
                        'spend_time': [spend_time_bar],
                        'efficiency': [efficiency_bar],
                        'avg_label_score': [avg_label_score_bar]
                    }
                    avg_score_bar_dict = str(u), avg_label_score_bar
                    user_avg_score_bar.append(avg_score_bar_dict)
                sorted_user_avg_score_bar = sorted(user_avg_score_bar, key=lambda d: d[1])
                for i in sorted_user_avg_score_bar:
                    sorted_user_avg_score_list.append(i[0])

                radar_data = {}
                for u in users:
                    attendance_score_list = []
                    total_data_score_list = []
                    efficiency_score_list = []
                    accuracy_score_list = []
                    proficiency_score_list = []
                    attendance_count = PicData.objects.filter(username=u).filter(created_date__lte=dates[-1]).count()
                    attendance_on_duty = PicData.objects.filter(username=u,is_on_duty=1).filter(created_date__lte=dates[-1]).count()
                    for d in dates:
                        try:
                            attendance = float('%.2f' % (int(attendance_on_duty)/int(attendance_count)))
                            attendance_score_list.append(attendance*10)
                            previous_data = PicData.objects.filter(username=u).filter(created_date__lte=dates[-1])\
                            .aggregate(Sum('total_data'))['total_data__sum']
                            proficiency_score_list.append(proficiency_score(previous_data))
                            total_data_score_list.append(data_score(data_bar.filter(username=u).filter(created_date=d, is_on_duty=1)\
                                .values('total_data').first()['total_data']))
                            efficiency_score_list.append(efficiency_score(data_bar.filter(username=u).filter(created_date=d, is_on_duty=1)\
                                .values('efficiency').first()['efficiency']))
                            accuracy_score_list.append(27)
                        except TypeError as e:
                            pass

                    try:
                        radar_total_data_score = float('%.2f' % (sum(total_data_score_list)/len(total_data_score_list)))
                    except ZeroDivisionError as e:
                        radar_total_data_score = 0
                    try:
                        radar_efficiency_score = float('%.2f' % (sum(efficiency_score_list)/len(efficiency_score_list)))
                    except ZeroDivisionError as e:
                        radar_efficiency_score = 0
                    try:
                        radar_accuracy_score = float('%.2f' % (sum(accuracy_score_list)/len(accuracy_score_list)))
                    except ZeroDivisionError as e:
                        radar_accuracy_score = 0

                    # print(attendance_score_list)
                    # print(total_data_score_list)
                    # print(efficiency_score_list)
                    # print(accuracy_score_list)
                    # print(proficiency_score_list)
                    radar_data[str(u)] = [float('%.2f' % (sum(attendance_score_list)/len(attendance_score_list))), 
                        radar_total_data_score,
                        radar_efficiency_score, 
                        radar_accuracy_score,
                        float('%.2f' % (sum(proficiency_score_list)/len(proficiency_score_list)))
                    ]

                remark_dict = {}
                for u in users:
                    remark_date_dict = {}
                    for d in dates:
                        try:
                            remark_date_dict[str(d)] = data_bar.filter(created_date=d,username=u).values('remark').first()['remark']
                        except Exception as e:
                            remark_date_dict[str(d)] = ""
                        remark_dict[str(u)] = remark_date_dict

                #################Table目前无用###################
                rr = []
                for d in table_data:
                    r = {}
                    r = {
                        'id': d.id,
                        'created_date': d.created_date.strftime("%Y-%m-%d"),
                        'total_data': d.total_data,
                        'spend_time': d.spend_time,
                        'efficiency': d.efficiency,
                        'username': d.username
                    }
                    rr.append(r)
                rr.reverse()
                count = int(len(list(users))/3+1)
                user_count = list(range(0,count))
                return render(request, 'display_score.html', {'username': request.user.username, 'table_data': rr, 'data': ret, 
                    'user': list(users), 'user_avg_score':sorted_user_avg_score_list, 'dates': dates , 'date_range': date_range, 'total_bar': total_bar, 'time_delta': time_delta,
                    'date_begin': date_begin, 'date_end': date_end, 'radar_data': radar_data, 'remark_dict':remark_dict, 
                    'user_count': user_count})
            except Exception as e:
                return render(request, 'display_score.html', {'username': request.user.username})
        else:
            return render(request, 'login.html')

@csrf_exempt
def save_echarts(request):
    if request.is_ajax():
        return dif_modal(request)
    else:
        res_total = download_image('"http://127.0.0.1:8000/pic_data/display_total_data/?flag=total&date_begin=&date_end=&time_delta=8"###echartsTotalData')
        res_total_efficiency = download_image('"http://127.0.0.1:8000/pic_data/display_total_data/?flag=total&date_begin=&date_end=&time_delta=8"###echartsTotalEfficiencyData')
        res_avg_score = download_image('"http://127.0.0.1:8000/pic_data/display_score/?flag=score&date_begin=&date_end=&time_delta=8"###echartsAvgScoreData')
        res_super_avg_total = download_image('"http://127.0.0.1:8000/pic_data/display_superuser_data/?flag=super&date_begin=&date_end=&time_delta=8"###echartsSuperAvgTotalData')
        if res_total == 0 and res_total_efficiency == 0 and res_avg_score == 0 and res_super_avg_total == 0:
            if send_util():
                return HttpResponse('send_mail_ok')
            else:
                return HttpResponse('send_mail_error')
        else:
            return HttpResponse('save_echarts_error')

def export_excel(request):
    wb = xlwt.Workbook(encoding='utf-8')
    style_heading = xlwt.easyxf("""
        font:
            name Arial,
            colour_index white,
            bold on,
            height 0xA0;
        align:
            wrap off,
            vert center,
            horiz center;
        pattern:
            pattern solid,
            fore-colour 0x19;
        borders:
            left THIN,
            right THIN,
            top THIN,
            bottom THIN;
        """
                                )
    style_body = xlwt.easyxf("""
        font:
            name Arial,
            bold off,
            height 0XA0;
        align:
            wrap on,
            vert center,
            horiz left;
        borders:
            left THIN,
            right THIN,
            top THIN,
            bottom THIN;
        """
                             )
    style_green = xlwt.easyxf(" pattern: pattern solid,fore-colour 0x11;")
    style_red = xlwt.easyxf(" pattern: pattern solid,fore-colour 0x0A;")
    fmts = [
        'M/D/YY',
        'D-MMM-YY',
        'D-MMM',
        'MMM-YY',
        'h:mm AM/PM',
        'h:mm:ss AM/PM',
        'h:mm',
        'h:mm:ss',
        'M/D/YY h:mm',
        'mm:ss',
        '[h]:mm:ss',
        'mm:ss.0',
    ]
    style_body.num_format_str = fmts[0]

    sheet_name = u'标注总量统计'
    sheet_first = wb.add_sheet(sheet_name)
    sheet_first.write(0, 0, u'日期', style_heading)
    sheet_first.write(0, 1, u'总量', style_heading)

    date_begin = request.GET.get('date_begin')
    date_end = request.GET.get('date_end')
    time_delta = request.GET.get('time_delta')
    date_begin_sql = PicData.objects.values('created_date').distinct().order_by('created_date').first()['created_date'].strftime("%Y-%m-%d")
    date_end_sql = PicData.objects.values('created_date').distinct().order_by('created_date').last()['created_date'].strftime("%Y-%m-%d")
    if date_begin == "" and date_end == "":
        if time_delta:
            now = datetime.now()
            now_delta = now + timedelta(days=-(int(time_delta)-1))
            data = PicData.objects.filter(created_date__gte=now_delta).filter(created_date__lte=now)\
            .values('created_date').distinct().order_by('created_date')
        else:
            data = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end_sql)\
            .values('created_date').distinct().order_by('created_date')
    elif date_begin == "":
        data = PicData.objects.filter(created_date__gte=date_begin_sql).filter(created_date__lte=date_end)\
        .values('created_date').distinct().order_by('created_date')
    elif date_end == "":
        data = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end_sql)\
        .values('created_date').distinct().order_by('created_date')
    else:
        data = PicData.objects.filter(created_date__gte=date_begin).filter(created_date__lte=date_end)\
        .values('created_date').distinct().order_by('created_date')
    date_list = []
    total_data_list = []
    avg_total_data_list = []
    rr = []
    for d in data:
        date_list.append(d['created_date'].strftime("%Y-%m-%d"))
    for date in date_list:
        r = {}
        total_data = PicData.objects.filter(created_date=date).aggregate(Sum('total_data'))['total_data__sum']
        total_data_list.append(total_data)
        avg_total_data_list.append(total_data)

        r = {
            'created_date': date,
            'total_data': total_data,
        }
        rr.append(r)
    rr.reverse()
    avg_total_data_list.sort()
    avg_total_data = custom_avg(avg_total_data_list)

    row = 1
    for content in rr:
        sheet_first.write(row, 0, content['created_date'], style_body)
        sheet_first.write(row, 1, str(content['total_data']), style_body)

        sheet_first.col(0).width = 100 * 50
        sheet_first.col(1).width = 100 * 50
        row += 1
    sheet_first.write(row, 0, u'基准值', style_body)
    sheet_first.write(row, 1, str(avg_total_data), style_body)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment;filename=total.xls'
    response.write(output.getvalue())
    return response