/**
 * Form Validation JavaScript for BusTrack Application
 * Provides real-time validation for login, signup, and profile forms
 */

class FormValidator {
    constructor() {
        this.emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        this.phoneRegex = /^\+?1?\d{9,15}$/;
        this.usernameRegex = /^[a-zA-Z0-9_]+$/;
        this.init();
    }

    init() {
        // Initialize validation for all forms on page load
        document.addEventListener('DOMContentLoaded', () => {
            this.setupFormValidation();
            this.setupPasswordStrength();
            this.setupRealTimeValidation();
        });
    }

    setupFormValidation() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        });
    }

    setupPasswordStrength() {
        const passwordFields = document.querySelectorAll('input[type="password"][name*="password1"]');
        passwordFields.forEach(field => {
            field.addEventListener('input', (e) => this.checkPasswordStrength(e.target));
        });
    }

    setupRealTimeValidation() {
        const inputs = document.querySelectorAll('.form-control');
        inputs.forEach(input => {
            input.addEventListener('blur', (e) => this.validateField(e.target));
            input.addEventListener('input', (e) => this.clearFieldErrors(e.target));
        });
    }

    handleFormSubmit(e) {
        const form = e.target;
        const isValid = this.validateForm(form);
        
        if (!isValid) {
            e.preventDefault();
            this.showFormError('Please fix the errors below before submitting.');
            return false;
        }

        // Show loading state
        this.showLoadingState(form);
        return true;
    }

    validateForm(form) {
        let isValid = true;
        const inputs = form.querySelectorAll('.form-control');
        
        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });

        return isValid;
    }

    validateField(field) {
        const value = field.value.trim();
        const fieldName = field.name;
        const fieldType = field.type;
        
        // Clear previous errors
        this.clearFieldErrors(field);

        // Skip validation for optional empty fields
        if (!value && !field.required) {
            return true;
        }

        // Required field validation
        if (field.required && !value) {
            this.showFieldError(field, `${this.getFieldLabel(field)} is required`);
            return false;
        }

        // Email validation
        if ((fieldType === 'email' || fieldName === 'email') && value) {
            if (!this.emailRegex.test(value)) {
                this.showFieldError(field, 'Please enter a valid email address');
                return false;
            }
        }

        // Username validation
        if (fieldName === 'username' && value) {
            if (value.length < 3) {
                this.showFieldError(field, 'Username must be at least 3 characters long');
                return false;
            }
            if (!this.usernameRegex.test(value)) {
                this.showFieldError(field, 'Username can only contain letters, numbers, and underscores');
                return false;
            }
        }

        // Phone number validation
        if ((fieldName.includes('phone') || fieldName.includes('Phone')) && value) {
            if (!this.phoneRegex.test(value)) {
                this.showFieldError(field, 'Please enter a valid phone number');
                return false;
            }
        }

        // Password validation
        if (fieldType === 'password' && fieldName.includes('password1') && value) {
            const passwordValidation = this.validatePassword(value);
            if (!passwordValidation.isValid) {
                this.showFieldError(field, passwordValidation.message);
                return false;
            }
        }

        // Password confirmation validation
        if (fieldName.includes('password2') && value) {
            const password1 = document.querySelector('input[name*="password1"]');
            if (password1 && value !== password1.value) {
                this.showFieldError(field, 'Passwords do not match');
                return false;
            }
        }

        // Name validation (no numbers or special characters)
        if ((fieldName === 'first_name' || fieldName === 'last_name') && value) {
            if (!/^[a-zA-Z\s]+$/.test(value)) {
                this.showFieldError(field, 'Name should only contain letters and spaces');
                return false;
            }
        }

        return true;
    }

    validatePassword(password) {
        const requirements = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /\d/.test(password)
        };

        const missingRequirements = [];
        if (!requirements.length) missingRequirements.push('at least 8 characters');
        if (!requirements.uppercase) missingRequirements.push('an uppercase letter');
        if (!requirements.lowercase) missingRequirements.push('a lowercase letter');
        if (!requirements.number) missingRequirements.push('a number');

        return {
            isValid: missingRequirements.length === 0,
            message: missingRequirements.length > 0 
                ? `Password must contain ${missingRequirements.join(', ')}`
                : 'Password is strong',
            requirements
        };
    }

    checkPasswordStrength(passwordField) {
        const password = passwordField.value;
        const strengthIndicator = document.getElementById('passwordStrength');
        const strengthFill = document.getElementById('strengthFill');
        const strengthText = document.getElementById('strengthText');

        if (!strengthIndicator) return;

        if (password.length === 0) {
            strengthIndicator.style.display = 'none';
            return;
        }

        strengthIndicator.style.display = 'block';

        const validation = this.validatePassword(password);
        const requirements = validation.requirements;
        
        let score = 0;
        if (requirements.length) score++;
        if (requirements.uppercase) score++;
        if (requirements.lowercase) score++;
        if (requirements.number) score++;

        // Special character bonus
        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score++;

        // Update strength indicator
        strengthFill.className = 'strength-fill';
        
        if (score <= 1) {
            strengthFill.classList.add('strength-weak');
            strengthText.textContent = 'Weak password';
        } else if (score <= 2) {
            strengthFill.classList.add('strength-fair');
            strengthText.textContent = 'Fair password';
        } else if (score <= 3) {
            strengthFill.classList.add('strength-good');
            strengthText.textContent = 'Good password';
        } else {
            strengthFill.classList.add('strength-strong');
            strengthText.textContent = 'Strong password!';
        }
    }

    showFieldError(field, message) {
        const formGroup = field.closest('.form-group');
        if (!formGroup) return;

        // Remove existing error
        const existingError = formGroup.querySelector('.error-message:not([class*="django"])');
        if (existingError) {
            existingError.remove();
        }

        // Add new error
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        formGroup.appendChild(errorDiv);

        // Style the field
        field.style.borderColor = '#e74c3c';
        field.classList.add('is-invalid');
    }

    clearFieldErrors(field) {
        const formGroup = field.closest('.form-group');
        if (!formGroup) return;

        // Remove custom error messages (not Django ones)
        const errorMessages = formGroup.querySelectorAll('.error-message:not([class*="django"])');
        errorMessages.forEach(error => {
            if (!error.innerHTML.includes('{{')) {
                error.remove();
            }
        });

        // Reset field styling
        field.style.borderColor = '#e1e5e9';
        field.classList.remove('is-invalid');
    }

    showFormError(message) {
        // Create or update form-level error message
        let errorContainer = document.querySelector('.form-error-message');
        
        if (!errorContainer) {
            errorContainer = document.createElement('div');
            errorContainer.className = 'error-message form-error-message';
            errorContainer.style.marginBottom = '20px';
            
            const form = document.querySelector('form');
            if (form) {
                form.insertBefore(errorContainer, form.firstChild);
            }
        }

        errorContainer.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    }

    showLoadingState(form) {
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        const loadingSpinner = document.getElementById('loadingSpinner');
        const btnText = document.getElementById('btnText');

        if (submitBtn) {
            submitBtn.disabled = true;
            
            if (loadingSpinner) {
                loadingSpinner.style.display = 'inline-block';
            }
            
            if (btnText) {
                const originalText = btnText.textContent;
                btnText.textContent = originalText.includes('Sign In') ? 'Signing In...' : 
                                    originalText.includes('Sign Up') ? 'Creating Account...' : 
                                    'Processing...';
            }
        }
    }

    getFieldLabel(field) {
        const label = field.closest('.form-group')?.querySelector('label');
        return label ? label.textContent.replace('*', '').trim() : field.name;
    }
}

// Initialize the form validator
new FormValidator();

// Additional utility functions
function togglePasswordVisibility(fieldId) {
    const field = document.getElementById(fieldId);
    const icon = field.nextElementSibling?.querySelector('i');
    
    if (field.type === 'password') {
        field.type = 'text';
        if (icon) icon.className = 'fas fa-eye-slash';
    } else {
        field.type = 'password';
        if (icon) icon.className = 'fas fa-eye';
    }
}

function validateEmailAvailability(email) {
    // This would typically make an AJAX call to check email availability
    // For now, we'll just return a promise
    return new Promise((resolve) => {
        setTimeout(() => {
            // Simulate API call
            resolve({ available: true });
        }, 500);
    });
}

function validateUsernameAvailability(username) {
    // This would typically make an AJAX call to check username availability
    // For now, we'll just return a promise
    return new Promise((resolve) => {
        setTimeout(() => {
            // Simulate API call
            resolve({ available: true });
        }, 500);
    });
}
