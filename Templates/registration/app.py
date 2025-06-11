from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import bcrypt
import jwt
import datetime
import os
import re
from functools import wraps

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'your-super-secret-key-change-this-in-production'
DATABASE = 'school_bus.db'

# Database initialization
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('student', 'parent', 'driver', 'admin')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create default admin user
    cursor.execute('SELECT id FROM users WHERE email = ? AND role = ?', ('admin@schoolbus.com', 'admin'))
    if not cursor.fetchone():
        hashed_password = bcrypt.hashpw('Admin123!'.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('''
            INSERT INTO users (full_name, email, password, role) 
            VALUES (?, ?, ?, ?)
        ''', ('System Administrator', 'admin@schoolbus.com', hashed_password, 'admin'))
        print("Default admin user created:")
        print("Email: admin@schoolbus.com")
        print("Password: Admin123!")
    
    conn.commit()
    conn.close()

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user

def create_user(full_name, email, password, role):
    conn = get_db_connection()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor = conn.execute('''
        INSERT INTO users (full_name, email, password, role) 
        VALUES (?, ?, ?, ?)
    ''', (full_name, email, hashed_password, role))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

# JWT token functions
def generate_token(user):
    payload = {
        'id': user['id'],
        'email': user['email'],
        'role': user['role'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401
        
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            data = verify_token(token)
            if not data:
                return jsonify({'success': False, 'message': 'Token is invalid'}), 401
            current_user = data
        except:
            return jsonify({'success': False, 'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

# Validation functions
def validate_email(email):
    pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
    return re.match(pattern, email) is not None

def validate_password(password):
    # At least 8 characters, one uppercase, one lowercase, one number
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'
    return re.match(pattern, password) is not None

# Routes
@app.route('/')
def index():
    return send_from_directory('htl', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('htl', filename)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'success': True,
        'message': 'School Bus System API is running!',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['fullName', 'email', 'password', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field} is required.'
                }), 400
        
        full_name = data['fullName'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        role = data['role']
        
        # Validate email format
        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Invalid email format.'
            }), 400
        
        # Validate password strength
        if not validate_password(password):
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters with uppercase, lowercase, and number.'
            }), 400
        
        # Validate role
        valid_roles = ['student', 'parent', 'driver']
        if role not in valid_roles:
            return jsonify({
                'success': False,
                'message': 'Invalid role selected.'
            }), 400
        
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'User with this email already exists.'
            }), 409
        
        # Create user
        user_id = create_user(full_name, email, password, role)
        
        return jsonify({
            'success': True,
            'message': 'User created successfully.'
        }), 201
        
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error.'
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['email', 'password', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field} is required.'
                }), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        role = data['role']
        
        # Get user by email
        user = get_user_by_email(email)
        if not user:
            return jsonify({
                'success': False,
                'message': 'Invalid credentials.'
            }), 401
        
        # Check if role matches
        if user['role'] != role:
            return jsonify({
                'success': False,
                'message': 'Invalid role for this account.'
            }), 401
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return jsonify({
                'success': False,
                'message': 'Invalid credentials.'
            }), 401
        
        # Generate token
        token = generate_token(user)
        
        return jsonify({
            'success': True,
            'message': 'Login successful.',
            'token': token,
            'user': {
                'id': user['id'],
                'fullName': user['full_name'],
                'email': user['email'],
                'role': user['role']
            }
        })
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error.'
        }), 500

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    conn = get_db_connection()
    user = conn.execute('SELECT id, full_name, email, role, created_at FROM users WHERE id = ?', 
                       (current_user['id'],)).fetchone()
    conn.close()
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found.'
        }), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'fullName': user['full_name'],
            'email': user['email'],
            'role': user['role'],
            'createdAt': user['created_at']
        }
    })

if __name__ == '__main__':
    init_db()
    print("🚌 School Bus System server starting...")
    print("📱 Frontend available at: http://localhost:5000")
    print("🔗 API available at: http://localhost:5000/api")
    print("🏥 Health check: http://localhost:5000/api/health")
    app.run(debug=True, host='0.0.0.0', port=5000)
