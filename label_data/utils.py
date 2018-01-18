import os
import json
import base64
import datetime
import logging

from PIL import Image
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib import auth
from django.db.models import Avg, Max, Min, Count, Sum
from django.conf import settings
from email.mime.image import MIMEImage
from django.core import mail

from .models import LabelData

logger = logging.getLogger('wms.wms_app.utils')

#分数计算公式
# def attendance_score(attendance):
#     return 10

def data_score(data):
    # print("data:" + str(data))
    if float(data) < 1000:
        data_score = float('%.2f' % (float(data)/1000*60*0.3))
    elif 1000 <= float(data) < 1800:
        data_score = float('%.2f' % ((60+((float(data)-1000)/(1800-1000))*40)*0.3))
    else:
        data_score = 30
    # print("data_score:" + str(data_score))
    return data_score

def efficiency_score(efficiency):
    # print("efficiency:" + str(efficiency))
    if float(efficiency) < 130:
        efficiency_score = float('%.2f' % (float(efficiency)/130*60*0.2))
    elif 130 <= float(efficiency) < 220:
        efficiency_score = float('%.2f' % ((60+((float(efficiency)-130)/(220-130))*40)*0.2))
    else:
        efficiency_score = 20
    # print("efficiency_score:" + str(efficiency_score))
    return efficiency_score

def accuracy_score(accuracy):
    # print("accuracy:" + str(accuracy))
    return accuracy

def proficiency_score(proficiency):
    # print("proficiency:" + str(proficiency))
    if float(proficiency) < 20000:
        proficiency_score = float('%.2f' % (float(proficiency)/20000*100*0.1))
    else:
        proficiency_score = 10
    # print("proficiency_score:" + str(proficiency_score))
    return proficiency_score

def score(attendance, data, efficiency, accuracy, proficiency):
    return float('%.2f' % (attendance + data_score(data) + efficiency_score(efficiency) + 
        accuracy_score(accuracy) + proficiency_score(proficiency)))

def custom_avg(data_list):
    try:
        if len(data_list) < 4:
            return float('%.2f' % (sum(data_list)/len(data_list)))
        else:
            part = int(len(data_list)/4)
            new_data_list = data_list[part+1:-part]
            return float('%.2f' % (sum(new_data_list)/len(new_data_list)))
    except ZeroDivisionError as e:
        return 0


def dif_modal(request):
    modal_name = request.POST.get('modal_name')
    if modal_name == "searchDateModal":
        return search_date(request)
    elif modal_name == "chgPassModal":
        return change_password(request)
    elif modal_name == "addDateModal":
        return add_data(request)
    elif modal_name == "editDateModal":
        return edit_data(request)
    elif modal_name == "delDateModal":
        return del_data(request)
    elif modal_name == "echartsSuperData":
        return save_pic(request, "super")
    elif modal_name == "echartsTotalData":
        return save_pic(request, "total")
    elif modal_name == "echartsTotalEfficiencyData":
        return save_pic(request, "efficiency")
    elif modal_name == "echartsAvgScoreData":
        return save_pic(request, "avg_score")
    elif modal_name == "echartsSuperAvgTotalData":
        return save_pic(request, "super_avg_total")

def search_date(request):
    flag = request.GET.get('flag')
    date_begin = request.POST.get('created_date_begin')
    date_end = request.POST.get('created_date_end')
    if_total_data = request.POST.get('if_total_data')
    time_delta = request.POST.get('created_date_delta')
    try:
        if not time_delta:
            time_delta = 10
        else:
            int(time_delta)
    except ValueError as e:
        return HttpResponse(json.dumps({'status':'fail', 'id':'created_date_delta_error', 'content':'●天数不能为非整数'}))

    if if_total_data == "on":
        time_delta = ""

    if flag == "super":
        return HttpResponse(json.dumps({'status':'success', 'content':'/display_superuser_data/?flag=super&date_begin=' + date_begin + '&date_end=' + date_end
            + '&time_delta=' + str(time_delta)}))
    elif flag == "total":
        return HttpResponse(json.dumps({'status':'success', 'content':'/display_total_data/?flag=total&date_begin=' + date_begin + '&date_end=' + date_end
            + '&time_delta=' + str(time_delta)}))
    elif flag == "score":
        return HttpResponse(json.dumps({'status':'success', 'content':'/display_score/?flag=score&date_begin=' + date_begin + '&date_end=' + date_end
            + '&time_delta=' + str(time_delta)}))
    else:
        return HttpResponse(json.dumps({'status':'success', 'content':'/display_commonuser_data/?flag=common&date_begin=' + date_begin + '&date_end=' + date_end
            + '&time_delta=' + str(time_delta)}))

def change_password(request):
    username = request.user.username
    user_form = request.POST
    old_password = user_form.get('old_password')
    password1 = user_form.get('password1')
    password2 = user_form.get('password2')
    user = auth.authenticate(username=username, password=old_password)
    if user is not None and user.is_active:
        if password1 == "" or password2 == "":
            return HttpResponse(json.dumps({'status':'fail', 'id':'new_password_error', 'content':'●新密码不能为空'}))
        elif password1 == password2:
            u = User.objects.get(username__exact=username)
            u.set_password(password1)
            u.save()
            return HttpResponse(json.dumps({'status':'success', 'content':'/login'}))
        else:
            return HttpResponse(json.dumps({'status':'fail', 'id':'new_password_error', 'content':'●密码不一致'}))
    else:
        return HttpResponse(json.dumps({'status':'fail', 'id':'old_password_error', 'content':'●旧密码错误'}))

def add_data(request):
    remark_flag = 0
    date_begin = request.GET.get('date_begin')
    date_end = request.GET.get('date_end')
    time_delta = request.GET.get('time_delta')
    is_on_duty = request.POST.get('is_on_duty')
    created_date = request.POST.get('created_date')
    total_data = request.POST.get('total_data')
    spend_time = request.POST.get('spend_time')
    remark = request.POST.get('remark')
    attendance_count = LabelData.objects.filter(username=request.user.username).count()
    attendance_on_duty = LabelData.objects.filter(username=request.user.username,is_on_duty=1).count()
    if is_on_duty == "on":
        if not created_date:
            return HttpResponse(json.dumps({'status':'fail', 'id':'add_date_error', 'content':'●日期不能为空'}))
        elif not total_data:
            return HttpResponse(json.dumps({'status':'fail', 'id':'add_data_error', 'content':'●总量不能为空'}))
        elif not spend_time:
            return HttpResponse(json.dumps({'status':'fail', 'id':'add_time_error', 'content':'●耗时不能为空'}))
        else:
            try:
                int(total_data)
            except ValueError as e:
                return HttpResponse(json.dumps({'status':'fail', 'id':'add_data_error', 'content':'●总量不能为非整数'}))
            try:
                float(spend_time)
            except ValueError as e:
                return HttpResponse(json.dumps({'status':'fail', 'id':'add_time_error', 'content':'●耗时不能为非数字'}))
            if not int(total_data):
                return HttpResponse(json.dumps({'status':'fail', 'id':'add_data_error', 'content':'●总量不能为0'}))
            elif not float(spend_time):
                return HttpResponse(json.dumps({'status':'fail', 'id':'add_time_error', 'content':'●耗时不能为0'}))
            else:
                data_count = LabelData.objects.filter(username=request.user.username,created_date=created_date).count()
                if data_count:
                    return HttpResponse(json.dumps({'status':'fail', 'id':'add_date_error', 'content':'●已经有该日期的数据'}))
                else:
                    # sum_total = 1200
                    # sum_efficiency = 150
                    sum_total_list = []
                    sum_total = LabelData.objects.values_list('total_data')
                    for i in sum_total:
                        sum_total_list.append(i[0])
                    sum_total_list.sort()
                    sum_total_base = custom_avg(sum_total_list)

                    sum_efficiency_list = []
                    sum_efficiency = LabelData.objects.values_list('efficiency')
                    for i in sum_efficiency:
                        sum_efficiency_list.append(i[0])
                    sum_efficiency_list.sort()
                    sum_efficiency_base = custom_avg(sum_efficiency_list)
                    # print(sum_total_base,sum_efficiency_base)
                    
                    efficiency = float('%.2f' % (int(total_data)/float(spend_time)))
                    if int(total_data) < sum_total_base and efficiency < sum_efficiency_base:
                        if remark == "":
                            return HttpResponse(json.dumps({'status':'fail', 'id':'add_remark_error', 'content':'●总量低于平均总量\
                                且效率低于平均效率，请在备注中说明理由(最长20字)'}))
                        remark_flag = 3
                    elif int(total_data) < sum_total_base:
                        if remark == "":
                            return HttpResponse(json.dumps({'status':'fail', 'id':'add_remark_error', 'content':'●总量低于平均总量\
                                ，请在备注中说明理由(最长20字)'}))
                        remark_flag = 1
                    elif efficiency < sum_efficiency_base:
                        if remark == "":
                            return HttpResponse(json.dumps({'status':'fail', 'id':'add_remark_error', 'content':'●效率低于平均效率\
                                ，请在备注中说明理由(最长20字)'}))
                        remark_flag = 2

                    if len(remark) > 20:
                        return HttpResponse(json.dumps({'status':'fail', 'id':'add_remark_error', 'content':'●备注超过20字'}))
                    try:
                        previous_data = LabelData.objects.filter(username=request.user.username).filter(created_date__lt=created_date)\
                        .aggregate(Sum('total_data'))['total_data__sum'] + int(total_data)
                    except TypeError as e:
                        previous_data = int(total_data)
                    attendance = float('%.2f' % ((int(attendance_on_duty)+1)/(int(attendance_count)+1)))
                    user_score = score(attendance*10, total_data, efficiency, 27, previous_data)
                    LabelData.objects.create(created_date=created_date, total_data=total_data, spend_time=spend_time, 
                        efficiency=efficiency, username=request.user.username, label_score=user_score, is_on_duty=1, remark=remark,
                        remark_flag = remark_flag)
                    logger.info(request.user.username + "-create-LabelData(" + str(created_date) + "," + str(total_data) + "," +\
                        str(spend_time) + "," + str(efficiency) + "," + str(request.user.username) + "," + str(user_score) + "," +\
                        str(1) + "," + str(remark) + "," + str(remark_flag) + ")")
    else:
        if not created_date:
            return HttpResponse(json.dumps({'status':'fail', 'id':'add_date_error', 'content':'●日期不能为空'}))
        else:
            data_count = LabelData.objects.filter(username=request.user.username,created_date=created_date).count()
            if data_count:
                return HttpResponse(json.dumps({'status':'fail', 'id':'add_date_error', 'content':'●已经有该日期的数据'}))
            else:
                if len(remark) > 20:
                    return HttpResponse(json.dumps({'status':'fail', 'id':'add_remark_error', 'content':'●备注超过20字'}))
                LabelData.objects.create(created_date=created_date, total_data=0, spend_time=0, 
                    efficiency=0, username=request.user.username, label_score=0, is_on_duty=0, remark=remark, remark_flag=3)
                logger.info(request.user.username + "-create-LabelData(" + str(created_date) + "," + str(0) + "," +\
                        str(0) + "," + str(0) + "," + str(request.user.username) + "," + str(0) + "," +\
                        str(0) + "," + str(remark) + "," + str(3) + ")")
    return HttpResponse(json.dumps({'status':'success', 'content':'/display_commonuser_data/?flag=common&date_begin='+date_begin+'&date_end='+date_end+
        '&time_delta='+time_delta}))

def edit_data(request):
    remark_flag = 0
    date_begin = request.GET.get('date_begin')
    date_end = request.GET.get('date_end')
    time_delta = request.GET.get('time_delta')
    nid = request.POST.get('data_id')
    obj = LabelData.objects.filter(id=nid).first()
    obj_id = obj.id
    created_date_id = obj.created_date.strftime("%Y-%m-%d")
    is_on_duty = request.POST.get('is_on_duty')
    created_date = request.POST.get('created_date')
    total_data = request.POST.get('total_data')
    spend_time = request.POST.get('spend_time')
    remark = request.POST.get('remark')
    attendance_count = LabelData.objects.filter(username=request.user.username).count()
    attendance_on_duty = LabelData.objects.filter(username=request.user.username,is_on_duty=1).count()
    if is_on_duty == "on":
        if not created_date:
            return HttpResponse(json.dumps({'status':'fail', 'id':'edit_date_error', 'content':'●日期不能为空'}))
        elif not total_data:
            return HttpResponse(json.dumps({'status':'fail', 'id':'edit_data_error', 'content':'●总量不能为空'}))
        elif not spend_time:
            return HttpResponse(json.dumps({'status':'fail', 'id':'edit_time_error', 'content':'●耗时不能为空'}))
        else:
            try:
                int(total_data)
            except ValueError as e:
                return HttpResponse(json.dumps({'status':'fail', 'id':'edit_data_error', 'content':'●总量不能为非整数'}))
            try:
                float(spend_time)
            except ValueError as e:
                return HttpResponse(json.dumps({'status':'fail', 'id':'edit_time_error', 'content':'●耗时不能为非数字'}))

            if not int(total_data):
                return HttpResponse(json.dumps({'status':'fail', 'id':'edit_data_error', 'content':'●总量不能为0'}))
            elif not float(spend_time):
                return HttpResponse(json.dumps({'status':'fail', 'id':'edit_time_error', 'content':'●耗时不能为0'}))
            else:
                if created_date_id != created_date:
                    data_count = LabelData.objects.filter(username=request.user.username,created_date=created_date).count()
                    if data_count:
                        return HttpResponse(json.dumps({'status':'fail', 'id':'edit_date_error', 'content':'●已经有该日期的数据'}))
                # sum_total = 1200
                # sum_efficiency = 150
                sum_total_list = []
                sum_total = LabelData.objects.values_list('total_data')
                for i in sum_total:
                    sum_total_list.append(i[0])
                sum_total_list.sort()
                sum_total_base = custom_avg(sum_total_list)

                sum_efficiency_list = []
                sum_efficiency = LabelData.objects.values_list('efficiency')
                for i in sum_efficiency:
                    sum_efficiency_list.append(i[0])
                sum_efficiency_list.sort()
                sum_efficiency_base = custom_avg(sum_efficiency_list)
                # print(sum_total_base,sum_efficiency_base)

                efficiency = float('%.2f' % (int(total_data)/float(spend_time)))
                if int(total_data) < sum_total_base and efficiency < sum_efficiency_base:
                    if remark == "":
                        return HttpResponse(json.dumps({'status':'fail', 'id':'edit_remark_error', 'content':'●总量低于平均总量\
                            且效率低于平均效率，请在备注中说明理由(最长20字)'}))
                    remark_flag = 3
                elif int(total_data) < sum_total_base:
                    if remark == "":
                        return HttpResponse(json.dumps({'status':'fail', 'id':'edit_remark_error', 'content':'●总量低于平均总量\
                            ，请在备注中说明理由(最长20字)'}))
                    remark_flag = 1
                elif efficiency < sum_efficiency_base:
                    if remark == "":
                        return HttpResponse(json.dumps({'status':'fail', 'id':'edit_remark_error', 'content':'●效率低于平均效率\
                            ，请在备注中说明理由(最长20字)'}))
                    remark_flag = 2
                if len(remark) > 20:
                    return HttpResponse(json.dumps({'status':'fail', 'id':'edit_remark_error', 'content':'●备注超过20字'}))
                try:
                    previous_data = LabelData.objects.filter(username=request.user.username).filter(created_date__lt=created_date)\
                    .aggregate(Sum('total_data'))['total_data__sum'] + int(total_data)
                except TypeError as e:
                    previous_data = int(total_data)
                attendance = float('%.2f' % ((int(attendance_on_duty)+1)/(int(attendance_count)+1)))
                user_score = score(attendance*10, total_data, efficiency, 27, previous_data)
                LabelData.objects.filter(id=nid).update(created_date=created_date, total_data=total_data, 
                    spend_time=spend_time, efficiency=efficiency, label_score=user_score, is_on_duty=1, remark=remark,
                    remark_flag=remark_flag)
                logger.info(request.user.username + "-update-LabelData("+ str(nid) + ","  + str(created_date) + "," + str(total_data) + "," +\
                        str(spend_time) + "," + str(efficiency) + "," + str(user_score) + "," + str(1) + "," +\
                        str(remark) + "," + str(remark_flag) + ")")
    else:
        if not created_date:
            return HttpResponse(json.dumps({'status':'fail', 'id':'edit_date_error', 'content':'●日期不能为空'}))
        else:
            if created_date_id != created_date:
                data_count = LabelData.objects.filter(username=request.user.username,created_date=created_date).count()
                if data_count:
                    return HttpResponse(json.dumps({'status':'fail', 'id':'edit_date_error', 'content':'●已经有该日期的数据'}))
                else:
                    if len(remark) > 20:
                        return HttpResponse(json.dumps({'status':'fail', 'id':'edit_remark_error', 'content':'●备注超过20字'}))
            LabelData.objects.filter(id=nid).update(created_date=created_date, total_data=0, 
                spend_time=0, efficiency=0, label_score=0, is_on_duty=0, remark=remark, remark_flag=3)
            logger.info(request.user.username + "-update-LabelData("+ str(nid) + "," + str(created_date) + "," + str(0) + "," +\
                        str(0) + "," + str(0) + "," + str(0) + "," + str(0) + "," +\
                        str(remark) + "," + str(3) + ")")
    return HttpResponse(json.dumps({'status':'success', 'content':'/display_commonuser_data/?flag=common&date_begin='+date_begin+'&date_end='+date_end+
        '&time_delta='+time_delta}))

def del_data(request):
    date_begin = request.GET.get('date_begin')
    date_end = request.GET.get('date_end')
    time_delta = request.GET.get('time_delta')
    nid = request.POST.get('data_id')
    LabelData.objects.filter(id=nid).delete()
    logger.info(request.user.username + "-delete-LabelData(" + str(nid) + ")")
    return HttpResponse(json.dumps({'status':'success', 'content':'/display_commonuser_data/?flag=common&date_begin='+date_begin+'&date_end='
        +date_end+'&time_delta='+time_delta}))

def save_pic(request, pic_name):
    date = datetime.datetime.now().strftime('%Y-%m-%d_%H')
    pic_info = request.POST.get('picInfo')
    pic = pic_info.replace(" ","+").split("base64,")[1]
    imgdata=base64.b64decode(pic)
    path = os.getcwd()
    path_use = path.replace('\\', '/')
    file=open(path_use + '/mail_util/' + pic_name + '_' + date + '.png','wb')
    file.write(imgdata)
    file.close()
    sImg=Image.open(path_use + '/mail_util/' + pic_name + '_' + date + '.png')
    w,h=sImg.size
    dImg=sImg.resize((w,h),Image.ANTIALIAS)  #设置压缩尺寸和选项，注意尺寸要用括号
    dImg.save(path_use + '/mail_util/' + pic_name + '_' + date + '.png')

def download_image(url):
    path = os.getcwd()
    path_use = path.replace('\\', '/')
    cmd = "phantomjs " + path_use + "/static/js/echarts_load.js " + url
    p = os.system(cmd)
    return p

def add_img(src, img_id):
    """
    在富文本邮件模板里添加图片
    :param src:
    :param img_id:
    :return:
    """
    fp = open(src, 'rb')
    msg_image = MIMEImage(fp.read())
    fp.close()
    msg_image.add_header('Content-ID', '<'+img_id+'>')
    return msg_image
  
def send_util():
    date = datetime.datetime.now().strftime('%Y-%m-%d_%H')
    date_day = datetime.datetime.now()
    now_delta = date_day + datetime.timedelta(days=-(int(8)-1))
    path = os.getcwd()
    path_use = path.replace('\\', '/')
    avg_score_list = []
    user_list = []
    date_list = []
    # data = LabelData.objects.filter(created_date__gte='2017-07-03').filter(created_date__lte='2017-07-09')
    data = LabelData.objects.filter(created_date__gte=now_delta).filter(created_date__lte=date_day)
    dates = data.values('created_date').distinct().order_by('created_date')
    for d in dates:
        date_list.append(d['created_date'].strftime("%Y-%m-%d"))
    users = data.values('username').distinct()
    total_data_week = int(data.aggregate(Sum('total_data'))['total_data__sum'])
    if total_data_week >= 4200*5:
        total_data_week_diff = "本周超出标准总量" + str(total_data_week - 4200*5) + "条。"
    else:
        total_data_week_diff = "本周低于标准总量" + str(4200*5 - total_data_week) + "条。"
    remarks = ""

    total_data_list = []
    avg_total_data_list = []
    for d in date_list:
        total_data_dict = {}
        total_data = LabelData.objects.filter(created_date=d).aggregate(Sum('total_data'))['total_data__sum']
        avg_total_data_list.append(total_data)
        total_data_dict[d] = total_data
        total_data_list.append(total_data_dict)
    avg_total_data_list.sort()
    avg_total_data = custom_avg(avg_total_data_list)
    user_remark_list = ""
    for i in total_data_list:
        if int(list(i.values())[0]) < avg_total_data:
            user = LabelData.objects.filter(created_date=list(i.keys())[0]).values('username', 'remark', 'remark_flag')
            user_remark_list += "<strong>" + list(i.keys())[0] + "</strong></br>"
            for u in user:
                user_remark_list += u['username'] + "：" + u['remark'] + "</br>"
    user_remark = "<font color='red'>总量低于平均值说明：</font><br/>" + user_remark_list

    for i in users:
        attendance_score_list = []
        proficiency_score_list = []
        total_data_score_list = []
        efficiency_score_list = []
        accuracy_score_list = []
        avg_user_score= float('%.2f' % (data.filter(username=i['username']).aggregate(Avg('label_score'))['label_score__avg']))
        if avg_user_score < 70:
            # attendance_count = LabelData.objects.filter(username=i['username']).filter(created_date__lte='2017-07-09').count()
            # attendance_on_duty = LabelData.objects.filter(username=i['username'],is_on_duty=1).filter(created_date__lte='2017-07-09').count()
            attendance_count = LabelData.objects.filter(username=i['username']).filter(created_date__lte=date_list[-1]).count()
            attendance_on_duty = LabelData.objects.filter(username=i['username'],is_on_duty=1).filter(created_date__lte=date_list[-1]).count()
            for d in date_list:
                try:
                    attendance = float('%.2f' % (int(attendance_on_duty)/int(attendance_count)))
                    attendance_score_list.append(attendance*10)
                    # previous_data = LabelData.objects.filter(username=i['username']).filter(created_date__lte='2017-07-09')\
                    # .aggregate(Sum('total_data'))['total_data__sum']
                    previous_data = LabelData.objects.filter(username=i['username']).filter(created_date__lte=date_list[-1])\
                    .aggregate(Sum('total_data'))['total_data__sum']
                    proficiency_score_list.append(proficiency_score(previous_data))
                    total_data_score_list.append(data_score(data.filter(username=i['username']).filter(created_date=d, is_on_duty=1)\
                        .values('total_data').first()['total_data']))
                    efficiency_score_list.append(efficiency_score(data.filter(username=i['username']).filter(created_date=d, is_on_duty=1)\
                        .values('efficiency').first()['efficiency']))
                    accuracy_score_list.append(27)
                except TypeError as e:
                    pass
            try:
                radar_attendance_score = float('%.2f' % (sum(attendance_score_list)/len(attendance_score_list)))
            except ZeroDivisionError as e:
                radar_attendance_score = 0
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
            try:
                radar_proficiency_score = float('%.2f' % (sum(proficiency_score_list)/len(proficiency_score_list)))
            except ZeroDivisionError as e:
                radar_proficiency_score = 0
            remark = "<font color='red'>得分低于70分人员："+ i['username'] + "</font><br/>" + "得分情况：<br/>" + "出勤率得分：" + str(radar_attendance_score) +\
            "(满分10)<br/>" + "完成量得分：" + str(radar_total_data_score) + "(满分30)<br/>" + "效率得分：" + str(radar_efficiency_score) +\
            "(满分20)<br/>" + "准确率得分：" + str(radar_accuracy_score) + "(满分30)<br/>" + "熟练度得分：" + str(radar_proficiency_score) +\
            "(满分10)<br/>"
        else:
            remark = ""
        remarks += remark
    
    remarks += user_remark
    remarks += "<br/>平台链接：http://10.81.9.93:8000/<br/>用户名/密码：admin/123456<br/><br/>\
    <strong><font color='blue'>本邮件由系统自动发送</font></strong><br/>"
    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Title</title>
    </head>
    <body>
    本周标注总量：'''+ str(total_data_week) +'''<br/>按合计大连提供3人力标准4200条/天对比，每周标准21000条，'''\
    + total_data_week_diff +'''<br/>
    <img src="cid:test_cid_total"/><br/>
    本周标注效率<br/>
    <img src="cid:test_cid_efficiency"/><br/>
    本周标注人员平均得分<br/>
    <img src="cid:test_cid_avg_score"/><br/>
    本周标注人员标注平均总量<br/>
    <img src="cid:test_cid_avg_total"/><br/>
    备注说明：<br/>''' + remarks +'''
    </body>
    </html>
    '''
    recipient_list = ['sawyersun@21kunpeng.com']
    from_mail = settings.EMAIL_HOST_USER
    msg = mail.EmailMessage('标注数据统计信息', html, from_mail, recipient_list)
    msg.content_subtype = 'html'
    msg.encoding = 'utf-8'
    image = add_img(path_use + '/mail_util/total_' + date + '.png', 'test_cid_total')
    image1 = add_img(path_use+'/mail_util/efficiency_' + date + '.png', 'test_cid_efficiency')
    image2 = add_img(path_use+'/mail_util/avg_score_' + date + '.png', 'test_cid_avg_score')
    image3 = add_img(path_use+'/mail_util/super_avg_total_' + date + '.png', 'test_cid_avg_total')
    msg.attach(image)
    msg.attach(image1)
    msg.attach(image2)
    msg.attach(image3)
    if msg.send():
        return True
    else:
        return False