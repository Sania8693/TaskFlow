import sqlite3
from flask import Flask, render_template,request

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

    conn.commit()
    conn.close()
app = Flask(__name__)
init_db()

@app.route('/')
def home():
    return render_template("index.html")
@app.route('/login')
def login():
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
        return "User registered successfully"
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)
