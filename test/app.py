from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production!

# Database Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'medicine_recommendation'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    if user_data:
        return User(user_data['id'], user_data['username'], user_data['role'])
    return None

# Helper Functions
def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def get_chat_participants(current_user_id, current_user_role):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    participants = {
        'experts': [],
        'patients': [],
        'admins': []
    }
    
    if current_user_role == 'admin':
        cursor.execute("SELECT * FROM users WHERE role = 'medical_expert'")
        participants['experts'] = cursor.fetchall()
    elif current_user_role == 'medical_expert':
        cursor.execute("SELECT * FROM users WHERE role = 'user'")
        participants['patients'] = cursor.fetchall()
        cursor.execute("SELECT * FROM users WHERE role = 'admin' AND id != %s", (current_user_id,))
        participants['admins'] = cursor.fetchall()
    else:  # user
        cursor.execute("SELECT * FROM users WHERE role = 'medical_expert'")
        participants['experts'] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return participants

# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        email = request.form['email']
        role = request.form['role']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)",
                (username, password, email, role)
            )
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data['id'], user_data['username'], user_data['role'])
            login_user(user)
            flash('Login successful!', 'success')
            
            # Redirect based on role
            if user_data['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user_data['role'] == 'medical_expert':
                return redirect(url_for('expert_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Admin Routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    
    participants = get_chat_participants(current_user.id, current_user.role)
    
    return render_template('admin/dashboard.html', experts=participants['experts'])

@app.route('/admin/add_expert', methods=['GET', 'POST'])
@login_required
def add_expert():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        email = request.form['email']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, 'medical_expert')",
                (username, password, email)
            )
            conn.commit()
            flash('Medical expert added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('admin/add_expert.html')

@app.route('/admin/manage_users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('admin/manage_users.html', users=users)

# User Routes
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.role != 'user':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    
    participants = get_chat_participants(current_user.id, current_user.role)
    
    return render_template('user/dashboard.html', experts=participants['experts'])

@app.route('/user/submit_symptoms', methods=['GET', 'POST'])
@login_required
def submit_symptoms():
    if current_user.role != 'user':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        symptoms_text = request.form['symptoms']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO symptoms (user_id, symptoms_text) VALUES (%s, %s)",
                (current_user.id, symptoms_text)
            )
            conn.commit()
            flash('Symptoms submitted successfully!', 'success')
            return redirect(url_for('view_recommendations'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('user/symptoms.html')

@app.route('/user/recommendations')
@login_required
def view_recommendations():
    if current_user.role != 'user':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT r.*, s.symptoms_text, s.submitted_at
        FROM recommendations r
        JOIN symptoms s ON r.symptom_id = s.id
        WHERE s.user_id = %s
        ORDER BY s.submitted_at DESC
    """, (current_user.id,))
    
    recommendations = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('user/recommendations.html', recommendations=recommendations)

# Medical Expert Routes
@app.route('/expert/dashboard')
@login_required
def expert_dashboard():
    if current_user.role != 'medical_expert':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    
    participants = get_chat_participants(current_user.id, current_user.role)
    
    # Get unread message counts
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT receiver_id, COUNT(*) as unread_count 
        FROM messages 
        WHERE receiver_id = %s AND read_status = 0
        GROUP BY receiver_id
    """, (current_user.id,))
    unread_counts = {msg['receiver_id']: msg['unread_count'] for msg in cursor.fetchall()}
    cursor.close()
    conn.close()
    
    return render_template('expert/dashboard.html', 
                         patients=participants['patients'],
                         admins=participants['admins'],
                         unread_counts=unread_counts)

@app.route('/expert/view_results')
@login_required
def view_results():
    if current_user.role != 'medical_expert':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT s.*, u.username 
        FROM symptoms s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.submitted_at DESC
    """)
    
    symptoms = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('expert/view_results.html', symptoms=symptoms)

@app.route('/expert/add_recommendation/<int:symptom_id>', methods=['POST'])
@login_required
def add_recommendation(symptom_id):
    if current_user.role != 'medical_expert':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    
    medicine = request.form['medicine']
    dosage = request.form['dosage']
    notes = request.form.get('notes', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO recommendations 
            (symptom_id, medicine_name, dosage, expert_notes, recommended_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (symptom_id, medicine, dosage, notes, current_user.id))
        
        conn.commit()
        flash('Recommendation added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('view_results'))

# Chat System Routes
@app.route('/chat/<int:receiver_id>', methods=['GET', 'POST'])
@login_required
def chat(receiver_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Handle message submission
    if request.method == 'POST':
        message = request.form['message']
        try:
            cursor.execute("""
                INSERT INTO messages (sender_id, receiver_id, message)
                VALUES (%s, %s, %s)
            """, (current_user.id, receiver_id, message))
            conn.commit()
        except mysql.connector.Error as err:
            flash(f'Error sending message: {err}', 'danger')
    
    # Mark messages as read
    cursor.execute("""
        UPDATE messages SET read_status = 1 
        WHERE receiver_id = %s AND sender_id = %s AND read_status = 0
    """, (current_user.id, receiver_id))
    conn.commit()
    
    # Get receiver info
    cursor.execute("SELECT * FROM users WHERE id = %s", (receiver_id,))
    receiver = cursor.fetchone()
    
    # Get chat participants based on role
    participants = get_chat_participants(current_user.id, current_user.role)
    
    # Get chat history
    cursor.execute("""
        SELECT m.*, u1.username as sender_name, u2.username as receiver_name
        FROM messages m
        JOIN users u1 ON m.sender_id = u1.id
        JOIN users u2 ON m.receiver_id = u2.id
        WHERE (m.sender_id = %s AND m.receiver_id = %s)
        OR (m.sender_id = %s AND m.receiver_id = %s)
        ORDER BY m.sent_at
    """, (current_user.id, receiver_id, receiver_id, current_user.id))
    
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not receiver:
        flash('User not found', 'danger')
        return redirect(url_for(f'{current_user.role}_dashboard'))
    
    template_map = {
        'admin': 'admin/chat.html',
        'user': 'user/chat.html',
        'medical_expert': 'expert/chat.html'
    }
    
    return render_template(template_map[current_user.role],
                         messages=messages,
                         receiver=receiver,
                         experts=participants['experts'],
                         patients=participants['patients'],
                         admins=participants['admins'],
                         current_user=current_user)

# API Endpoint for Unread Messages Count
@app.route('/api/unread_count')
@login_required
def unread_count():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM messages 
        WHERE receiver_id = %s AND read_status = 0
    """, (current_user.id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({'unread_count': result['count'] if result else 0})

if __name__ == '__main__':
    app.run(debug=True)