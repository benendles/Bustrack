from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('location_tracker/', views.student_location, name='student_location'),
    path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('parent/dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('location_tracker/', views.location_tracker, name='location_tracker'),
    
    # Location tracking API endpoints
    path('api/update-location/', views.update_location, name='update_location'),
    path('api/get-locations/', views.get_locations, name='get_locations'),
    path('api/set-offline/', views.set_offline, name='set_offline'),
]