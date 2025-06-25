from django.contrib import admin
from .models import BusRoute, User , Driver , Parent , ParentProfile , DriverProfile , Student , StudentProfile

@admin.register(BusRoute)
class BusRouteAdmin(admin.ModelAdmin):
    pass

@admin.register(User)
class UserAdim(admin.ModelAdmin):
    pass
@admin.register(Driver)
class Driver(admin.ModelAdmin):
    pass
@admin.register(Parent)
class Parent(admin.ModelAdmin):
    pass
@admin.register(ParentProfile)
class ParentProfile(admin.ModelAdmin):
    pass
@admin.register(DriverProfile)
class DriverProfile(admin.ModelAdmin):
    pass
@admin.register(Student)
class Student(admin.ModelAdmin):
    pass
@admin.register(StudentProfile)
class StudentProfile(admin.ModelAdmin):
    pass