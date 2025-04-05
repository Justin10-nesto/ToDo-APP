from rest_framework import serializers, exceptions
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from ApiDevt.models import Task, TaskCategory, OtpCode


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
    Serializer for creating and updating user accounts.
    """
    is_superuser = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "username", "password", "first_name", "last_name", "is_superuser"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        is_superuser = validated_data.pop("is_superuser", False)
        if is_superuser:
            user = User.objects.create_superuser(**validated_data)
        else:
            user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.email = validated_data.get("email", instance.email)
        instance.save()
        return instance


class TaskCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for task categories.
    """
    class Meta:
        model = TaskCategory
        fields = "__all__"


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for tasks.
    """
    class Meta:
        model = Task
        fields = "__all__"
        depth = 2


class OtpCodeSerializer(serializers.ModelSerializer):
    """
    Serializer for OTP codes.
    """
    class Meta:
        model = OtpCode
        fields = "__all__"
        depth = 2