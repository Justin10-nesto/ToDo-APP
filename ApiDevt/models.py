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
        db_table = "task_category"

class Task(models.Model):
    PRIORITY_CHOICES = [
        ("Low", "Low"),
        ("Medium", "Medium"),
        ("High", "High"),
    ]

    RECURRING_CHOICES = [
        ("None", "None"),
        ("Daily", "Daily"),
        ("Weekly", "Weekly"),
        ("Monthly", "Monthly"),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=255)
    start_date = models.DateField()
    start_time = models.TimeField()
    end_date = models.DateField()
    end_time = models.TimeField()
    is_notified = models.BooleanField(default=False)
    is_expired = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)  # Soft deletion
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="Medium")
    recurring = models.CharField(max_length=10, choices=RECURRING_CHOICES, default="None")  # Recurring tasks
    progress = models.PositiveIntegerField(default=0)  # Progress tracking (0-100%)
    reminder_time = models.TimeField(null=True, blank=True)  # Custom reminder time
    assigned_user = models.ForeignKey(User, related_name="assigned_tasks", on_delete=models.CASCADE)
    collaborators = models.ManyToManyField(User, related_name="collaborated_tasks", blank=True)  # Collaborators
    category = models.ForeignKey("TaskCategory", related_name="tasks", on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField("Tag", related_name="tasks", blank=True)  # Tags for organization
    attachments = models.FileField(upload_to="task_attachments/", null=True, blank=True)  # File attachments
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def check_expired_tasks(self):
        """
        Mark tasks as expired if the current time is past their end time.
        """
        tasks_to_expire = Task.objects.filter(is_expired=False, is_deleted=False, end_date__lte=datetime.date.today())
        current_time = datetime.datetime.now()

        for task in tasks_to_expire:
            task_end_datetime = datetime.datetime.combine(task.end_date, task.end_time)
            if current_time > task_end_datetime:
                task.is_expired = True

        Task.objects.bulk_update(tasks_to_expire, ["is_expired"])
        return Task.objects.filter(is_expired=True)

    def send_notifications(self):
        """
        Send email notifications for tasks starting soon.
        """
        tasks_to_notify = Task.objects.filter(is_expired=False, is_notified=False, is_deleted=False)
        current_time = datetime.datetime.now()

        for task in tasks_to_notify:
            task_start_datetime = datetime.datetime.combine(task.start_date, task.start_time)
            reminder_datetime = task_start_datetime - datetime.timedelta(hours=1)

            if current_time >= reminder_datetime:
                email = task.assigned_user.email
                header = "Task Reminder"
                message = (
                    f"Dear {task.assigned_user.first_name} {task.assigned_user.last_name},\n\n"
                    f"Your task '{task.name}' is scheduled to start soon at {task.start_date} {task.start_time}.\n\n"
                    "Please make sure to prepare accordingly."
                )
                email_from = settings.EMAIL_HOST_USER
                send_mail(header, message, email_from, [email])

                task.is_notified = True

        Task.objects.bulk_update(tasks_to_notify, ["is_notified"])
        return "Notifications sent to all users."

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Task"
        db_table = "task"


class Tag(models.Model):
    """
    Tag model for organizing tasks.
    """
    name = models.CharField(max_length=50, unique=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "tag"
        db_table = "tag"