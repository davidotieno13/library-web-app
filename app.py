from flask import Flask, render_template, request, redirect, session
import sqlite3

# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.secret_key = "library_secret_key"

DB_NAME = "library.db"

# ---------------- USERS ----------------
users = {
    "admin": "1234",
    "user": "1111"
}

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            subject TEXT,
            shelf TEXT,
            row TEXT,
            position TEXT,
            available TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------------- LOGIN ROUTE ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["user"] = username
            return redirect("/")

        return "Invalid login"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# ---------------- HOME PAGE ----------------
@app.route("/", methods=["GET"])
def home():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    search = request.args.get("search")

if search:
    cursor.execute("""
        SELECT * FROM books
        WHERE title LIKE ? OR author LIKE ? OR subject LIKE ?
    """, (f"%{search}%", f"%{search}%", f"%{search}%"))
else:
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    conn.close()

    return render_template("index.html", books=books)


# ---------------- ADD BOOK ----------------
@app.route("/add", methods=["POST"])
def add():
    if session.get("user") != "admin":
        return "Access Denied"
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO books (title, author, subject, shelf, row, position, available)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        request.form["title"],
        request.form["author"],
        request.form["subject"],
        request.form["shelf"],
        request.form["row"],
        request.form["position"],
        "True"
    ))

    conn.commit()
    conn.close()

    return redirect("/")


import os

# ---------------- START APP ----------------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
