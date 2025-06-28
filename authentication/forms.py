from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from .models import User, PaymentReceipt, ParentChildConnection
import re

class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name',
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name',
            'autocomplete': 'family-name'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1234567890',
            'autocomplete': 'tel'
        })
    )
    # Exclude admin role from regular user registration
    REGULAR_USER_ROLES = [
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('driver', 'Driver'),
    ]

    role = forms.ChoiceField(
        choices=REGULAR_USER_ROLES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'role', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username',
                'autocomplete': 'username'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long.")
        if not re.match("^[a-zA-Z0-9_]+$", username):
            raise ValidationError("Username can only contain letters, numbers, and underscores.")
        return username

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            if len(password1) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            if not re.search(r'[A-Z]', password1):
                raise ValidationError("Password must contain at least one uppercase letter.")
            if not re.search(r'[a-z]', password1):
                raise ValidationError("Password must contain at least one lowercase letter.")
            if not re.search(r'\d', password1):
                raise ValidationError("Password must contain at least one digit.")
        return password1

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and not re.match(r'^\+?1?\d{9,15}$', phone):
            raise ValidationError("Enter a valid phone number.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        if commit:
            user.save()
        return user


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        })
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Try to authenticate with username first
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )

            # If that fails, try with email
            if self.user_cache is None:
                try:
                    user_obj = User.objects.get(email=username)
                    self.user_cache = authenticate(
                        self.request,
                        username=user_obj.username,
                        password=password
                    )
                except User.DoesNotExist:
                    pass

            if self.user_cache is None:
                raise ValidationError("Invalid username/email or password.")
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class AdminSignUpForm(UserCreationForm):
    """Special form for admin registration with enhanced security"""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter admin email address',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name',
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name',
            'autocomplete': 'family-name'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=True,  # Required for admin
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1234567890',
            'autocomplete': 'tel'
        })
    )
    admin_code = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter admin registration code',
            'autocomplete': 'off'
        }),
        help_text="Contact system administrator for the registration code"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'admin_code', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose an admin username',
                'autocomplete': 'username'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")

        # Additional validation for admin emails (optional)
        if email and not email.endswith(('@school.edu', '@admin.bustrack.com')):
            # You can customize this validation based on your requirements
            pass  # Remove this restriction if not needed

        return email

    def clean_admin_code(self):
        admin_code = self.cleaned_data.get('admin_code')
        # You should store this in settings or database
        VALID_ADMIN_CODES = ['ADMIN2024', 'BUSTRACK_ADMIN', 'SCHOOL_ADMIN_2024']

        if admin_code not in VALID_ADMIN_CODES:
            raise ValidationError("Invalid admin registration code. Contact system administrator.")

        return admin_code

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 5:  # Stricter requirement for admin
            raise ValidationError("Admin username must be at least 5 characters long.")
        if not re.match("^[a-zA-Z0-9_]+$", username):
            raise ValidationError("Username can only contain letters, numbers, and underscores.")
        return username

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            # Stricter password requirements for admin
            if len(password1) < 10:
                raise ValidationError("Admin password must be at least 10 characters long.")
            if not re.search(r'[A-Z]', password1):
                raise ValidationError("Password must contain at least one uppercase letter.")
            if not re.search(r'[a-z]', password1):
                raise ValidationError("Password must contain at least one lowercase letter.")
            if not re.search(r'\d', password1):
                raise ValidationError("Password must contain at least one digit.")
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
                raise ValidationError("Password must contain at least one special character.")
        return password1

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.role = User.Role.ADMIN  # Set role to admin
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address',
                 'emergency_contact', 'emergency_phone', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("A user with this email already exists.")
        return email


class PaymentReceiptForm(forms.ModelForm):
    """Form for students to submit payment receipts"""

    class Meta:
        model = PaymentReceipt
        fields = ['receipt_image', 'amount', 'payment_date', 'description']
        widgets = {
            'receipt_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional: Add any notes about this payment'
            }),
        }

    def clean_receipt_image(self):
        image = self.cleaned_data.get('receipt_image')
        if image:
            # Check file size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("Image file too large. Maximum size is 5MB.")

            # Check file type
            if not image.content_type.startswith('image/'):
                raise ValidationError("Please upload a valid image file.")

        return image

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        return amount


class ReceiptVerificationForm(forms.ModelForm):
    """Form for admins to verify payment receipts"""

    class Meta:
        model = PaymentReceipt
        fields = ['status', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'admin_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add notes about the verification decision...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show approved/rejected options for admin
        self.fields['status'].choices = [
            ('approved', 'Approve'),
            ('rejected', 'Reject'),
        ]


class ParentChildSearchForm(forms.Form):
    """Form for parents to search for their children"""

    search_query = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter child\'s username, name, or email',
            'autocomplete': 'off'
        }),
        help_text="Search by username, first name, last name, or email"
    )

    def clean_search_query(self):
        query = self.cleaned_data.get('search_query')
        if query and len(query.strip()) < 2:
            raise ValidationError("Search query must be at least 2 characters long.")
        return query.strip()


class ConnectionResponseForm(forms.ModelForm):
    """Form for students to respond to parent connection requests"""

    class Meta:
        model = ParentChildConnection
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show approve/reject options
        self.fields['status'].choices = [
            ('approved', 'Accept Connection'),
            ('rejected', 'Reject Connection'),
        ]