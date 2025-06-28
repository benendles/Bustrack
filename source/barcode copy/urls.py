from django.urls import path
from . import views

urlpatterns = [
    path('', views.submit_info, name='submit_info'),
    path('qr/<int:pk>/', views.show_qr, name='show_qr'),
    path('info/<int:pk>/', views.view_info, name='view_info'),
]