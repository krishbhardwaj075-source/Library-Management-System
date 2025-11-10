from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# ---------------------- Database Models ----------------------
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Auto-generated Member ID
    member_id = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    def __init__(self, name, email, phone):
        self.name = name
        self.email = email
        self.phone = phone
        # Generate unique member_id like M001, M002, ...
        last_member = Member.query.order_by(Member.id.desc()).first()
        if last_member:
            num = int(last_member.member_id[1:]) + 1
        else:
            num = 1
        self.member_id = f"M{num:03d}"
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    copies = db.Column(db.Integer, default=1)
class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Issued")
    member = db.relationship('Member', backref=db.backref('issues', lazy=True))
    book = db.relationship('Book', backref=db.backref('issues', lazy=True))
# ---------------------- Create Tables ----------------------
with app.app_context():
    db.create_all()
# ---------------------- Routes ----------------------
@app.route('/')
def index():
    books = Book.query.all()
    members = Member.query.all()
    issued_books = Issue.query.all()
    return render_template('index.html', books=books, members=members, issued_books=issued_books)
# Add Member
@app.route('/add_member', methods=['POST'])
def add_member():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']

    # Check if email already exists
    if Member.query.filter_by(email=email).first():
        return redirect(url_for('index'))

    new_member = Member(name=name, email=email, phone=phone)
    db.session.add(new_member)
    db.session.commit()
    return redirect(url_for('index'))
# Add Book
@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form['title']
    author = request.form['author']
    copies = request.form['copies']
    # Validate copies
    try:
        copies = int(copies)
        if copies < 1:
            copies = 1
    except ValueError:
        copies = 1
    new_book = Book(title=title, author=author, copies=copies)
    db.session.add(new_book)
    db.session.commit()
    return redirect(url_for('index'))
# Issue Book
@app.route('/issue_book', methods=['POST'])
def issue_book():
    member_id_str = request.form['member_id']  # e.g., 'M001'
    book_id_str = request.form['book_id']      # e.g., '1'
    # Convert Book ID to integer
    try:
        book_id = int(book_id_str)
    except ValueError:
        return redirect(url_for('index'))  # invalid input
    # Find member by Member ID
    member = Member.query.filter_by(member_id=member_id_str).first()
    book = Book.query.get(book_id)
    # Only issue if book exists, member exists, and copies available
    if book and book.copies > 0 and member:
        issue = Issue(member_id=member.id, book_id=book.id)
        book.copies -= 1
        db.session.add(issue)
        db.session.commit()
    return redirect(url_for('index'))
# Return Book
@app.route('/return_book/<int:issue_id>')
def return_book(issue_id):
    issue = Issue.query.get(issue_id)
    if issue and issue.status == "Issued":
        issue.status = "Returned"
        issue.book.copies += 1
        db.session.commit()
    return redirect(url_for('index'))
# ---------------------- Run Server ----------------------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
