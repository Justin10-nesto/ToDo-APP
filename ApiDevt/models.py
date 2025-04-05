import datetime
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail

# Create your models here.
    
class OtpCode(models.Model):
    code = models.CharField(max_length=100)
    is_used = models.BooleanField(default = False)
    user = models.ForeignKey(User, on_delete= models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def get_status(self):
        date = datetime.datetime(self.date_created.year, self.date_created.month, self.date_created.day, self.date_created.hour +3, self.date_created.minute, self.date_created.second)

        if date > self.date_created:
            return 'Valid'
        else:
            return 'Invalid'

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "OtpCode"
        db_table = "OtpCode"

class TaskCategory(models.Model):
    name = models.CharField(max_length=100)
    # created_by = models.ForeignKey(User, related_name='created_by', on_delete=models.CASCADE)
    # update_by = models.ForeignKey(User, related_name='updated_by', on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Task Category"
        db_table = "Task Category"

class Task(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=255) 
    start_date = models.DateField() 
    start_time = models.TimeField() 
    end_date = models.DateTimeField()
    end_time = models.TimeField()
    is_notified = models.BooleanField(default=False)
    is_expired = models.BooleanField(default=False)
    assigned_user = models.ForeignKey(User, related_name='assigned_user', on_delete=models.CASCADE)
    # created_by = models.ForeignKey(User, related_name='created_by', on_delete=models.CASCADE)
    # update_by = models.ForeignKey(User, related_name='updated_by', on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def checking_expiredTask(self):
        tasks = Task.objects.filter(is_expired = False)
        if tasks.exists():
            for task in tasks:
                current_time = datetime.datetime.now()
                end_date = datetime.datetime(self.end_date.year, self.end_date.month, self.end_date.day, self.end_date.hour - 1, self.end_time.minute, self.end_time.second)

                if current_time > end_date:
                    tasks.is_expired = True
                    tasks.save()
        return Task.objects.all()
    
    def semdingNotification(self):
        tasks = Task.objects.filter(is_expired = False, is_notified = True)
        if tasks.exists():
            for task in tasks:
                current_time = datetime.datetime.now()
                start_delay = datetime.datetime(self.start_date.year, self.start_date.month, self.start_date.day, self.start_date.hour - 1, self.start_time.minute, self.start_time.second)
                if current_time >= start_delay:
                    email = self.assigned_user.email
                    header = 'Task Reminder'
                    msg =f"dear {self.assigned_user.first_name} {self.assigned_user.last_name} your taks of {self.name} will start soon at {self.start_date}"
                    email_from = settings.EMAIL_HOST_USER
                    send_mail(header, msg, email_from, email)
                    tasks.is_notified = True
                    tasks.save()
        return 'Notification Sent to all User'
    
    class Meta:
        verbose_name = "Task"
        db_table = "Task"