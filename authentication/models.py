from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
import re

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        DRIVER = 'driver', 'Driver'
        PARENT = 'parent', 'Parent'
        STUDENT = 'student', 'Student'

    base_role = Role.STUDENT  # Changed default to student for new registrations
    role = models.CharField(max_length=50, choices=Role.choices, default=base_role)

    # Enhanced fields
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(max_length=500, blank=True, null=True)
    emergency_contact = models.CharField(max_length=100, blank=True, null=True)
    emergency_phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Emergency phone must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    is_active_user = models.BooleanField(default=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    def clean(self):
        super().clean()
        # Validate email format
        if self.email:
            email_validator = EmailValidator()
            try:
                email_validator(self.email)
            except ValidationError:
                raise ValidationError({'email': 'Enter a valid email address.'})

    def save(self, *args, **kwargs):
        if not self.pk and not self.role:
            self.role = self.base_role
        self.full_clean()  # Run validation before saving
        return super().save(*args, **kwargs)

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()

    def get_role_display_name(self):
        """Return a user-friendly role name."""
        return dict(self.Role.choices)[self.role]

    def __str__(self):
        return f"{self.username} ({self.get_role_display_name()})"


class PaymentReceipt(models.Model):
    """Model for student payment receipts with admin verification"""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Verification'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='payment_receipts'
    )
    receipt_image = models.ImageField(upload_to='receipts/')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    description = models.TextField(max_length=500, blank=True)

    # Verification fields
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'admin'},
        related_name='verified_receipts'
    )
    verification_date = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(max_length=1000, blank=True)

    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Receipt by {self.student.username} - {self.status}"

    @property
    def is_verified(self):
        return self.status == self.Status.APPROVED


class ParentChildConnection(models.Model):
    """Model for parent-child connections with validation"""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Approval'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'parent'},
        related_name='child_connections'
    )
    child = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='parent_connections'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['parent', 'child']
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.parent.username} -> {self.child.username} ({self.status})"


class Notification(models.Model):
    """Model for system notifications"""

    class Type(models.TextChoices):
        RECEIPT_SUBMITTED = 'receipt_submitted', 'Receipt Submitted'
        RECEIPT_APPROVED = 'receipt_approved', 'Receipt Approved'
        RECEIPT_REJECTED = 'receipt_rejected', 'Receipt Rejected'
        PARENT_REQUEST = 'parent_request', 'Parent Connection Request'
        CONNECTION_APPROVED = 'connection_approved', 'Connection Approved'
        CONNECTION_REJECTED = 'connection_rejected', 'Connection Rejected'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional references
    receipt = models.ForeignKey(PaymentReceipt, on_delete=models.CASCADE, null=True, blank=True)
    connection = models.ForeignKey(ParentChildConnection, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

# Location tracking models
class UserLocation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='location')
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    is_online = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - ({self.latitude}, {self.longitude})"

class BusRoute(models.Model):
    name = models.CharField(max_length=100)
    driver = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'driver'})
    students = models.ManyToManyField(User, related_name='bus_routes', limit_choices_to={'role': 'student'})
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Route {self.name} - {self.driver.username}"

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
        UserLocation.objects.create(user=instance)

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.IntegerField(null=True, blank=True)
    parent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='children', limit_choices_to={'role': 'parent'})

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
    license_number = models.CharField(max_length=50, null=True, blank=True)

@receiver(post_save, sender=Driver)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.role == User.Role.DRIVER:
        DriverProfile.objects.create(user=instance)
        UserLocation.objects.create(user=instance)

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

# Signal to create UserLocation for all users
@receiver(post_save, sender=User)
def create_user_location(sender, instance, created, **kwargs):
    if created:
        UserLocation.objects.get_or_create(user=instance)