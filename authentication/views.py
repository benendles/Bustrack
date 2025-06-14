from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .forms import SignUpForm
from .models import User, UserLocation, BusRoute, StudentProfile
import json

def home(request):
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
def driver_dashboard(request):
    # Get all students assigned to this driver's routes
    students_locations = []
    try:
        bus_routes = BusRoute.objects.filter(driver=request.user)
        for route in bus_routes:
            for student in route.students.all():
                try:
                    location = UserLocation.objects.get(user=student)
                    if location.is_online:
                        students_locations.append({
                            'user': student,
                            'location': location
                        })
                except UserLocation.DoesNotExist:
                    pass
    except Exception as e:
        pass
    
    context = {
        'students_locations': students_locations,
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

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            # Optionally, log the user in immediately:
            # login(request, user)
            if user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'driver':
                return redirect('driver_dashboard')
            elif user.role == 'parent':
                return redirect('parent_dashboard')
            else:
                messages.error(request, 'Invalid role selected')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username, password)

        user = authenticate(request, username=username, password=password)
        print(user)

        if user is not None:  
            login(request, user)

            if user.role == 'student':
                return redirect('student_dashboard')  # Use the URL name!
            elif user.role == 'driver':
                return redirect('driver_dashboard')
            elif user.role == 'parent':
                return redirect('parent_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'registration/login.html')
def location_tracker(request):
    return render(request, 'location_tracker.html')