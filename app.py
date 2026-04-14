import sqlite3
from flask import Flask, render_template,request,redirect,session,url_for
app=Flask(__name__)
app.secret_key="secret_key_for_session"

def init_db():
    conn = sqlite3.connect("database.db")
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
            FOREIGN KEY (user_id) REFERENCES users(id)

        )
    """)
    conn.commit()
    conn.close()
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

        conn = sqlite3.connect("database.db")
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
            session['role']=user[4]
            if session['role']=="admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("user_dashboard"))
        return "ivalid credentials"
    return render_template("login.html")

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']

        conn=sqlite3.connect("database.db")
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
    conn=sqlite3.connect("database.db")
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
    return render_template("user_dashboard.html",alltasks=tasks,total_tasks=total,pending_tasks=pending,inprogresstas=inprogress,high=high_priority)

@app.route("/setup_admin")
def setup_admin():
    conn=sqlite3.connect("database.db")
    cursor=conn.cursor()
    cursor.execute("""INSERT INTO users(username,email,password,role)
                       VALUES(?,?,?,?)
                       """,("admin","admin@gmail.com","admin123","admin"))
    conn.commit()
    conn.close()
    return "admin created"
    

@app.route("/create_task",methods=["POST"])
def create_task():
    user_id=session.get('user_id')
    if 'user_id' not in session:
        return redirect(url_for("login"))
    title=request.form['title']
    description=request.form['description']
    due_date=request.form['due_date']
    priority=ai_priority_logic(description)
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO tasks(title,description,due_date,priority,user_id)
                       VALUES(?,?,?,?,?)
                       """,(title,description,due_date,priority,session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for("user_dashboard"))
@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get('role')!='admin':
        return "Access denied"
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks ORDER BY priority DESC")
    all_task=cursor.fetchall()
    conn.close()

    return render_template("admin_dashboard.html",tasks=all_task)
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
