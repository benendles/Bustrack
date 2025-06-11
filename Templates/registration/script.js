// API Base URL
const API_BASE_URL = 'http://localhost:5000/api';

// Utility Functions
function validateEmail(email) {
    const re = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
    return re.test(email);
}

function validatePassword(password) {
    // At least 8 characters, one uppercase, one lowercase, one number
    const re = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    return re.test(password);
}

function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    errorElement.textContent = message;
    errorElement.classList.add('show');
    setTimeout(() => {
        errorElement.classList.remove('show');
    }, 5000);
}

function showSuccess(elementId, message) {
    const successElement = document.getElementById(elementId);
    successElement.textContent = message;
    successElement.classList.add('show');
    setTimeout(() => {
        successElement.classList.remove('show');
    }, 3000);
}

function toggleForms() {
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");
    loginForm.classList.toggle("hidden");
    signupForm.classList.toggle("hidden");

    // Clear error messages when switching forms
    document.getElementById("loginError").classList.remove('show');
    document.getElementById("signupError").classList.remove('show');
}

// Login Form Handler
async function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;
    const role = document.getElementById("loginRole").value;

    // Validation
    if (!validateEmail(email)) {
        showError("loginError", "Invalid email format.");
        return;
    }

    if (password.length < 8) {
        showError("loginError", "Password must be at least 8 characters.");
        return;
    }

    if (!role) {
        showError("loginError", "Please select a role.");
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password, role }),
        });

        const data = await response.json();

        if (response.ok) {
            // Store token in localStorage
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));

            // Redirect based on role
            redirectToDashboard(data.user.role);
        } else {
            showError("loginError", data.message || "Login failed.");
        }
    } catch (error) {
        showError("loginError", "Network error. Please try again.");
        console.error('Login error:', error);
    }
}

// Signup Form Handler
async function handleSignup(event) {
    event.preventDefault();

    const fullName = document.getElementById("fullName").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;
    const role = document.getElementById("role").value;

    // Validation
    if (!fullName.trim()) {
        showError("signupError", "Full name is required.");
        return;
    }

    if (!validateEmail(email)) {
        showError("signupError", "Invalid email format.");
        return;
    }

    if (!validatePassword(password)) {
        showError("signupError", "Password must be 8+ chars, include uppercase, lowercase, and number.");
        return;
    }

    if (password !== confirmPassword) {
        showError("signupError", "Passwords do not match.");
        return;
    }

    if (!role) {
        showError("signupError", "Please select a role.");
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/auth/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ fullName, email, password, role }),
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess("signupError", "Account created successfully! Please login.");
            // Clear form
            document.getElementById("signupForm").reset();
            // Switch to login form after a delay
            setTimeout(() => {
                toggleForms();
            }, 2000);
        } else {
            showError("signupError", data.message || "Signup failed.");
        }
    } catch (error) {
        showError("signupError", "Network error. Please try again.");
        console.error('Signup error:', error);
    }
}

function redirectToDashboard(role) {
    // For now, just show an alert. In a real app, you'd redirect to different dashboards
    alert(`Welcome! You are logged in as ${role}. Dashboard would load here.`);

    // Example redirects (you would create these pages):
    // switch(role) {
    //     case 'student':
    //         window.location.href = '/student-dashboard.html';
    //         break;
    //     case 'parent':
    //         window.location.href = '/parent-dashboard.html';
    //         break;
    //     case 'driver':
    //         window.location.href = '/driver-dashboard.html';
    //         break;
    //     case 'admin':
    //         window.location.href = '/admin-dashboard.html';
    //         break;
    // }
}

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');

    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }
});
