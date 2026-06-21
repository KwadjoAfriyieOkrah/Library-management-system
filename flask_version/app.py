from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db():
    connection = sqlite3.connect("library.db")
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            author TEXT NOT NULL,
            status TEXT DEFAULT 'available',
            borrowed_by TEXT
        )
    """)
    connection.commit()
    connection.close()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/books")
def books():
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM books")
    all_books = cursor.fetchall()
    connection.close()
    return render_template("books.html", books=all_books)

@app.route("/add-book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        title = request.form["title"].strip().title()
        author = request.form["author"].strip().title()

        if title and author:
            try:
                connection = get_db()
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO books (title, author) VALUES (?, ?)",
                    (title, author)
                )
                connection.commit()
                connection.close()
            except sqlite3.IntegrityError:
                return render_template("add_book.html",
                                       error=f"'{title}' already exists!")

        return redirect(url_for("books"))
    return render_template("add_book.html")

@app.route("/borrow/<int:book_id>", methods=["GET", "POST"])
def borrow_book(book_id):
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()

    if not book:
        connection.close()
        return redirect(url_for("books"))

    if request.method == "POST":
        borrower = request.form["borrower"].strip().title()
        if borrower:
            cursor.execute("""
                UPDATE books
                SET status = 'borrowed', borrowed_by = ?
                WHERE id = ?
            """, (borrower, book_id))
            connection.commit()
        connection.close()
        return redirect(url_for("books"))

    connection.close()
    return render_template("borrow_book.html", book=book)

@app.route("/return/<int:book_id>")
def return_book(book_id):
    connection = get_db()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE books
        SET status = 'available', borrowed_by = NULL
        WHERE id = ?
    """, (book_id,))
    connection.commit()
    connection.close()
    return redirect(url_for("books"))

@app.route("/search")
def search():
    search_term = request.args.get("q", "").strip()
    books = []

    if search_term:
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ?
        """, (f"%{search_term}%", f"%{search_term}%"))
        books = cursor.fetchall()
        connection.close()

    return render_template("search.html",
                           books=books,
                           search_term=search_term)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)