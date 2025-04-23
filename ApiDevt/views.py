import datetime
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework import status, viewsets, generics, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend
import random
import string

from .models import Task, TaskCategory, OtpCode, SubTask, Tag, UserPreference
from .serializer import (
    LoginSerializer, 
    UserSerializer, 
    TaskSerializer,
    TaskCategorySerializer, 
    OtpCodeSerializer,
    SubTaskSerializer,
    TagSerializer,
    UserPreferenceSerializer,
    TaskListSerializer,
    TaskDetailSerializer
)

# Add this new serializer for logout
from rest_framework import serializers
class LogoutSerializer(serializers.Serializer):
    """Serializer for user logout."""
    pass


class IndexView(APIView):
    """
    API Index view to provide basic info about the API
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="API Index",
        description="Returns the basic structure and endpoints of the API.",
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        """Get API endpoints overview"""
        api_urls = {
            'Auth': {
                'Login': '/api/v1/auth/login/',
                'Logout': '/api/v1/auth/logout/',
            },
            'Users': {
                'List': '/api/users/',
                'Create': '/api/users/',
                'Retrieve': '/api/users/{id}/',
                'Update': '/api/users/{id}/',
                'Delete': '/api/users/{id}/',
            },
            'Tasks': {
                'List': '/api/tasks/',
                'Create': '/api/tasks/',
                'Retrieve': '/api/tasks/{id}/',
                'Update': '/api/tasks/{id}/',
                'Delete': '/api/tasks/{id}/',
                'Notifications': '/api/tasks/notifications/',
            },
            'Documentation': {
                'Swagger': '/api/docs/',
                'Redoc': '/api/redoc/',
                'Schema': '/api/schema/',
            }
        }
        
        return Response(api_urls)


@extend_schema(tags=['Auth'])
class LoginView(APIView):
    """
    Login view for authenticating users and generating tokens.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="User login",
        description="Authenticate user and return token",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description="Login successful",
                examples=[
                    OpenApiExample(
                        "Successful login",
                        value={
                            "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
                            "user_id": 1,
                            "email": "user@example.com",
                            "username": "username",
                            "first_name": "First",
                            "last_name": "Last",
                            "is_staff": False,
                            "is_active": True,
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid credentials")
        }
    )
    def post(self, request):
        """Login user and return authentication token"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            login(request, user)
            
            # Create or get token for the user
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                "token": token.key,
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_staff": user.is_staff,
                "is_active": user.is_active,
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Auth'])
class LogoutView(APIView):
    """
    Logout view to invalidate the user's token.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="User logout",
        description="Invalidate the user's authentication token",
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(description="Successfully logged out"),
            500: OpenApiResponse(description="Logout error")
        }
    )
    def post(self, request):
        """Logout the current user by deleting their token"""
        try:
            # Delete the user's token
            request.user.auth_token.delete()
            logout(request)
            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Users'])
class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for users
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def get_permissions(self):
        """
        Allow user registration (POST) without authentication
        Restrict user list and deletion to admin users
        Allow users to view and update their own profile
        """
        if self.action == 'create':
            permission_classes = [AllowAny]
        elif self.action in ['list', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_object(self):
        """
        Get the object for the requested user, ensuring proper permissions
        """
        obj = super().get_object()
        if self.request.user != obj and not self.request.user.is_staff:
            self.permission_denied(self.request)
        return obj
    
    @extend_schema(
        summary="Create new user",
        description="Register a new user account",
        responses={
            201: UserSerializer,
            400: OpenApiResponse(description="Invalid data")
        }
    )
    def create(self, request, *args, **kwargs):
        """Create a new user account"""
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        summary="List users",
        description="Get list of all users (admin only)",
        responses={
            200: UserSerializer(many=True),
            403: OpenApiResponse(description="Permission denied")
        }
    )
    def list(self, request, *args, **kwargs):
        """List all user accounts (admin only)"""
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Get user details",
        description="Get details for a specific user",
        responses={
            200: UserSerializer,
            404: OpenApiResponse(description="User not found")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Get user account details"""
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update user",
        description="Update user account information",
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Invalid data"),
            404: OpenApiResponse(description="User not found")
        }
    )
    def update(self, request, *args, **kwargs):
        """Update user account information"""
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        summary="Delete user",
        description="Delete user account (admin only)",
        responses={
            204: OpenApiResponse(description="User deleted"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="User not found")
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Delete user account"""
        return super().destroy(request, *args, **kwargs)
    
    @extend_schema(
        summary="Get current user",
        description="Get the current authenticated user's details",
        responses={
            200: UserSerializer,
        }
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current authenticated user's details"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


@extend_schema(tags=['OTP Codes'])
class OtpCodeViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for OTP codes
    """
    queryset = OtpCode.objects.all().order_by('-date_created')
    serializer_class = OtpCodeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['user', 'is_used']
    search_fields = ['code']
    
    @extend_schema(
        summary="Create OTP code",
        description="Generate a new OTP code for a user",
        responses={
            201: OtpCodeSerializer,
            400: OpenApiResponse(description="Invalid data")
        }
    )
    def create(self, request, *args, **kwargs):
        """Generate a new OTP code"""
        data = request.data.copy()
        
        # Generate a random OTP code if not provided
        if 'code' not in data or not data['code']:
            data['code'] = ''.join(random.choices(string.digits, k=6))
        
        # Set the user if not provided
        if 'user' not in data or not data['user']:
            data['user'] = request.user.id
            
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @extend_schema(
        summary="Verify OTP code",
        description="Verify an OTP code and mark it as used",
        request={"application/json": {"code": str}},
        responses={
            200: OpenApiResponse(
                description="OTP verification result",
                examples=[
                    OpenApiExample(
                        "Valid OTP",
                        value={
                            "status": "valid",
                            "message": "OTP code is valid"
                        }
                    ),
                    OpenApiExample(
                        "Invalid OTP",
                        value={
                            "status": "invalid",
                            "message": "OTP code is invalid or expired"
                        }
                    )
                ]
            ),
            404: OpenApiResponse(description="OTP code not found")
        }
    )
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """Verify an OTP code and mark it as used if valid"""
        code = request.data.get('code')
        user_id = request.data.get('user_id', request.user.id)
        
        try:
            otp = OtpCode.objects.get(
                code=code,
                user_id=user_id,
                is_used=False,
                expiry_time__gt=timezone.now()
            )
            
            otp.is_used = True
            otp.save()
            
            return Response({
                "status": "valid",
                "message": "OTP code is valid"
            })
            
        except OtpCode.DoesNotExist:
            return Response({
                "status": "invalid",
                "message": "OTP code is invalid or expired"
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Task Categories'])
class TaskCategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for task categories
    """
    queryset = TaskCategory.objects.all().order_by('name')
    serializer_class = TaskCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'date_created', 'date_updated']
    
    @extend_schema(
        summary="List task categories",
        description="Get a list of all task categories",
        responses={200: TaskCategorySerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """List all task categories"""
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create task category",
        description="Create a new task category",
        request=TaskCategorySerializer,
        responses={
            201: TaskCategorySerializer,
            400: OpenApiResponse(description="Invalid data")
        }
    )
    def create(self, request, *args, **kwargs):
        """Create a new task category"""
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        summary="Get task category",
        description="Get details for a specific task category",
        responses={
            200: TaskCategorySerializer,
            404: OpenApiResponse(description="Category not found")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Get task category details"""
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update task category",
        description="Update an existing task category",
        request=TaskCategorySerializer,
        responses={
            200: TaskCategorySerializer,
            400: OpenApiResponse(description="Invalid data"),
            404: OpenApiResponse(description="Category not found")
        }
    )
    def update(self, request, *args, **kwargs):
        """Update task category details"""
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        summary="Delete task category",
        description="Delete a task category",
        responses={
            204: OpenApiResponse(description="Category deleted"),
            404: OpenApiResponse(description="Category not found")
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a task category"""
        return super().destroy(request, *args, **kwargs)


@extend_schema(tags=['Tasks'])
class TaskViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for tasks
    """
    queryset = Task.objects.filter(is_deleted=False)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'assigned_user': ['exact'],
        'category': ['exact'],
        'status': ['exact'],
        'priority': ['exact'],
        'start_date': ['gte', 'lte', 'exact'],
        'end_date': ['gte', 'lte', 'exact'],
        'is_expired': ['exact'],
        'tags': ['exact'],
    }
    search_fields = ['name', 'description']
    ordering_fields = ['start_date', 'end_date', 'priority', 'date_created', 'date_updated']
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter tasks based on user permissions:
        - Staff can see all tasks
        - Regular users can see tasks assigned to them or where they are collaborators
        """
        queryset = super().get_queryset()
        
        if not self.request.user.is_staff:
            # Regular users can see tasks they're assigned to or collaborating on
            queryset = queryset.filter(
                Q(assigned_user=self.request.user) | 
                Q(collaborators=self.request.user)
            ).distinct()
            
        return queryset
    
    def get_serializer_class(self):
        """
        Use different serializers for list and detail views:
        - List view: TaskListSerializer (lightweight)
        - Detail view: TaskDetailSerializer (full data)
        """
        if self.action == 'list':
            return TaskListSerializer
        return TaskDetailSerializer
    
    @extend_schema(
        summary="List tasks",
        description="Get a filtered list of tasks",
        parameters=[
            OpenApiParameter("assigned_user", OpenApiTypes.INT, description="Filter by assigned user ID"),
            OpenApiParameter("category", OpenApiTypes.INT, description="Filter by category ID"),
            OpenApiParameter("status", OpenApiTypes.STR, description="Filter by status"),
            OpenApiParameter("priority", OpenApiTypes.STR, description="Filter by priority"),
            OpenApiParameter("start_date__gte", OpenApiTypes.DATE, description="Filter by start date (greater than or equal)"),
            OpenApiParameter("end_date__lte", OpenApiTypes.DATE, description="Filter by end date (less than or equal)"),
            OpenApiParameter("search", OpenApiTypes.STR, description="Search in name and description"),
            OpenApiParameter("ordering", OpenApiTypes.STR, description="Order by field (prefix with - for descending)"),
        ],
        responses={200: TaskListSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """List all tasks with filtering options"""
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create task",
        description="Create a new task",
        request=TaskDetailSerializer,
        responses={
            201: TaskDetailSerializer,
            400: OpenApiResponse(description="Invalid data")
        }
    )
    def create(self, request, *args, **kwargs):
        """Create a new task"""
        # Set the assigned user to the current user if not provided
        if 'assigned_user_id' not in request.data:
            request.data['assigned_user_id'] = request.user.id
            
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        summary="Get task details",
        description="Get details for a specific task",
        responses={
            200: TaskDetailSerializer,
            404: OpenApiResponse(description="Task not found")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Get task details"""
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update task",
        description="Update an existing task",
        request=TaskDetailSerializer,
        responses={
            200: TaskDetailSerializer,
            400: OpenApiResponse(description="Invalid data"),
            404: OpenApiResponse(description="Task not found")
        }
    )
    def update(self, request, *args, **kwargs):
        """Update task details"""
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        summary="Delete task",
        description="Soft delete a task (mark as deleted)",
        responses={
            204: OpenApiResponse(description="Task deleted"),
            404: OpenApiResponse(description="Task not found")
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Soft delete a task by marking it as deleted"""
        task = self.get_object()
        task.is_deleted = True
        task.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        summary="Check expired tasks",
        description="Check for and update expired tasks",
        responses={200: OpenApiResponse(description="Expired tasks updated")}
    )
    @action(detail=False, methods=['get'])
    def check_expired(self, request):
        """Check for expired tasks and update their status"""
        expired_tasks = Task.check_expired_tasks()
        serializer = TaskListSerializer(expired_tasks, many=True)
        return Response({
            "message": "Expired tasks have been updated",
            "expired_tasks_count": expired_tasks.count(),
            "expired_tasks": serializer.data
        })
    
    @extend_schema(
        summary="Send task notifications",
        description="Send notifications for tasks starting soon",
        responses={200: OpenApiResponse(description="Notifications sent")}
    )
    @action(detail=False, methods=['post'])
    def send_notifications(self, request):
        """Send notifications for tasks starting soon"""
        result = Task.send_notifications()
        return Response({"message": result})
    
    @extend_schema(
        summary="Get upcoming tasks",
        description="Get tasks with upcoming deadlines",
        responses={200: TaskListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get tasks with upcoming deadlines (within the next 7 days)"""
        today = timezone.now().date()
        upcoming_deadline = today + datetime.timedelta(days=7)
        
        queryset = self.get_queryset().filter(
            end_date__gte=today,
            end_date__lte=upcoming_deadline,
            is_expired=False
        ).order_by('end_date')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TaskListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TaskListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get overdue tasks",
        description="Get tasks that are overdue but not completed",
        responses={200: TaskListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue tasks (past deadline and not completed)"""
        today = timezone.now().date()
        
        queryset = self.get_queryset().filter(
            end_date__lt=today,
            status__in=["Not Started", "In Progress", "On Hold"],
            is_expired=True
        ).order_by('end_date')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TaskListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TaskListSerializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema(tags=['Subtasks'])
class SubTaskViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for subtasks
    """
    queryset = SubTask.objects.all()
    serializer_class = SubTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent_task', 'status', 'assigned_user', 'due_date']
    search_fields = ['name', 'description']
    ordering_fields = ['due_date', 'status', 'date_created', 'date_updated']
    
    def get_queryset(self):
        """
        Filter subtasks based on user permissions:
        - Staff can see all subtasks
        - Regular users can see subtasks of tasks assigned to them or where they are collaborators
        """
        queryset = super().get_queryset()
        
        if not self.request.user.is_staff:
            # Get tasks the user is assigned to or collaborating on
            user_tasks = Task.objects.filter(
                Q(assigned_user=self.request.user) | 
                Q(collaborators=self.request.user)
            )
            
            # Filter subtasks for those tasks
            queryset = queryset.filter(parent_task__in=user_tasks)
            
        return queryset
    
    @extend_schema(
        summary="List subtasks",
        description="Get a list of subtasks with filtering options",
        parameters=[
            OpenApiParameter("parent_task", OpenApiTypes.INT, description="Filter by parent task ID"),
            OpenApiParameter("status", OpenApiTypes.STR, description="Filter by status"),
            OpenApiParameter("assigned_user", OpenApiTypes.INT, description="Filter by assigned user ID"),
            OpenApiParameter("search", OpenApiTypes.STR, description="Search in name and description"),
        ],
        responses={200: SubTaskSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """List all subtasks with filtering options"""
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create subtask",
        description="Create a new subtask for a task",
        request=SubTaskSerializer,
        responses={
            201: SubTaskSerializer,
            400: OpenApiResponse(description="Invalid data"),
            404: OpenApiResponse(description="Parent task not found")
        }
    )
    def create(self, request, *args, **kwargs):
        """Create a new subtask"""
        # Set the assigned user to the current user if not provided
        if 'assigned_user' not in request.data:
            request.data['assigned_user'] = request.user.id
            
        return super().create(request, *args, **kwargs)


@extend_schema(tags=['Tags'])
class TagViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for tags
    """
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'date_created']
    
    @extend_schema(
        summary="Get tasks by tag",
        description="Get all tasks associated with a specific tag",
        responses={200: TaskListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Get all tasks for a specific tag"""
        tag = self.get_object()
        
        # Filter tasks by tag and user permissions
        if request.user.is_staff:
            tasks = tag.tasks.filter(is_deleted=False)
        else:
            tasks = tag.tasks.filter(
                Q(assigned_user=request.user) | 
                Q(collaborators=request.user),
                is_deleted=False
            ).distinct()
        
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = TaskListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)


@extend_schema(tags=['User Preferences'])
class UserPreferenceViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for user preferences
    """
    queryset = UserPreference.objects.all()
    serializer_class = UserPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter preferences based on user permissions:
        - Staff can see all preferences
        - Regular users can only see their own preference
        """
        queryset = super().get_queryset()
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
            
        return queryset
    
    @extend_schema(
        summary="Get my preferences",
        description="Get the current user's preferences",
        responses={
            200: UserPreferenceSerializer,
            404: OpenApiResponse(description="Preferences not found")
        }
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get or create preferences for the current user"""
        preference, created = UserPreference.objects.get_or_create(
            user=request.user,
            defaults={
                'theme': 'System',
                'receive_email_notifications': True,
                'receive_collaboration_notifications': True,
                'default_view': 'calendar'
            }
        )
        
        serializer = self.get_serializer(preference)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Update my preferences",
        description="Update the current user's preferences",
        request=UserPreferenceSerializer,
        responses={
            200: UserPreferenceSerializer,
            400: OpenApiResponse(description="Invalid data"),
            404: OpenApiResponse(description="Preferences not found")
        }
    )
    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        """Update preferences for the current user"""
        preference, created = UserPreference.objects.get_or_create(
            user=request.user,
            defaults={
                'theme': 'System',
                'receive_email_notifications': True,
                'receive_collaboration_notifications': True,
                'default_view': 'calendar'
            }
        )
        
        serializer = self.get_serializer(preference, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)
