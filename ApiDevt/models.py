import datetime
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone

# Create your models here.
    
class OtpCode(models.Model):
    code = models.CharField(max_length=100)
    is_used = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    expiry_time = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Set expiry time to 3 hours after creation if not already set
        if not self.expiry_time:
            self.expiry_time = timezone.now() + datetime.timedelta(hours=3)
        super().save(*args, **kwargs)

    def get_status(self):
        if self.is_used:
            return 'Used'
        elif timezone.now() > self.expiry_time:
            return 'Expired'
        else:
            return 'Valid'

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
    STATUS_CHOICES = [
        ("Not Started", "Not Started"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
        ("On Hold", "On Hold"),
        ("Cancelled", "Cancelled"),
    ]
    
    PRIORITY_CHOICES = [
        ("Low", "Low"),
        ("Medium", "Medium"),
        ("High", "High"),
        ("Urgent", "Urgent"),
    ]

    RECURRING_CHOICES = [
        ("None", "None"),
        ("Daily", "Daily"),
        ("Weekly", "Weekly"),
        ("Monthly", "Monthly"),
        ("Yearly", "Yearly"),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Not Started")
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

    @classmethod
    def check_expired_tasks(cls):
        """
        Mark tasks as expired if the current time is past their end time.
        """
        tasks_to_expire = cls.objects.filter(is_expired=False, is_deleted=False, end_date__lte=datetime.date.today())
        current_time = timezone.now()

        for task in tasks_to_expire:
            task_end_datetime = datetime.datetime.combine(task.end_date, task.end_time)
            if current_time > task_end_datetime:
                task.is_expired = True
                
                # Handle recurring tasks
                if task.recurring != "None":
                    cls.create_recurring_task(task)

        cls.objects.bulk_update(tasks_to_expire, ["is_expired"])
        return cls.objects.filter(is_expired=True)
        
    @classmethod
    def create_recurring_task(cls, original_task):
        """
        Create a new task based on the recurring settings of the original task.
        """
        if original_task.recurring == "Daily":
            next_start_date = original_task.start_date + datetime.timedelta(days=1)
            next_end_date = original_task.end_date + datetime.timedelta(days=1)
        elif original_task.recurring == "Weekly":
            next_start_date = original_task.start_date + datetime.timedelta(weeks=1)
            next_end_date = original_task.end_date + datetime.timedelta(weeks=1)
        elif original_task.recurring == "Monthly":
            # Add one month (approximate)
            next_start_date = original_task.start_date.replace(month=original_task.start_date.month % 12 + 1)
            next_end_date = original_task.end_date.replace(month=original_task.end_date.month % 12 + 1)
            # Handle year change
            if original_task.start_date.month == 12:
                next_start_date = next_start_date.replace(year=original_task.start_date.year + 1)
            if original_task.end_date.month == 12:
                next_end_date = next_end_date.replace(year=original_task.end_date.year + 1)
        elif original_task.recurring == "Yearly":
            next_start_date = original_task.start_date.replace(year=original_task.start_date.year + 1)
            next_end_date = original_task.end_date.replace(year=original_task.end_date.year + 1)
        else:
            return None
            
        # Create new task
        new_task = cls(
            name=original_task.name,
            description=original_task.description,
            status="Not Started",
            start_date=next_start_date,
            start_time=original_task.start_time,
            end_date=next_end_date,
            end_time=original_task.end_time,
            priority=original_task.priority,
            recurring=original_task.recurring,
            progress=0,
            reminder_time=original_task.reminder_time,
            assigned_user=original_task.assigned_user,
            category=original_task.category
        )
        new_task.save()
        
        # Copy tags
        for tag in original_task.tags.all():
            new_task.tags.add(tag)
            
        # Copy collaborators
        for collaborator in original_task.collaborators.all():
            new_task.collaborators.add(collaborator)
            
        return new_task

    @classmethod
    def send_notifications(cls):
        """
        Send email notifications for tasks starting soon.
        """
        tasks_to_notify = cls.objects.filter(is_expired=False, is_notified=False, is_deleted=False)
        current_time = timezone.now()

        for task in tasks_to_notify:
            task_start_datetime = datetime.datetime.combine(task.start_date, task.start_time)
            # Use custom reminder time if set, otherwise default to 1 hour
            if task.reminder_time:
                reminder_hours = task.reminder_time.hour
                reminder_minutes = task.reminder_time.minute
                reminder_datetime = task_start_datetime - datetime.timedelta(hours=reminder_hours, minutes=reminder_minutes)
            else:
                reminder_datetime = task_start_datetime - datetime.timedelta(hours=1)

            if current_time >= reminder_datetime:
                # Notify assigned user
                cls._send_notification_email(task, task.assigned_user)
                
                # Notify collaborators if they have notification preferences enabled
                for collaborator in task.collaborators.all():
                    if hasattr(collaborator, 'userpreference') and collaborator.userpreference.receive_collaboration_notifications:
                        cls._send_notification_email(task, collaborator)

                task.is_notified = True

        cls.objects.bulk_update(tasks_to_notify, ["is_notified"])
        return "Notifications sent to all users."
        
    @staticmethod
    def _send_notification_email(task, user):
        """
        Helper method to send notification email to a user.
        """
        email = user.email
        header = "Task Reminder"
        message = (
            f"Dear {user.first_name} {user.last_name},\n\n"
            f"Your task '{task.name}' is scheduled to start soon at {task.start_date} {task.start_time}.\n\n"
            f"Status: {task.status}\n"
            f"Priority: {task.priority}\n\n"
            "Please make sure to prepare accordingly."
        )
        email_from = settings.EMAIL_HOST_USER
        send_mail(header, message, email_from, [email])

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Task"
        db_table = "task"


class SubTask(models.Model):
    """
    SubTask model for breaking down tasks into smaller components.
    """
    STATUS_CHOICES = [
        ("Not Started", "Not Started"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Not Started")
    parent_task = models.ForeignKey(Task, related_name="subtasks", on_delete=models.CASCADE)
    assigned_user = models.ForeignKey(User, related_name="assigned_subtasks", on_delete=models.CASCADE, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update parent task progress
        self.update_parent_progress()
    
    def update_parent_progress(self):
        parent = self.parent_task
        subtasks = parent.subtasks.all()
        total = subtasks.count()
        if total > 0:
            completed = subtasks.filter(status="Completed").count()
            parent.progress = int((completed / total) * 100)
            parent.save(update_fields=["progress"])
    
    class Meta:
        verbose_name = "SubTask"
        db_table = "subtask"


class Tag(models.Model):
    """
    Tag model for organizing tasks.
    """
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default="#3498db")  # Hex color code
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "tag"
        db_table = "tag"


class UserPreference(models.Model):
    """
    User preferences for the ToDo app.
    """
    THEME_CHOICES = [
        ("Light", "Light"),
        ("Dark", "Dark"),
        ("System", "System"),
    ]
    
    user = models.OneToOneField(User, related_name="userpreference", on_delete=models.CASCADE)
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="System")
    receive_email_notifications = models.BooleanField(default=True)
    receive_collaboration_notifications = models.BooleanField(default=True)
    default_view = models.CharField(max_length=20, default="calendar")  # calendar, list, kanban, etc.
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s preferences"
    
    class Meta:
        verbose_name = "User Preference"
        db_table = "user_preference"