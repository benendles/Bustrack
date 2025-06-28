from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('admin/signup/', views.admin_signup, name='admin_signup'),
    path('signout/', views.signout, name='signout'),
    path('profile/', views.profile_view, name='profile'),

    # Dashboard URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('parent/dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin/receipts/', views.admin_receipts, name='admin_receipts'),
    path('admin/receipts/<int:receipt_id>/verify/', views.verify_receipt, name='verify_receipt'),

    # Receipt management
    path('submit-receipt/', views.submit_receipt, name='submit_receipt'),
    path('receipt-status/', views.receipt_status, name='receipt_status'),

    # Parent-child connections
    path('search-children/', views.search_children, name='search_children'),
    path('request-connection/<int:child_id>/', views.request_connection, name='request_connection'),
    path('connection-requests/', views.connection_requests, name='connection_requests'),
    path('respond-connection/<int:connection_id>/', views.respond_connection, name='respond_connection'),
    path('location_tracker/', views.location_tracker, name='location_tracker'),

    # Password reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Location tracking API endpoints
    path('api/update-location/', views.update_location, name='update_location'),
    path('api/get-locations/', views.get_locations, name='get_locations'),
    path('api/set-offline/', views.set_offline, name='set_offline'),
]