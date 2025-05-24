from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import SignUpForm
def home(request):
    return render(request, 'home.html')

#def ChooseDashboard(request):
    #return render(request, 'chooseDashboard.html')

def student_dashboard(request):
    print(request.user)
    return render(request, 'student_dashboard.html')

def driver_dashboard(request):

    return render(request, 'driver_dashboard.html')

def parent_dashboard(request):
    return render(request, 'parent_dashboard')

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