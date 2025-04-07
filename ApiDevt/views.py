import random
from django.contrib.auth import login, logout
from rest_framework.response import Response

from ApiDevt.permissionChecking import permission_required
from .models import *
from .serializer import *
from django.contrib.auth import login as django_login, logout as django_logout
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import generics, mixins
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication

def index(request):
    return Response("Hello world")

class listUserMixin(mixins.ListModelMixin, generics.GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

class loginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        if username and password:
            user = authenticate(username = username, password = password)
            if user:
                if user.is_active:
                    django_login(request, user)
                    token, created = Token.objects.get_or_create(user = user)
                    return Response({'token':token.key}, status=200)
                else:
                    msg = 'user account is blocked'
                    raise exceptions.ValidationError(msg)
            else:
                msg = 'Unable to login with given cridentials'
                raise exceptions.ValidationError(msg)

        else:
            msg = 'you must provide username or password'
            raise exceptions.ValidationError(msg)
    
class logoutView(APIView):
    authentication_classes = (TokenAuthentication)
    def post(self, request):
        django_logout(request)
        return Response(status=204)

@api_view(['GET','POST'])
def addUser(request):
    serializer = UserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.validate(request.data)
    return Response(serializer.data)

@api_view(['GET','POST'])
# @permission_required(['auth.view_user'])
def listUser(request):
    user =User.objects.all()
    serializer = UserSerializer(user,many=True)
    return Response(serializer.data, status=200)

@api_view(['GET','POST'])
@permission_required(['auth.view_user'])
def showUser(request,pk):
    user = User.objects.filter(id=pk).first()
    serializer = UserSerializer(user,many=True)
    return Response(serializer.data)

@api_view(['GET','POST'])
@permission_required(['auth.change_user'])
def updateUser(request,pk):
    user = User.objects.filter(id=pk).first()
    if(user):
        serializer = UserSerializer(instance=user,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    return Response({"error":"error while updating"})

@api_view(['GET','POST'])
@permission_required(['auth.delete_user'])
def deleteUser(request,pk):
    user = User.objects.filter(id=pk).first()
    if(user):
        user.is_active = not user.is_active
        return Response({"success":"user is blocked successful"})
    else:
        return Response({"error":"error while deleting"})

@api_view(['GET','POST'])
@permission_required(["ApiDevt.add_taskcategory"])
def addTaskCategory(request):
    serializer = TaskCategorySerializer(data=request.data)
    serializer.is_valid(raise_exception=True )
    serializer.save()
    return Response(serializer.data)

@api_view(['GET','POST'])
@permission_required(["ApiDevt.view_taskcategory"])
def listTaskCategory(request):
    taskCategory = TaskCategory.objects.all()
    serializer = TaskCategorySerializer(taskCategory,many=True)
    return Response(serializer.data)

@api_view(['GET','POST'])
@permission_required(["ApiDevt.view_taskcategory"])
def showTaskCategory(request,pk):
    taskCategory = TaskCategory.objects.filter(id=pk).first()
    serializer = TaskCategorySerializer(taskCategory)
    return Response(serializer.data)

@api_view(['GET','POST'])
@permission_required(["ApiDevt.change_taskcategory"])
def updateTaskCategory(request,pk):
    taskCategory = TaskCategory.objects.filter(id=pk).first()
    if(taskCategory):
        serializer = TaskCategorySerializer(instance=taskCategory,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    else:
        return Response({"error":"error while updating"})

@api_view(['GET','POST'])
@permission_required(["ApiDevt.delete_taskcategory"])
def deleteTaskCategory(request,pk):
    taskCategory = TaskCategory.objects.filter(id=pk)
    if(taskCategory):
        taskCategory.delete()
        return Response({"success":"deleted successful"})
    else:
        return Response({"error":"error while deleting"})

@api_view(['GET','POST'])
@permission_required(["ApiDevt.add_task"])
def addTask(request):
    serializer = TaskCategorySerializer(data=request.data)
    
    name = request.data.get('name', '')
    description = request.data.get('description', '')
    status = request.data.get('status', '')
    start_date = request.data.get('start_date', '')
    start_time = request.data.get('start_time', '')
    end_date = request.data.get('end_date', '')
    end_time = request.data.get('end_time', '')
    # if not (start_date or start_time):
    #     raise exceptions.ValidationError('please set atart date and time')
    # if not (end_date or end_time):
    #     raise exceptions.ValidationError('please set atart date and time')
    assigned_user_id = request.user.id
    assigned_user = User.objects.get(id = assigned_user_id)
    task = Task.objects.get_or_create(name = name, description = description, status = status, start_date = start_date, start_time = start_time, end_date = end_date, end_time = end_time, assigned_user =assigned_user )
    serializer = TaskSerializer(task)
    return Response({'Status': 'task added sucessfully'})

@api_view(['GET','POST'])
@permission_required(["ApiDevt.view_task"])
def listTask(request):
    if request.user.is_superuser:
        task = Task.objects.all()
    else:
        task = Task.objects.filter(assigned_user = request.user)
    serializer = TaskSerializer(task,many=True)
    return Response(serializer.data)

@api_view(['GET','POST'])
@permission_required(["ApiDevt.view_task"])
def showTask(request,pk):
    task = Task.objects.filter(id=pk).first()

    if request.user.is_superuser:
        if request.user.id != task.assigned_user.id:
            return Response({'Access': "You don't have required access"})

    serializer = TaskSerializer(task)
    return Response(serializer.data, status=200)

@api_view(['GET','POST'])
@permission_required(["ApiDevt.change_task"])
def updateTask(request,pk):
    task = Task.objects.filter(id=pk).first()
    if(task):

        if not request.user.is_superuser:
            if request.user.id != task.assigned_user.id:
                return Response({'Access': "You don't have required access"})
        
        serializer = TaskSerializer(instance=task,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    else:
        return Response({"error":"error while updating"})

@api_view(['GET','POST'])
@permission_required(["ApiDevt.delete_task"])
def deleteTask(request,pk):
    task = Task.objects.filter(id=pk).first()
    if(task):

        if not request.user.is_superuser:
            if request.user.id != task.assigned_user.id:
                return Response({'Access': "You don't have required access"})
        task.delete()
        return Response({"success":"deleted successful"})
    else:
        return Response({"error":"error while deleting"})

@api_view(['GET','POST','PUT'])
def taskNotification(request):
    tasks = Task.objects.all()
    for task in tasks:
        notify = task.semdingNotification
        expried = task.checking_expiredTask
    return Response({"success":"Expering of task sucessfully"}, status=200)
  
@api_view(['GET','POST'])
def addOtpCode(request):
    serializer = OtpCodeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True )
    serializer.save()
    for key, value in serializer.data.items():
        if key == 'id':
            pk = value
            otpCode = OtpCode.objects.filter(id=value).first()
            for key1, value1 in request.data.items():    
                if key1 == 'user':
                    user = User.objects.filter(id = value1).first()
                    otpCode.user =user
                    otpCode.save()
    otpCode = OtpCode.objects.filter(id=pk)
    serializer = OtpCodeSerializer(otpCode,many=True)
    return Response(serializer.data)

@api_view(['GET','POST'])
def listOtpCode(request):
    otpCode = OtpCode.objects.all()
    serializer = OtpCodeSerializer(otpCode,many=True)
    return Response(serializer.data)

@api_view(['GET','POST'])
def showOtpCode(request,pk):
    otpCode = OtpCode.objects.filter(id=pk)
    serializer = OtpCodeSerializer(otpCode,many=True)
    return Response(serializer.data)
    
@api_view(['GET','POST'])
def updateOtpCode(request,pk):
     otpCode = OtpCode.objects.filter(id=pk).first()

     if(otpCode):
        serializer = OtpCodeSerializer(instance=otpCode,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        for key, value in serializer.data.items():
            if key == 'id':
                pk = value
                otpCode = OtpCode.objects.filter(id=value).first()
                for key1, value1 in request.data.items():    
                    if key1 == 'user':
                        user = User.objects.filter(id = value1).first()
                        otpCode.user =user
                        otpCode.save()
        otpCode = OtpCode.objects.filter(id=pk)
        serializer = OtpCodeSerializer(otpCode,many=True)
        return Response(serializer.data)

     return Response({"error":"error while updating"})

@api_view(['GET','POST','PUT'])
def deleteOtpCode(request,pk):
    otpCode = OtpCode.objects.filter(id=pk).delete()
    if(otpCode):
        return Response({"success":"deleted successful"})
    else:
        return Response({"error":"error while deleting"})
 
@api_view(['GET','POST'])    
def foggotenPassword(request):
    username = request.data['username']
        
    user = User.objects.filter(username=username).first()
    opts_exists = OtpCode.objects.filter(user__username__gt = username, is_used=False).exists()
    opts = OtpCode.objects.filter(user__username__gt = username, is_used=False)
    email = [user.email]
    status = False
    if opts_exists:
        for opt in opts:
            if opt.get_status == 'Valid':
                status = True
                
    if not status:
        opt = random.randint(100000,999999)
        opt_generated = 'E-' + str(opt)
        OtpCode.objects.create(code = opt_generated, user = user)
        header = 'Resset Password'
        message = f"dear {user.first_name},\n we heard that you lost your password account. Don't worry you can reset your password by returning to your browser and use the following code.\n {opt_generated}"
        email_from = settings.EMAIL_HOST_USER
        send_mail(header, message, email_from, email)
    serializer = UserSerializer(user)
    return Response(serializer.data)

@api_view(['GET','POST'])
def resend_password(request, id):
    user = User.objects.filter(id=id).first()
    opts_exists = OtpCode.objects.filter(user__id__gt = id, is_used=False).exists()
    opts = OtpCode.objects.filter(user__id__gt = id, is_used=False)
    status = False
    if opts_exists:
        for opt in opts:
            if opt.get_status == 'Valid':
                status = True
    if not status:
        opt = random.randint(100000,999999)
        opt_generated = 'E-' + str(opt)
        OtpCode.objects.create(code = opt_generated, user = user)
        header = 'Resset Password'
        message = f"dear {user.first_name},\n we heard that you lost your password account. Don't worry you can reset your password by returning to your browser and use the following code.\n {opt_generated}"
        email_from = settings.EMAIL_HOST_USER
        send_mail(header, message, email_from, email)
    serializer = UserSerializer(user,many=True)
    return Response(serializer.data)

@api_view(['GET','POST'])
def opt_sent(request, id):
    if request.method == "POST":
        code = request.data['code']
        # print(id)
        user = User.objects.filter(id = id).first()
        opts = OtpCode.objects.filter(user = user, is_used=False)
        user = User.objects.filter(id = id).first()
        for opt in opts:
            if opt.code == code:
                if opt.get_status == 'Valid':
                    opt.is_used = True
                    opt.save()
                    serializer = UserSerializer(user)
                    return Response(serializer.data)
                else:

                    opt.is_used = True
                    opt.save()
                    serializer = UserSerializer(user)
                    return Response(serializer.data)
                    return Response({'status':'Code used has been arleady expired'})
        return Response({'status':'Incorrect code used'})
