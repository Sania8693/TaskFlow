import sqlite3
import os
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, url_for, send_file, jsonify
from werkzeug.utils import secure_filename
app=Flask(__name__)
app.secret_key="secret_key_for_session"

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Absolute path for database - persists in current directory
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "database.db"))

def getdb():
    """Get database connection with absolute path"""
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    """Initialize database tables if they don't exist"""
    conn = getdb()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            priority TEXT,
            due_date DATE,
            user_id INTEGER,
            category TEXT,
            file_path TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")

def chatbot_response(message):
    """Return a chatbot answer based on a user's message."""
    if not message:
        return "Please type your question so I can help."

    text = message.lower()

    greeting_responses = [
        "Hello! I'm SmartTask, your task assistant. Ask me anything about registration, login, or task management.",
        "Hi there! I can help you register, log in, create tasks, and understand how the dashboard works.",
    ]

    register_responses = [
        "Start by clicking 'Get Started', then fill the registration form with your username, email, and password.",
        "Register first using the link on the homepage. After registration, you can log in and create tasks right away.",
    ]

    login_responses = [
        "Use the Login button in the top nav to sign in with your email and password.",
        "If you already have an account, log in and your task dashboard will appear instantly.",
    ]

    task_responses = [
        "After logging in, go to task creation and add a title, description, due date, and optional category.",
        "Each task you add gets a priority automatically based on the description, so you can focus on what matters.",
    ]

    priority_responses = [
        "Tasks are labeled HIGH, MEDIUM, or LOW based on keyword importance like urgent, critical, update, and improve.",
        "The AI logic checks your task description for urgency words and assigns a priority to help you plan better.",
    ]

    dashboard_responses = [
        "Your dashboard shows totals, pending tasks, in-progress work, completed tasks, and priority counts.",
        "The admin dashboard gives an overview of all tasks, while the user dashboard shows only your own tasks.",
    ]

    if any(greet in text for greet in ["hi", "hello", "hey", "greetings"]):
        return random.choice(greeting_responses)

    if any(word in text for word in ["register", "sign up", "create account"]):
        return random.choice(register_responses)

    if any(word in text for word in ["login", "sign in", "log in"]):
        return random.choice(login_responses)

    if any(word in text for word in ["task", "create", "add task", "new task"]):
        return random.choice(task_responses)

    if any(word in text for word in ["priority", "classify", "ai", "urgent", "critical"]):
        return random.choice(priority_responses)

    if any(word in text for word in ["dashboard", "analytics", "progress", "completed", "pending", "in progress"]):
        return random.choice(dashboard_responses)

    if "due date" in text or "deadline" in text:
        return "You can include a due date when creating a task so the system stores it and you can track deadlines from your dashboard."

    if "password" in text and "forgot" not in text:
        return "Make sure you use the correct registered email and password when logging in. If you forgot your password, register again or add a recovery feature later."

    if any(word in text for word in ["forgot", "reset"]):
        return "This version does not have a password reset flow yet, so please use your existing credentials or register a new account."

    if any(word in text for word in ["bye", "thanks", "thank you", "see you"]):
        return random.choice([
            "You're welcome! If you want, I can help with another question.",
            "Glad I could help. Close the chat when you're done and I'll reset the conversation next time.",
        ])

    if any(word in text for word in ["who are you", "your name", "yourself"]):
        return "I'm SmartTask Assistant, here to help you register, log in, create tasks, and understand your dashboard."

    default_responses = [
        "I can answer questions about registration, login, task creation, priorities, and dashboards. What would you like to know?",
        "Try asking how to add a task, how priority classification works, or how to view your dashboard.",
    ]
    return random.choice(default_responses)

@app.route('/chatbot', methods=['POST'])
def chatbot():
    user_message = request.json.get('message') if request.is_json else request.form.get('message')
    reply = chatbot_response(user_message)
    return jsonify({'reply': reply})

def ai_priority_logic(description):
    #intelligent logic for automatic priority assignment
    desc=description.lower()
    high_keywords=['urgent','immediate','critical','fix','error','important']
    medium_keywords=['update','improve','change','moderate']
    if any(word in desc for word in high_keywords):
        return "HIGH"
    elif any(word in desc for word in medium_keywords):
        return "MEDIUM"
    else:
        return "LOW"
@app.route('/')
def home():
    return render_template("index.html")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = getdb()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users 
            WHERE email = ? AND password = ?
        """, (email, password))

        user = cursor.fetchone()

        conn.close()

        if user:
            session['user_id']=user[0]
            session['username']=user[1]
            session['email']=user[2]
            session['role']=user[4]
            session['login_time'] = datetime.now().strftime("%B %d, %Y at %I:%M %p")

            return render_template("login_success.html", username=user[1], email=user[2], role=user[4], login_time=session['login_time'])
        return "Invalid credentials"
    return render_template("login.html")

@app.route('/logout')
def logout():
    """Logout user and clear session"""
    session.clear()
    return redirect(url_for("login"))

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']

        conn=getdb()
        cursor=conn.cursor()

        cursor.execute("""INSERT INTO users(username,email,password)
                       VALUES(?,?,?)
                       """,(username,email,password))
        conn.commit()
        conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/user_dashboard")
def user_dashboard():
    user_id=session.get('user_id')
    if 'user_id' not in session:
        return redirect(url_for("login"))
    conn=getdb()
    cursor=conn.cursor()
    # Fetch all task details to display in the UI table.
    cursor.execute("SELECT * FROM tasks WHERE user_id=?", (user_id,))
    tasks = cursor.fetchall()
    #Total tasks for user
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id=?", (user_id,))
    total = cursor.fetchone()[0]
    # Pending
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND status='Pending'", (user_id,))
    pending = cursor.fetchone()[0]

    # In Progress
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND status='In Progress'", (user_id,))
    inprogress= cursor.fetchone()[0]

    # Completed
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND status='Completed'", (user_id,))
    completed= cursor.fetchone()[0]
    # high priority tasks
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND priority='HIGH'", (user_id,))
    high_priority = cursor.fetchone()[0]
    conn.close()
    return render_template("user_dashboard.html",alltasks=tasks,total_tasks=total,pending_tasks=pending,inprogresstas=inprogress,high=high_priority,completed=completed)

@app.route("/setup_admin")
def setup_admin():
    conn=getdb()
    cursor=conn.cursor()
    cursor.execute("""INSERT INTO users(username,email,password,role)
                       VALUES(?,?,?,?)
                       """,("admin","admin@gmail.com","admin123","admin"))
    conn.commit()
    conn.close()
    return "admin created"
    
@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if request.method == "GET":
        # Check if user is logged in
        if 'user_id' not in session:
            return redirect(url_for("login"))
        # Display the form
        return render_template("add_task.html")
    
    # POST request - handle form submission
    if request.method == "POST":
        user_id = session.get('user_id')
        if 'user_id' not in session:
            return redirect(url_for("login"))
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        category = request.form.get('category', '')  # Optional field
        priority = ai_priority_logic(description)
        
        # Handle file upload
        file_path = None
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
        
        conn = getdb()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO tasks(title,description,due_date,priority,user_id,category,file_path)
                           VALUES(?,?,?,?,?,?,?)
                           """, (title, description, due_date, priority, session['user_id'], category, file_path))
        conn.commit()
        conn.close()
        return redirect(url_for("user_dashboard"))
@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get('role')!='admin':
        return "Access denied"
    conn = getdb()
    cursor = conn.cursor()

    # Get tasks with user information
    cursor.execute("""
        SELECT t.id, t.title, t.description, t.status, t.priority, t.due_date, t.user_id, u.username, t.category, t.file_path
        FROM tasks t
        LEFT JOIN users u ON t.user_id = u.id
        ORDER BY t.priority DESC
    """)
    all_task=cursor.fetchall()
    
    # Get statistics for all tasks
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total_tasks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE priority='HIGH'")
    high_priority = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status='Completed'")
    completed = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status='Pending'")
    pending = cursor.fetchone()[0]
    
    conn.close()

    return render_template("admin_dashboard.html", tasks=all_task, total_tasks=total_tasks, high=high_priority, completed=completed, pending_tasks=pending)

@app.route("/manage_tasks")
def manage_tasks():
    if session.get('role')!='admin':
        return redirect(url_for("login"))
    
    conn = getdb()
    cursor = conn.cursor()
    
    # Get all tasks with user information
    cursor.execute("""
        SELECT t.id, t.title, t.description, t.status, t.priority, t.due_date, t.user_id, u.username, t.category, t.file_path
        FROM tasks t
        LEFT JOIN users u ON t.user_id = u.id
        ORDER BY t.priority DESC
    """)
    tasks = cursor.fetchall()
    
    conn.close()
    
    return render_template("manage_tasks.html", tasks=tasks)

@app.route("/manage_users")
def manage_users():
    if session.get('role') != 'admin':
        return redirect(url_for("login"))
    
    conn = getdb()
    cursor = conn.cursor()
    
    # Fetch all users
    cursor.execute("SELECT id, username, email, role FROM users ORDER BY username")
    users = cursor.fetchall()
    
    conn.close()
    
    return render_template("manage_users.html", users=users)

@app.route("/my_tasks")
def my_tasks():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    
    user_id = session.get('user_id')
    conn = getdb()
    cursor = conn.cursor()
    
    # Fetch user's tasks
    cursor.execute("SELECT * FROM tasks WHERE user_id = ? ORDER BY priority DESC, due_date ASC", (user_id,))
    tasks = cursor.fetchall()
    
    conn.close()
    
    return render_template("my_tasks.html", tasks=tasks)

@app.route("/start_task/<int:task_id>")
def start_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for("login"))
    
    user_id = session.get('user_id')
    conn = getdb()
    cursor = conn.cursor()
    
    # Verify task belongs to user and update status
    cursor.execute("UPDATE tasks SET status = 'In Progress' WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for("my_tasks"))

@app.route("/complete_task/<int:task_id>")
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for("login"))
    
    user_id = session.get('user_id')
    conn = getdb()
    cursor = conn.cursor()
    
    # Verify task belongs to user and update status
    cursor.execute("UPDATE tasks SET status = 'Completed' WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for("my_tasks"))

@app.route("/download/<int:task_id>")
def download_file(task_id):
    if 'user_id' not in session:
        return redirect(url_for("login"))
    
    user_id = session.get('user_id')
    conn = getdb()
    cursor = conn.cursor()
    
    # Verify task belongs to user and get file path
    cursor.execute("SELECT file_path FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0]:
        file_path = result[0]
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
    
    return "File not found", 404

@app.route("/admin_start_task/<int:task_id>")
def admin_start_task(task_id):
    if session.get('role') != 'admin':
        return redirect(url_for("login"))
    
    conn = getdb()
    cursor = conn.cursor()
    
    # Update task status to In Progress
    cursor.execute("UPDATE tasks SET status = 'In Progress' WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for("admin_dashboard"))

@app.route("/admin_complete_task/<int:task_id>")
def admin_complete_task(task_id):
    if session.get('role') != 'admin':
        return redirect(url_for("login"))
    
    conn = getdb()
    cursor = conn.cursor()
    
    # Update task status to completed
    cursor.execute("UPDATE tasks SET status = 'Completed' WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for("admin_dashboard"))

@app.route("/admin_download/<int:task_id>")
def admin_download_file(task_id):
    if session.get('role') != 'admin':
        return redirect(url_for("login"))
    
    conn = getdb()
    cursor = conn.cursor()
    
    # Get file path for the task
    cursor.execute("SELECT file_path FROM tasks WHERE id = ?", (task_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0]:
        file_path = result[0]
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
    
    return "File not found", 404

@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for("login"))
    
    # Prevent deleting admin users
    conn = getdb()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    user_role = cursor.fetchone()
    
    if user_role and user_role[0] == 'admin':
        conn.close()
        return redirect(url_for("manage_users"))
    
    # Delete user's tasks first, then the user
    cursor.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for("manage_users"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
