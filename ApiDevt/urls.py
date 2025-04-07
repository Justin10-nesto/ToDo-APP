
from django.urls import path
from . import views
from .views import *
urlpatterns = [ 

    path('index/', views.index, name='index'),

    path('v1/auth/login/', loginView.as_view(),),
    path('v1/auth/logout/', logoutView.as_view(),),
    path('listUserMixin/', views.listUserMixin.as_view(), name='listUserMixin'),
    path('listUser/', views.listUser, name='listUser'),
    path('addUser/', views.addUser, name='addUser'),
    path('showUser/<str:pk>/', views.showUser, name='showUser'),
    path('updateUser/<str:pk>/', views.updateUser, name='updateUser'),
    path('deleteUser/<str:pk>/', views.deleteUser, name='deleteUser'),

    path('listOtpCode/', views.listOtpCode, name='listOtpCode'),
    path('addOtpCode/', views.addOtpCode, name='addOtpCode'),
    path('showOtpCode/<str:pk>/', views.showOtpCode, name='showOtpCode'),
    path('updateOtpCode/<str:pk>/', views.updateOtpCode, name='updateOtpCode'),
    path('deleteOtpCode/<str:pk>/', views.deleteOtpCode, name='deleteOtpCode'),

    path('listTaskCategory/', views.listTaskCategory, name='listTaskCategory'),
    path('addTaskCategory/', views.addTaskCategory, name='addTaskCategory'),
    path('showTaskCategory/<str:pk>/', views.showTaskCategory, name='showTaskCategory'),
    path('updateTaskCategory/<str:pk>/', views.updateTaskCategory, name='updateTaskCategory'),
    path('deleteTaskCategory/<str:pk>/', views.deleteTaskCategory, name='deleteTaskCategory'),

    path('listTask/', views.listTask, name='listTask'),
    path('addTask/', views.addTask, name='addTask'),
    path('showTask/<str:pk>/', views.showTask, name='showTask'),
    path('updateTask/<str:pk>/', views.updateTask, name='updateTask'),
    path('deleteTask/<str:pk>/', views.deleteTask, name='deleteTask'),
    path('taskNotification/', views.taskNotification, name='taskNotification'),

]
