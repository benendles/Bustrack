from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from .forms import (SignUpForm, CustomLoginForm, UserProfileForm, AdminSignUpForm,
                   PaymentReceiptForm, ReceiptVerificationForm, ParentChildSearchForm,
                   ConnectionResponseForm)
from .models import (User, UserLocation, BusRoute, StudentProfile, PaymentReceipt,
                    ParentChildConnection, Notification)
import json
from functools import wraps

# Role-based access decorator
def role_required(allowed_roles):
    """Decorator to restrict access based on user roles"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('signin')

            if request.user.role not in allowed_roles:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('home')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def home(request):
    # If user is already authenticated, redirect to their dashboard
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)
    return render(request, 'home.html')

@login_required
def student_dashboard(request):
    # Get driver location if student is assigned to a route
    driver_location = None
    try:
        bus_route = request.user.bus_routes.first()
        if bus_route:
            driver_location = UserLocation.objects.get(user=bus_route.driver)
    except UserLocation.DoesNotExist:
        pass
    
    context = {
        'driver_location': driver_location,
    }
    return render(request, 'student_dashboard.html', context)

@login_required
@role_required(['driver'])
def driver_dashboard(request):
    """Driver dashboard view with verified students only"""
    # Get all students assigned to this driver's routes who have verified payments
    students_locations = []
    verified_students = []

    try:
        bus_routes = BusRoute.objects.filter(driver=request.user)
        for route in bus_routes:
            for student in route.students.all():
                # Check if student has approved payment receipt
                has_approved_receipt = PaymentReceipt.objects.filter(
                    student=student,
                    status='approved'
                ).exists()

                if has_approved_receipt:
                    verified_students.append(student)
                    try:
                        location = UserLocation.objects.get(user=student)
                        if location.is_online:
                            students_locations.append({
                                'user': student,
                                'location': location,
                                'payment_verified': True
                            })
                    except UserLocation.DoesNotExist:
                        # Add student even without location if payment is verified
                        students_locations.append({
                            'user': student,
                            'location': None,
                            'payment_verified': True
                        })
    except Exception as e:
        pass

    # Get recent verified receipts for this driver's students
    recent_receipts = PaymentReceipt.objects.filter(
        student__in=verified_students,
        status='approved'
    ).select_related('student').order_by('-verification_date')[:5]

    context = {
        'students_locations': students_locations,
        'verified_students': verified_students,
        'recent_receipts': recent_receipts,
        'total_verified': len(verified_students),
    }
    return render(request, 'driver_dashboard.html', context)

@login_required
def parent_dashboard(request):
    # Get children locations and driver location
    children_locations = []
    driver_location = None
    
    try:
        children = StudentProfile.objects.filter(parent=request.user)
        for child_profile in children:
            try:
                location = UserLocation.objects.get(user=child_profile.user)
                children_locations.append({
                    'user': child_profile.user,
                    'location': location
                })
                
                # Get driver location for the child's route
                bus_route = child_profile.user.bus_routes.first()
                if bus_route and not driver_location:
                    driver_location = UserLocation.objects.get(user=bus_route.driver)
            except UserLocation.DoesNotExist:
                pass
    except Exception as e:
        pass
    
    context = {
        'children_locations': children_locations,
        'driver_location': driver_location,
    }
    return render(request, 'parent_dashboard.html', context)

@csrf_exempt
@login_required
def update_location(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            if latitude and longitude:
                location, created = UserLocation.objects.get_or_create(user=request.user)
                location.latitude = latitude
                location.longitude = longitude
                location.is_online = True
                location.save()
                
                return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def get_locations(request):
    """API endpoint to get real-time locations based on user role"""
    locations = []
    
    if request.user.role == 'driver':
        # Driver sees all students in their routes
        bus_routes = BusRoute.objects.filter(driver=request.user)
        for route in bus_routes:
            for student in route.students.all():
                try:
                    location = UserLocation.objects.get(user=student, is_online=True)
                    locations.append({
                        'id': student.id,
                        'username': student.username,
                        'first_name': student.first_name,
                        'last_name': student.last_name,
                        'role': student.role,
                        'latitude': float(location.latitude) if location.latitude else None,
                        'longitude': float(location.longitude) if location.longitude else None,
                        'last_updated': location.last_updated.isoformat(),
                    })
                except UserLocation.DoesNotExist:
                    pass
                    
    elif request.user.role == 'student':
        # Student sees their driver
        bus_route = request.user.bus_routes.first()
        if bus_route:
            try:
                location = UserLocation.objects.get(user=bus_route.driver, is_online=True)
                locations.append({
                    'id': bus_route.driver.id,
                    'username': bus_route.driver.username,
                    'first_name': bus_route.driver.first_name,
                    'last_name': bus_route.driver.last_name,
                    'role': bus_route.driver.role,
                    'latitude': float(location.latitude) if location.latitude else None,
                    'longitude': float(location.longitude) if location.longitude else None,
                    'last_updated': location.last_updated.isoformat(),
                })
            except UserLocation.DoesNotExist:
                pass
                
    elif request.user.role == 'parent':
        # Parent sees their children and the driver
        children = StudentProfile.objects.filter(parent=request.user)
        driver_added = False
        
        for child_profile in children:
            # Add child location
            try:
                location = UserLocation.objects.get(user=child_profile.user, is_online=True)
                locations.append({
                    'id': child_profile.user.id,
                    'username': child_profile.user.username,
                    'first_name': child_profile.user.first_name,
                    'last_name': child_profile.user.last_name,
                    'role': child_profile.user.role,
                    'latitude': float(location.latitude) if location.latitude else None,
                    'longitude': float(location.longitude) if location.longitude else None,
                    'last_updated': location.last_updated.isoformat(),
                })
            except UserLocation.DoesNotExist:
                pass
            
            # Add driver location (only once)
            if not driver_added:
                bus_route = child_profile.user.bus_routes.first()
                if bus_route:
                    try:
                        location = UserLocation.objects.get(user=bus_route.driver, is_online=True)
                        locations.append({
                            'id': bus_route.driver.id,
                            'username': bus_route.driver.username,
                            'first_name': bus_route.driver.first_name,
                            'last_name': bus_route.driver.last_name,
                            'role': bus_route.driver.role,
                            'latitude': float(location.latitude) if location.latitude else None,
                            'longitude': float(location.longitude) if location.longitude else None,
                            'last_updated': location.last_updated.isoformat(),
                        })
                        driver_added = True
                    except UserLocation.DoesNotExist:
                        pass
    
    return JsonResponse({'locations': locations})

@csrf_exempt
@login_required
def set_offline(request):
    """Mark user as offline"""
    if request.method == 'POST':
        try:
            location = UserLocation.objects.get(user=request.user)
            location.is_online = False
            location.save()
            return JsonResponse({'status': 'success'})
        except UserLocation.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Location not found'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def get_client_ip(request):
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def role_required(allowed_roles):
    """Decorator to check if user has required role."""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('signin')
            if request.user.role not in allowed_roles:
                raise PermissionDenied("You don't have permission to access this page.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

@require_http_methods(["GET", "POST"])
def signup(request):
    # Check if user is authenticated and handle accordingly
    if request.user.is_authenticated:
        # If it's a GET request, show them the option to logout and signup
        if request.method == 'GET':
            context = {
                'current_user': request.user,
                'current_role': request.user.get_role_display(),
                'show_logout_option': True
            }
            return render(request, 'registration/signup.html', context)
        # If it's a POST request and they want to logout and signup
        elif request.method == 'POST' and 'logout_and_signup' in request.POST:
            logout(request)
            messages.info(request, 'You have been logged out. Please create your new account below.')
            return redirect('signup')
        # If they're trying to signup while logged in without logout
        else:
            messages.warning(request, 'You are already logged in. Please logout first to create a new account.')
            return redirect_to_dashboard(request.user)

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Store IP address for security tracking
                user.last_login_ip = get_client_ip(request)
                user.save()

                messages.success(request, 'Account created successfully! Please log in to continue.')
                return redirect('signin')
            except Exception as e:
                messages.error(request, 'An error occurred during registration. Please try again.')
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form})

def redirect_to_dashboard(user):
    """Redirect user to appropriate dashboard based on role."""
    role_dashboard_map = {
        'student': 'student_dashboard',
        'driver': 'driver_dashboard',
        'parent': 'parent_dashboard',
        'admin': 'admin_dashboard',
    }
    return redirect(role_dashboard_map.get(user.role, 'home'))

@require_http_methods(["GET", "POST"])
def admin_signup(request):
    """Admin registration with enhanced security"""
    # Check if user is authenticated and handle accordingly
    if request.user.is_authenticated:
        # If it's a GET request, show them the option to logout and signup
        if request.method == 'GET':
            context = {
                'current_user': request.user,
                'current_role': request.user.get_role_display(),
                'show_logout_option': True
            }
            return render(request, 'registration/admin_signup.html', context)
        # If it's a POST request and they want to logout and signup
        elif request.method == 'POST' and 'logout_and_signup' in request.POST:
            logout(request)
            messages.info(request, 'You have been logged out. Please create your admin account below.')
            return redirect('admin_signup')
        # If they're trying to signup while logged in without logout
        else:
            messages.warning(request, 'You are already logged in. Please logout first to create a new account.')
            return redirect_to_dashboard(request.user)

    if request.method == 'POST':
        form = AdminSignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Store IP address for security tracking
                user.last_login_ip = get_client_ip(request)
                user.save()

                messages.success(request, 'Admin account created successfully! Please log in to continue.')
                return redirect('signin')
            except Exception as e:
                messages.error(request, 'An error occurred during admin registration. Please try again.')
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = AdminSignUpForm()

    return render(request, 'registration/admin_signup.html', {'form': form})

@login_required
@role_required(['admin'])
def admin_dashboard(request):
    """Admin dashboard with system overview and user management"""
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta

    # Get system statistics
    total_users = User.objects.count()
    total_students = User.objects.filter(role='student').count()
    total_parents = User.objects.filter(role='parent').count()
    total_drivers = User.objects.filter(role='driver').count()
    total_admins = User.objects.filter(role='admin').count()

    # Recent registrations (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_registrations = User.objects.filter(created_at__gte=week_ago).count()

    # Active users (logged in within last 24 hours)
    day_ago = timezone.now() - timedelta(days=1)
    active_users = User.objects.filter(last_login__gte=day_ago).count()

    # Get recent users
    recent_users = User.objects.order_by('-created_at')[:10]

    # Get online users (with location data)
    online_users = UserLocation.objects.filter(is_online=True).select_related('user')

    # Bus routes statistics
    total_routes = BusRoute.objects.count()

    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_parents': total_parents,
        'total_drivers': total_drivers,
        'total_admins': total_admins,
        'recent_registrations': recent_registrations,
        'active_users': active_users,
        'recent_users': recent_users,
        'online_users': online_users,
        'total_routes': total_routes,
    }

    return render(request, 'admin_dashboard.html', context)

@login_required
@role_required(['admin'])
def admin_users(request):
    """Admin user management page"""
    from django.core.paginator import Paginator
    from django.db.models import Q

    # Get search query
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')

    # Filter users
    users = User.objects.all().order_by('-created_at')

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    if role_filter:
        users = users.filter(role=role_filter)

    # Pagination
    paginator = Paginator(users, 20)  # Show 20 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'roles': User.Role.choices,
    }

    return render(request, 'admin_users.html', context)

@login_required
@role_required(['admin'])
def admin_user_detail(request, user_id):
    """Admin user detail and edit page"""
    user_obj = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'toggle_active':
            user_obj.is_active = not user_obj.is_active
            user_obj.save()
            status = "activated" if user_obj.is_active else "deactivated"
            messages.success(request, f'User {user_obj.username} has been {status}.')

        elif action == 'change_role':
            new_role = request.POST.get('new_role')
            if new_role in [choice[0] for choice in User.Role.choices]:
                user_obj.role = new_role
                user_obj.save()
                messages.success(request, f'User role changed to {user_obj.get_role_display_name()}.')

        elif action == 'reset_password':
            # Generate a temporary password
            import secrets
            import string
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            user_obj.set_password(temp_password)
            user_obj.save()
            messages.success(request, f'Password reset. Temporary password: {temp_password}')

        return redirect('admin_user_detail', user_id=user_id)

    # Get user's location if available
    try:
        user_location = UserLocation.objects.get(user=user_obj)
    except UserLocation.DoesNotExist:
        user_location = None

    context = {
        'user_obj': user_obj,
        'user_location': user_location,
        'roles': User.Role.choices,
    }

    return render(request, 'admin_user_detail.html', context)

# Receipt Management Views
@login_required
@role_required(['student'])
def submit_receipt(request):
    """Student receipt submission"""
    if request.method == 'POST':
        form = PaymentReceiptForm(request.POST, request.FILES)
        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.student = request.user
            receipt.save()

            # Create notification for admins
            admin_users = User.objects.filter(role='admin')
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    type=Notification.Type.RECEIPT_SUBMITTED,
                    title='New Receipt Submitted',
                    message=f'Student {request.user.get_full_name() or request.user.username} submitted a payment receipt for verification.',
                    receipt=receipt
                )

            messages.success(request, 'Receipt submitted successfully! It will be reviewed by an administrator.')
            return redirect('student_dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = PaymentReceiptForm()

    return render(request, 'submit_receipt.html', {'form': form})

@login_required
@role_required(['student'])
def receipt_status(request):
    """View receipt submission status"""
    receipts = PaymentReceipt.objects.filter(student=request.user).order_by('-submitted_at')
    return render(request, 'receipt_status.html', {'receipts': receipts})

@login_required
@role_required(['admin'])
def admin_receipts(request):
    """Admin receipt verification dashboard"""
    status_filter = request.GET.get('status', 'pending')

    receipts = PaymentReceipt.objects.all()
    if status_filter != 'all':
        receipts = receipts.filter(status=status_filter)

    receipts = receipts.order_by('-submitted_at')

    context = {
        'receipts': receipts,
        'status_filter': status_filter,
        'status_choices': PaymentReceipt.Status.choices,
    }

    return render(request, 'admin_receipts.html', context)

@login_required
@role_required(['admin'])
def verify_receipt(request, receipt_id):
    """Admin receipt verification"""
    receipt = get_object_or_404(PaymentReceipt, id=receipt_id)

    if request.method == 'POST':
        form = ReceiptVerificationForm(request.POST, instance=receipt)
        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.verified_by = request.user
            receipt.verification_date = timezone.now()
            receipt.save()

            # Create notification for student
            notification_type = (Notification.Type.RECEIPT_APPROVED
                               if receipt.status == 'approved'
                               else Notification.Type.RECEIPT_REJECTED)

            Notification.objects.create(
                user=receipt.student,
                type=notification_type,
                title=f'Receipt {receipt.status.title()}',
                message=f'Your payment receipt has been {receipt.status}. {receipt.admin_notes}',
                receipt=receipt
            )

            messages.success(request, f'Receipt {receipt.status} successfully.')
            return redirect('admin_receipts')
    else:
        form = ReceiptVerificationForm(instance=receipt)

    context = {
        'receipt': receipt,
        'form': form,
    }

    return render(request, 'verify_receipt.html', context)

# Parent-Child Connection Views
@login_required
@role_required(['parent'])
def search_children(request):
    """Parent search for children"""
    children = []
    search_performed = False

    if request.method == 'POST':
        form = ParentChildSearchForm(request.POST)
        if form.is_valid():
            search_query = form.cleaned_data['search_query']
            search_performed = True

            # Search for students
            from django.db.models import Q
            children = User.objects.filter(
                role='student'
            ).filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            ).exclude(
                # Exclude children already connected or with pending requests
                parent_connections__parent=request.user
            )
    else:
        form = ParentChildSearchForm()

    # Get existing connections
    existing_connections = ParentChildConnection.objects.filter(parent=request.user)

    context = {
        'form': form,
        'children': children,
        'search_performed': search_performed,
        'existing_connections': existing_connections,
    }

    return render(request, 'search_children.html', context)

@login_required
@role_required(['parent'])
def request_connection(request, child_id):
    """Parent request connection to child"""
    child = get_object_or_404(User, id=child_id, role='student')

    # Check if connection already exists
    existing_connection = ParentChildConnection.objects.filter(
        parent=request.user,
        child=child
    ).first()

    if existing_connection:
        messages.warning(request, f'Connection request already exists for {child.get_full_name() or child.username}.')
    else:
        # Create connection request
        connection = ParentChildConnection.objects.create(
            parent=request.user,
            child=child
        )

        # Create notification for child
        Notification.objects.create(
            user=child,
            type=Notification.Type.PARENT_REQUEST,
            title='Parent Connection Request',
            message=f'{request.user.get_full_name() or request.user.username} wants to connect as your parent.',
            connection=connection
        )

        messages.success(request, f'Connection request sent to {child.get_full_name() or child.username}.')

    return redirect('search_children')

@login_required
@role_required(['student'])
def connection_requests(request):
    """Student view and respond to parent connection requests"""
    pending_requests = ParentChildConnection.objects.filter(
        child=request.user,
        status='pending'
    )

    approved_connections = ParentChildConnection.objects.filter(
        child=request.user,
        status='approved'
    )

    context = {
        'pending_requests': pending_requests,
        'approved_connections': approved_connections,
    }

    return render(request, 'connection_requests.html', context)

@login_required
@role_required(['student'])
def respond_connection(request, connection_id):
    """Student respond to parent connection request"""
    connection = get_object_or_404(
        ParentChildConnection,
        id=connection_id,
        child=request.user,
        status='pending'
    )

    if request.method == 'POST':
        form = ConnectionResponseForm(request.POST, instance=connection)
        if form.is_valid():
            connection = form.save(commit=False)
            connection.responded_at = timezone.now()
            connection.save()

            # Create notification for parent
            notification_type = (Notification.Type.CONNECTION_APPROVED
                               if connection.status == 'approved'
                               else Notification.Type.CONNECTION_REJECTED)

            Notification.objects.create(
                user=connection.parent,
                type=notification_type,
                title=f'Connection {connection.status.title()}',
                message=f'{request.user.get_full_name() or request.user.username} {connection.status} your connection request.',
                connection=connection
            )

            status_text = 'accepted' if connection.status == 'approved' else 'rejected'
            messages.success(request, f'Connection request {status_text}.')
            return redirect('connection_requests')
    else:
        form = ConnectionResponseForm(instance=connection)

    context = {
        'connection': connection,
        'form': form,
    }

    return render(request, 'respond_connection.html', context)

@require_http_methods(["GET", "POST"])
def signin(request):
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # Update last login IP
            user.last_login_ip = get_client_ip(request)
            user.save(update_fields=['last_login_ip'])

            login(request, user)

            # Set session timeout (30 minutes of inactivity)
            request.session.set_expiry(1800)

            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')

            # Redirect to intended page or dashboard
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect_to_dashboard(user)
        else:
            # Add form errors to messages
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = CustomLoginForm()

    return render(request, 'registration/login.html', {'form': form})

@login_required
def signout(request):
    """Logout view with proper session cleanup."""
    user_name = request.user.get_full_name() or request.user.username
    logout(request)
    messages.success(request, f'Goodbye, {user_name}! You have been logged out successfully.')
    return redirect('signin')

@login_required
def profile_view(request):
    """View and edit user profile."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'registration/profile.html', {'form': form})
def location_tracker(request):
    return render(request, 'location_tracker.html')