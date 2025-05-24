from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    #path('ChooseDashoard/',views.ChooseDashboard, name='ChooseDashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('parent/dashboard/', views.parent_dashboard, name='parent_dashboard'),
    
]