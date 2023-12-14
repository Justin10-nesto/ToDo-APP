from rest_framework import serializers
from django.contrib.auth.models import *
from  rest_framework import exceptions
from ApiDevt.models import *
from django.contrib.auth import authenticate

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def vlidate(self, data):
        username = data.get('username', '')
        password = data.get('password', '')
        if username and password:
            user = authenticate(username = username, password = password)
            if user:
                if user.is_active:
                    data['user'] = user
                    print('ok')
                else:
                    msg = 'user account is blocked'
                    raise exceptions.ValidationError(msg)
            else:
                msg = 'Unable to login with given cridentials'
                raise exceptions.ValidationError(msg)

        else:
            msg = 'you must provide username or password'
            raise exceptions.ValidationError(msg)
        return data
    
class UserSerializer(serializers.Serializer):
    email = serializers.CharField()
    username = serializers.CharField()
    password = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    
    is_superuser = serializers.BooleanField()
    
    def validate(self, data):
        email = data.get('email', '')
        username = data.get('username', '')
        password = data.get('password', '')
        last_name = data.get('last_name', '')
        first_name = data.get('first_name', '')
        is_superuser = data.get('is_superuser', '')
        if email and password and username:
            if is_superuser:
                User.objects.create_superuser(email=email, username=username, password=password)
            else:
                
                User.objects.create_user(email=email, username=username, password=password)
            user = User.objects.get(username = username)
            user = User.objects.filter(username = email).first() 
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            data = user
            return data
        else:
            raise exceptions.ValidationError('all username, email, password and user role is required')

    class Meta:
        model = User
        fields = '__all__'

class TaskCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = TaskCategory
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        depth = 2
        
class OtpCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = OtpCode
        fields = '__all__'
        depth = 2
