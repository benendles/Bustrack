from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        DRIVER = 'driver', 'Driver'
        PARENT = 'parent', 'Parent'
        STUDENT = 'student', 'Student'
    base_role = Role.ADMIN
    role = models.CharField(max_length=50, choices=Role.choices, default=base_role)
def save(self, *args, **kwargs):
    if not self.pk and not self.role:
        self.role = self.base_role
    return super().save(*args, **kwargs)

class StudentManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=User.Role.STUDENT)

class Student(User):
    base_role = User.Role.STUDENT
    student = StudentManager()
    class Meta:
        proxy = True
    def welcome(self):
        return "Only for students"

@receiver(post_save, sender=Student)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == User.Role.STUDENT:
        StudentProfile.objects.create(user=instance)

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.IntegerField(null=True, blank=True)

class DriverManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=User.Role.DRIVER)

class Driver(User):
    base_role = User.Role.DRIVER
    driver = DriverManager()
    class Meta:
        proxy = True
    def welcome(self):
        return "Only for drivers"

class DriverProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    driver_id = models.IntegerField(null=True, blank=True)

@receiver(post_save, sender=Driver)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == User.Role.DRIVER:
        DriverProfile.objects.create(user=instance)

class ParentManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        results = super().get_queryset(*args, **kwargs)
        return results.filter(role=User.Role.PARENT)

class Parent(User):
    base_role = User.Role.PARENT
    parent = ParentManager()
    class Meta:
        proxy = True
    def welcome(self):
        return "Only for parents"

class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    parent_id = models.IntegerField(null=True, blank=True)

@receiver(post_save, sender=Parent)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == User.Role.PARENT:
        ParentProfile.objects.create(user=instance)
