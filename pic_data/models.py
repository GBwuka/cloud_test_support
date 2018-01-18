from django.db import models
from django.contrib.auth.models import User


class PicData(models.Model):
    created_date = models.DateField()
    total_data = models.IntegerField(default=0)
    spend_time = models.FloatField(default=0)
    efficiency = models.FloatField(default=0)
    username = models.CharField(max_length=50)
    label_score = models.FloatField(default=0)
    is_on_duty = models.BooleanField(default=1)
    remark = models.CharField(max_length=50)
    remark_flag = models.IntegerField(default=0)
    # efficiency_remark = models.CharField(max_length=50)
    # user = models.ForeignKey(User)
    # username = models.CharField(max_length=30)

    class Meta:
        db_table = 'pic_data'
