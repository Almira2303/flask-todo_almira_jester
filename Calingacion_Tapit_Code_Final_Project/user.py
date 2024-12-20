import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import bleach
import os


app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for flashing messages
bcrypt = Bcrypt(app)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Setup logging
log_handler = RotatingFileHandler('todo_app.log', maxBytes=10000, backupCount=3)
log_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)

app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(100))  # Store hashed password


# Todo model
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    priority = db.Column(db.String(10), default="Low")  # New field
    complete = db.Column(db.Boolean, default=False)

# Validate the priority level
def validate_priority(priority):
    """Validate priority input."""
    return priority in ["Low", "Medium", "High"]

# Home route to display tasks
@app.route("/")
def home():
    try:
        if 'username' not in session:
            return redirect(url_for('login'))

        page = request.args.get('page', 1, type=int)
        per_page = 5
        todo_pagination = Todo.query.paginate(page=page, per_page=per_page)

        return render_template(
            "base.html",
            todo_list=todo_pagination.items,
            pagination=todo_pagination
        )
    except Exception as e:
        app.logger.error(f"Error in home: {e}")
        flash("An error occurred while loading tasks.")
        return redirect(url_for("login"))

# Route to add a new task
@app.route("/add", methods=["POST"])
def add():
    if 'username' not in session:
        app.logger.warning("Attempt to access add task without login.")
        return redirect(url_for('login'))

    title = request.form.get("title")
    priority = request.form.get("priority", "Low")

    if not title or not title.strip():
        flash("Title cannot be empty!")
        app.logger.warning(f"Empty title attempt: {session.get('username')}")
        return redirect(url_for("home"))

    if not validate_priority(priority):
        flash("Invalid priority level!")
        app.logger.warning(f"Invalid priority level attempt: {session.get('username')} with priority {priority}")
        return redirect(url_for("home"))

    title = bleach.clean(title.strip())
    new_todo = Todo(title=title, priority=priority, complete=False)
    db.session.add(new_todo)
    db.session.commit()
    flash("Task added successfully!")
    app.logger.info(f"Task added: {title} by {session.get('username')}")
    return redirect(url_for("home"))


# Route to update a task's completion status
@app.route("/update/<int:todo_id>")
def update(todo_id):
    if 'username' not in session:
        app.logger.warning("Attempt to update task without login.")
        return redirect(url_for('login'))

    todo = Todo.query.get(todo_id)
    if not todo:
        flash("Task not found!")
        app.logger.warning(f"Task not found during update attempt: {todo_id} by {session.get('username')}")
        return redirect(url_for("home"))

    todo.complete = not todo.complete
    db.session.commit()
    flash("Task updated successfully!")
    app.logger.info(f"Task updated: {todo.id} by {session.get('username')}")
    return redirect(url_for("home"))

# Route to rename a task
@app.route("/rename/<int:todo_id>", methods=["POST"])
def rename(todo_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    new_title = request.form.get("new_title").strip()

    # Input validation
    if not new_title:
        flash("Title cannot be empty!")
        return redirect(url_for("home"))

    # Sanitization
    new_title = bleach.clean(new_title)

    todo = Todo.query.get(todo_id)
    if not todo:
        flash("Task not found!")
        return redirect(url_for("home"))

    todo.title = new_title
    db.session.commit()
    flash("Task title updated successfully!")
    return redirect(url_for("home"))

# Route to delete a task
@app.route("/delete/<int:todo_id>")
def delete(todo_id):
    try:
        if 'username' not in session:
            return redirect(url_for('login'))

        todo = Todo.query.get(todo_id)
        if not todo:
            flash("Task not found!")
            return redirect(url_for("home"))

        db.session.delete(todo)
        db.session.commit()
        flash("Task deleted successfully!")
        return redirect(url_for("home"))
    except Exception as e:
        app.logger.error(f"Error in delete: {e}")
        flash("An error occurred while deleting the task.")
        return redirect(url_for("home"))

# Route to search for tasks by title
@app.route("/search", methods=["GET"])
def search():
    if 'username' not in session:
        return redirect(url_for('login'))

    query = request.args.get("query", "").strip()
    
    # Check if the query is empty
    if not query:
        flash("Search query cannot be empty!")
        return redirect(url_for("home"))

    # Perform a case-insensitive search
    todo_list = Todo.query.filter(Todo.title.ilike(f"%{query}%")).all()

    # If no tasks match the query
    if not todo_list:
        flash(f"No tasks found for search query: '{query}'")
        return redirect(url_for("home"))

    # Render the search results
    return render_template("base.html", todo_list=todo_list, search_query=query, pagination=None)

# Route to mark all tasks as complete or incomplete
@app.route("/mark_all/<action>")
def mark_all(action):
    if 'username' not in session:
        return redirect(url_for('login'))

    if action == "complete":
        Todo.query.update({Todo.complete: True})
    elif action == "incomplete":
        Todo.query.update({Todo.complete: False})
    else:
        flash("Invalid action!")
        return redirect(url_for("home"))

    db.session.commit()
    flash(f"All tasks marked as {action}!")
    return redirect(url_for("home"))

# Login route for users
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            session['username'] = username
            flash("Logged in successfully!")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password")

    return render_template("login.html")


# Register route for new users
@app.route("/register", methods=["GET", "POST"])
def register():
    message = None
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        if not username or not password:
            message = "Username and password cannot be empty!"
        elif User.query.filter_by(username=username).first():
            message = "Username already exists!"
        else:
            # Hash password before storing
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash("User registered successfully! Please login.")
            return redirect(url_for("login"))

    return render_template("register.html", message=message)

# Logout route
@app.route("/logout")
def logout():
    session.pop('username', None)
    flash("Logged out successfully!")
    return redirect(url_for("login"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
