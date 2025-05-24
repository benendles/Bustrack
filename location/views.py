from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import  Location

@login_required
def driver_location_view(request):
    user = request.user
    student_locations = Location.objects.filter(role='student')
    my_location = Location.objects.filter(user=user, role='driver')
    locations = list(student_locations) + list(my_location)
    return render(request, 'driver_dasboard.html', {'locations': locations})

@login_required
def location_tracker(request):
    user = request.user
    driver_locations = Location.objects.filter(role='driver')
    my_location = Location.objects.filter(user=user, role='student')
    locations = list(driver_locations) + list(my_location)
    return render(request, 'location_tracker.html', {'locations': locations})

@login_required
def parent_location_view(request):
    user = request.user
    driver_locations = Location.objects.filter(role='driver')
    my_location = Location.objects.filter(user=user, role='parent')
    locations = list(driver_locations) + list(my_location)
    return render(request, 'parent_dashboard.html', {'locations': locations})