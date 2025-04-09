from django.urls import path
from . import views
from .views import *
urlpatterns = [
    path("index/", views.index, name="index"),

    path("v1/auth/login/", loginView.as_view(), name="login"),
    path("v1/auth/logout/", logoutView.as_view(), name="logout"),

    path("users/", views.listUser, name="list_user"),  # Ensure this endpoint is defined
    path("users/list/", views.listUser, name="list_user"),
    path("users/add/", views.addUser, name="add_user"),
    path("users/<str:pk>/", views.showUser, name="show_user"),
    path("users/<str:pk>/update/", views.updateUser, name="update_user"),
    path("users/<str:pk>/delete/", views.deleteUser, name="delete_user"),

    path("otp-codes/", views.listOtpCode, name="list_otp_code"),
    path("otp-codes/add/", views.addOtpCode, name="add_otp_code"),
    path("otp-codes/<str:pk>/", views.showOtpCode, name="show_otp_code"),
    path("otp-codes/<str:pk>/update/", views.updateOtpCode, name="update_otp_code"),
    path("otp-codes/<str:pk>/delete/", views.deleteOtpCode, name="delete_otp_code"),

    path("task-categories/", views.listTaskCategory, name="list_task_category"),
    path("task-categories/add/", views.addTaskCategory, name="add_task_category"),
    path("task-categories/<str:pk>/", views.showTaskCategory, name="show_task_category"),
    path("task-categories/<str:pk>/update/", views.updateTaskCategory, name="update_task_category"),
    path("task-categories/<str:pk>/delete/", views.deleteTaskCategory, name="delete_task_category"),

    path("tasks/", views.listTask, name="list_task"),
    path("tasks/add/", views.addTask, name="add_task"),
    path("tasks/<str:pk>/", views.showTask, name="show_task"),
    path("tasks/<str:pk>/update/", views.updateTask, name="update_task"),
    path("tasks/<str:pk>/delete/", views.deleteTask, name="delete_task"),
    path("tasks/notifications/", views.taskNotification, name="task_notification"),
]
