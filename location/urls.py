from django.urls import path
from . import views

urlpatterns = [
   path('location_tracker/', views.location_tracker, name='location_tracker'),
]