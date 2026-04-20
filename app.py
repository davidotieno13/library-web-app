from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "library_secret_key")

DB = "library.db"

# ---------------- USERS ----------------
users = {
    "admin": "1234",
    "user": "1111"
}

# ---------------- INIT DB ----------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            isbn TEXT,
            publisher TEXT,
            year TEXT,
            edition TEXT,
            category TEXT,
            copies INTEGER,
            shelf TEXT,
            available INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS borrowed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            book_id INTEGER,
            borrow_date TEXT,
            due_date TEXT,
            returned INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u in users and users[u] == p:
            session["user"] = u
            return redirect("/")

        return "Invalid login"

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- HOME ----------------
@app.route("/", methods=["GET"])
def home():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    search = request.args.get("search")

    if search:
        c.execute("""
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ? OR category LIKE ?
        """, (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        c.execute("SELECT * FROM books")

    books = c.fetchall()
    conn.close()

    return render_template("index.html", books=books)


# ---------------- ADD BOOK ----------------
@app.route("/add", methods=["POST"])
def add():
    if session.get("user") != "admin":
        return "Access Denied"

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    copies = int(request.form["copies"])

    c.execute("""
        INSERT INTO books (
            title, author, isbn, publisher, year,
            edition, category, copies, shelf, available
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        request.form["title"],
        request.form["author"],
        request.form["isbn"],
        request.form["publisher"],
        request.form["year"],
        request.form["edition"],
        request.form["category"],
        copies,
        request.form["shelf"],
        copies
    ))

    conn.commit()
    conn.close()

    return redirect("/")


# ---------------- BORROW BOOK ----------------
@app.route("/borrow/<int:book_id>")
def borrow(book_id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT available FROM books WHERE id=?", (book_id,))
    book = c.fetchone()

    if book and book[0] > 0:
        borrow_date = datetime.now()
        due_date = borrow_date + timedelta(days=14)

        c.execute("""
            INSERT INTO borrowed (user, book_id, borrow_date, due_date, returned)
            VALUES (?, ?, ?, ?, 0)
        """, (session["user"], book_id, borrow_date, due_date))

        c.execute("""
            UPDATE books SET available = available - 1 WHERE id=?
        """, (book_id,))

    conn.commit()
    conn.close()

    return redirect("/")


# ---------------- RETURN BOOK ----------------
@app.route("/return/<int:borrow_id>")
def return_book(borrow_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT book_id FROM borrowed WHERE id=?", (borrow_id,))
    book_id = c.fetchone()[0]

    c.execute("UPDATE borrowed SET returned=1 WHERE id=?", (borrow_id,))
    c.execute("UPDATE books SET available = available + 1 WHERE id=?", (book_id,))

    conn.commit()
    conn.close()

    return redirect("/")


# ---------------- START ----------------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
