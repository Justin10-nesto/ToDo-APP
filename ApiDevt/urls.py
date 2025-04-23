from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IndexView,
    LoginView,
    LogoutView,
    UserViewSet,
    TaskViewSet,
    TaskCategoryViewSet,
    OtpCodeViewSet,
    SubTaskViewSet,
    TagViewSet,
    UserPreferenceViewSet
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'task-categories', TaskCategoryViewSet)
router.register(r'otp-codes', OtpCodeViewSet)
router.register(r'subtasks', SubTaskViewSet)
router.register(r'tags', TagViewSet)
router.register(r'user-preferences', UserPreferenceViewSet)

# API URLs
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('v1/auth/login/', LoginView.as_view(), name='login'),
    path('v1/auth/logout/', LogoutView.as_view(), name='logout'),
    path('v1/', include(router.urls)),
]
