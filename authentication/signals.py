from django.db.models.signals import post_save
from django.dispatch import receiver
from authentication.models import (
    StudentProfile,
    DriverProfile,
    ParentProfile,
    UserLocation,
    User as BaseUser,
    BusRoute,
)
import random
import string


# ✅ Automatically create profile and location when a User is created
@receiver(post_save, sender=BaseUser)
def create_profiles_and_location(sender, instance, created, **kwargs):
    """Create appropriate profile and location based on role after user creation."""
    if created:
        # Create UserLocation for all users
        UserLocation.objects.get_or_create(user=instance)

        # Create role-specific profiles
        if instance.role == BaseUser.Role.STUDENT:
            StudentProfile.objects.get_or_create(user=instance)
        elif instance.role == BaseUser.Role.DRIVER:
            DriverProfile.objects.get_or_create(user=instance)
        elif instance.role == BaseUser.Role.PARENT:
            ParentProfile.objects.get_or_create(user=instance)


# ✅ Helper to generate a random route name
def generate_random_route_name(length=8):
    return 'Route-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# ✅ Automatically assign student to a bus route when their profile is created
@receiver(post_save, sender=StudentProfile)
def assign_bus_route(sender, instance, created, **kwargs):
    if created:
        # Ensure the student isn't already in a route
        existing_routes = instance.routes.all()
        if not existing_routes.exists():
            # Create a new route with a random name
            route_name = generate_random_route_name()
            bus_route = BusRoute.objects.create(name=route_name)

            # Add the student to the route
            bus_route.students.add(instance)

            print(f"✅ Assigned {instance.user.username} to {bus_route.name}")