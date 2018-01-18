from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import auth
# logger = logging.getLogger(__name__)

def homepage(request):
    # user = request.user
    # if user is not None and user.is_active:
    #     if user.is_superuser:
    #         return HttpResponseRedirect("label_data/label_super/")
    #         # return render(request, 'label_super.html')
    #     else:
    #         return HttpResponseRedirect("label_data/label/")
            # label_form = LabelForm()
            # return render(request, 'label.html', {'label_form': label_form})
    return render(request, 'login.html')

@csrf_exempt
def login(request):
    if request.method == 'POST':
        user_form = request.POST
        username = user_form.get('username')
        password = user_form.get('password')
        user = auth.authenticate(username=username, password=password)
        if not username:
            return render(request, 'login.html', {'username_error': '●用户名为空'})
        elif user is not None and user.is_active:
            auth.login(request, user)
            if user.is_superuser:
                return render(request, 'display_project.html', {'issuper': 'true'})
            else:
                return render(request, 'display_project.html', {'issuper': 'false'})
        else:
            return render(request, 'login.html', {'password_error': '●密码错误'})
    return render(request, 'login.html')

@login_required
def logout(request):
    auth.logout(request)
    return render(request, 'login.html')

@login_required
def display_project(request):
    if request.user.is_superuser:
        return render(request, 'display_project.html', {'issuper': 'true'})
    else:
        return render(request, 'display_project.html', {'issuper': 'false'})