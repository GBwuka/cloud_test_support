import os
import shutil
import urllib.request
from celery import task

@task()
def email():
    urllib.request.urlopen("http://127.0.0.1:8000/label_data/save_echarts/")