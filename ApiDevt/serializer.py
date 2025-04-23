from rest_framework import serializers, exceptions
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
import datetime
from drf_spectacular.utils import extend_schema_field
from typing import Dict, Any, Union, List, Optional
from ApiDevt.models import Task, TaskCategory, OtpCode, SubTask, Tag, UserPreference


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            raise exceptions.ValidationError("Username and password are required.")

        user = authenticate(username=username, password=password)
        if user:
            if not user.is_active:
                raise exceptions.ValidationError("User account is blocked.")
            data["user"] = user
        else:
            raise exceptions.ValidationError("Unable to login with the provided credentials.")

        return data


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user accounts with password handling.
    """
    password = serializers.CharField(write_only=True, required=False)
    is_superuser = serializers.BooleanField(write_only=True, required=False)
    assigned_tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            "id", "email", "username", "password", "first_name", 
            "last_name", "is_active", "is_superuser", "date_joined", 
            "last_login", "assigned_tasks_count"
        ]
        read_only_fields = ["id", "date_joined", "last_login"]
        extra_kwargs = {
            "password": {"write_only": True},
        }
    
    @extend_schema_field(int)
    def get_assigned_tasks_count(self, obj) -> int:
        """Return the count of tasks assigned to this user."""
        return obj.assigned_tasks.filter(is_deleted=False).count()

    def create(self, validated_data):
        is_superuser = validated_data.pop("is_superuser", False)
        password = validated_data.pop("password", None)
        
        if is_superuser:
            user = User.objects.create_superuser(**validated_data)
        else:
            user = User.objects.create_user(**validated_data)
            
        if password:
            user.set_password(password)
            user.save()
            
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        is_superuser = validated_data.pop("is_superuser", instance.is_superuser)
        
        instance = super().update(instance, validated_data)
        
        # Only update password if provided
        if password:
            instance.set_password(password)
            
        # Handle superuser status if the requester has permission
        instance.is_superuser = is_superuser
        instance.save()
        
        return instance


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for task tags.
    """
    tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ["id", "name", "color", "date_created", "tasks_count"]
        read_only_fields = ["id", "date_created"]
    
    @extend_schema_field(int)
    def get_tasks_count(self, obj) -> int:
        """Return the count of active tasks associated with this tag."""
        return obj.tasks.filter(is_deleted=False).count()
    
    def validate_color(self, value):
        """Validate that the color is a valid hex color."""
        if not value.startswith("#") or len(value) != 7:
            raise serializers.ValidationError("Color must be a valid hex code (e.g., #3498db)")
        try:
            # Check if the color is a valid hex by trying to convert it
            int(value[1:], 16)
        except ValueError:
            raise serializers.ValidationError("Invalid hex color code")
        return value


class UserPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for user preferences.
    """
    username = serializers.ReadOnlyField(source="user.username")
    
    class Meta:
        model = UserPreference
        fields = [
            "id", "user", "username", "theme", "receive_email_notifications", 
            "receive_collaboration_notifications", "default_view", 
            "date_created", "date_updated"
        ]
        read_only_fields = ["id", "date_created", "date_updated"]


class TaskCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for task categories with task count.
    """
    tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskCategory
        fields = ["id", "name", "date_created", "date_updated", "tasks_count"]
        read_only_fields = ["id", "date_created", "date_updated"]
    
    @extend_schema_field(int)
    def get_tasks_count(self, obj) -> int:
        """Return the count of active tasks in this category."""
        return obj.tasks.filter(is_deleted=False).count()


class SubTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for subtasks.
    """
    assigned_user_name = serializers.ReadOnlyField(source="assigned_user.username")
    
    class Meta:
        model = SubTask
        fields = [
            "id", "name", "description", "status", "parent_task", 
            "assigned_user", "assigned_user_name", "due_date", 
            "date_created", "date_updated"
        ]
        read_only_fields = ["id", "date_created", "date_updated"]
    
    def validate_parent_task(self, value):
        """Ensure parent task is not deleted."""
        if value.is_deleted:
            raise serializers.ValidationError("Cannot add subtask to a deleted task")
        return value


class TaskListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing tasks.
    """
    assigned_to = serializers.ReadOnlyField(source="assigned_user.username")
    category_name = serializers.ReadOnlyField(source="category.name")
    subtasks_count = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = [
            "id", "name", "status", "priority", "start_date", 
            "end_date", "progress", "assigned_to", "category_name", 
            "subtasks_count", "tags", "is_expired"
        ]
    
    @extend_schema_field(int)
    def get_subtasks_count(self, obj) -> int:
        return obj.subtasks.count()


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual task view with nested data.
    """
    assigned_user = UserSerializer(read_only=True)
    assigned_user_id = serializers.IntegerField(write_only=True)
    category = TaskCategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    subtasks = SubTaskSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    collaborators = UserSerializer(many=True, read_only=True)
    collaborator_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Task
        fields = [
            "id", "name", "description", "status", "start_date", 
            "start_time", "end_date", "end_time", "is_notified", 
            "is_expired", "is_deleted", "priority", "recurring", 
            "progress", "reminder_time", "assigned_user", "assigned_user_id",
            "collaborators", "collaborator_ids", "category", "category_id",
            "tags", "tag_ids", "subtasks", "attachments", "date_created", 
            "date_updated"
        ]
        read_only_fields = ["id", "is_notified", "is_expired", "date_created", "date_updated"]
    
    def validate(self, data):
        """
        Validate start date is before end date and other complex validations.
        """
        # If both dates are provided, ensure start is before end
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        start_time = data.get("start_time") 
        end_time = data.get("end_time")
        
        if all([start_date, end_date, start_time, end_time]):
            start_datetime = datetime.datetime.combine(start_date, start_time)
            end_datetime = datetime.datetime.combine(end_date, end_time)
            
            if start_datetime >= end_datetime:
                raise serializers.ValidationError(
                    "Task end date/time must be after start date/time"
                )
        
        return data
    
    def create(self, validated_data):
        """
        Handle creation with M2M relationships.
        """
        collaborator_ids = validated_data.pop("collaborator_ids", [])
        tag_ids = validated_data.pop("tag_ids", [])
        
        task = Task.objects.create(**validated_data)
        
        # Add collaborators
        if collaborator_ids:
            task.collaborators.set(User.objects.filter(id__in=collaborator_ids))
        
        # Add tags
        if tag_ids:
            task.tags.set(Tag.objects.filter(id__in=tag_ids))
        
        return task
    
    def update(self, instance, validated_data):
        """
        Handle updates with M2M relationships.
        """
        collaborator_ids = validated_data.pop("collaborator_ids", None)
        tag_ids = validated_data.pop("tag_ids", None)
        
        # Update direct fields
        instance = super().update(instance, validated_data)
        
        # Update collaborators if provided
        if collaborator_ids is not None:
            instance.collaborators.set(User.objects.filter(id__in=collaborator_ids))
        
        # Update tags if provided
        if tag_ids is not None:
            instance.tags.set(Tag.objects.filter(id__in=tag_ids))
        
        return instance


class OtpCodeSerializer(serializers.ModelSerializer):
    """
    Serializer for OTP codes with status info.
    """
    status = serializers.SerializerMethodField()
    username = serializers.ReadOnlyField(source="user.username")
    
    class Meta:
        model = OtpCode
        fields = [
            "id", "code", "is_used", "user", "username", "date_created", 
            "date_updated", "expiry_time", "status"
        ]
        read_only_fields = ["id", "date_created", "date_updated", "status"]
    
    @extend_schema_field(str)
    def get_status(self, obj) -> str:
        """Return the current status of the OTP code."""
        return obj.get_status()


class TaskSerializer(serializers.ModelSerializer):
    """
    Standard serializer for tasks with basic related fields.
    Use for general purpose task operations.
    """
    assigned_user_name = serializers.ReadOnlyField(source="assigned_user.username")
    category_name = serializers.ReadOnlyField(source="category.name", allow_null=True)
    
    class Meta:
        model = Task
        fields = [
            "id", "name", "description", "status", "start_date", 
            "start_time", "end_date", "end_time", "is_notified", 
            "is_expired", "is_deleted", "priority", "recurring", 
            "progress", "reminder_time", "assigned_user", "assigned_user_name",
            "category", "category_name", "date_created", "date_updated"
        ]
        read_only_fields = ["id", "is_notified", "is_expired", "date_created", "date_updated"]
    
    def validate(self, data):
        """
        Validate start date is before end date.
        """
        # If both dates and times are provided, ensure start is before end
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        start_time = data.get("start_time") 
        end_time = data.get("end_time")
        
        if all([start_date, end_date, start_time, end_time]):
            start_datetime = datetime.datetime.combine(start_date, start_time)
            end_datetime = datetime.datetime.combine(end_date, end_time)
            
            if start_datetime >= end_datetime:
                raise serializers.ValidationError(
                    "Task end date/time must be after start date/time"
                )
        
        return data


class TaskRelationshipSerializer(serializers.Serializer):
    """
    Serializer for task relationship operations like assigning tags or collaborators.
    """
    task_id = serializers.IntegerField(required=True)
    
    # For collaborators
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    
    # For tags
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )


class TaskBulkOperationSerializer(serializers.Serializer):
    """
    Serializer for bulk operations on tasks.
    """
    task_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )
    operation = serializers.ChoiceField(
        choices=["delete", "mark_completed", "change_status", "change_priority"],
        required=True
    )
    status = serializers.ChoiceField(
        choices=Task.STATUS_CHOICES,
        required=False
    )
    priority = serializers.ChoiceField(
        choices=Task.PRIORITY_CHOICES,
        required=False
    )
    
    def validate(self, data):
        operation = data.get("operation")
        
        if operation == "change_status" and "status" not in data:
            raise serializers.ValidationError("Status field is required for 'change_status' operation")
            
        if operation == "change_priority" and "priority" not in data:
            raise serializers.ValidationError("Priority field is required for 'change_priority' operation")
            
        return data