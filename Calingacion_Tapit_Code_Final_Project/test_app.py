import unittest
from user import app, db, User, Todo  # Import your app, database, and models
from flask import session

class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        """Define the test variables and initialize the app."""
        self.app = app.test_client()
        self.app.testing = True

        # Create all tables
        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Teardown all initialized variables."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_register(self):
        """Test if user can register."""
        response = self.app.post('/register', data=dict(
            username="testuser",
            password="password"
        ), follow_redirects=True)
        self.assertIn(b"User registered successfully!", response.data)

    def test_login(self):
        """Test if user can log in."""
        self.app.post('/register', data=dict(
            username="testuser",
            password="password"
        ), follow_redirects=True)

        response = self.app.post('/login', data=dict(
            username="testuser",
            password="password"
        ), follow_redirects=True)
        self.assertIn(b"Logged in successfully!", response.data)
        self.assertTrue('username' in session)

    def test_logout(self):
        """Test if user can log out."""
        self.app.post('/register', data=dict(
            username="testuser",
            password="password"
        ), follow_redirects=True)

        self.app.post('/login', data=dict(
            username="testuser",
            password="password"
        ), follow_redirects=True)

        response = self.app.get('/logout', follow_redirects=True)
        self.assertIn(b"Logged out successfully!", response.data)
        self.assertFalse('username' in session)

    def test_add_todo(self):
        """Test if user can add a todo."""
        with app.app_context():
            self.app.post('/register', data=dict(
                username="testuser",
                password="password"
            ), follow_redirects=True)

            self.app.post('/login', data=dict(
                username="testuser",
                password="password"
            ), follow_redirects=True)

            response = self.app.post('/add', data=dict(
                title="New Todo",
                priority="Medium"
            ), follow_redirects=True)
            self.assertIn(b"Task added successfully!", response.data)

    def test_update_todo(self):
        """Test if user can update a todo."""
        with app.app_context():
            self.app.post('/register', data=dict(
                username="testuser",
                password="password"
            ), follow_redirects=True)

            self.app.post('/login', data=dict(
                username="testuser",
                password="password"
            ), follow_redirects=True)

            self.app.post('/add', data=dict(
                title="New Todo",
                priority="Medium"
            ), follow_redirects=True)

            # Fetch the todo id
            todo_id = Todo.query.first().id

            response = self.app.get(f'/update/{todo_id}', follow_redirects=True)
            self.assertIn(b"Task updated successfully!", response.data)

    def test_delete_todo(self):
        """Test if user can delete a todo."""
        with app.app_context():
            self.app.post('/register', data=dict(
                username="testuser",
                password="password"
            ), follow_redirects=True)

            self.app.post('/login', data=dict(
                username="testuser",
                password="password"
            ), follow_redirects=True)

            self.app.post('/add', data=dict(
                title="New Todo",
                priority="Medium"
            ), follow_redirects=True)

            # Fetch the todo id
            todo_id = Todo.query.first().id

            response = self.app.get(f'/delete/{todo_id}', follow_redirects=True)
            self.assertIn(b"Task deleted successfully!", response.data)

    def test_search(self):
        """Test if user can search for a todo."""
        with app.app_context():
            self.app.post('/register', data=dict(
                username="testuser",
                password="password"
            ), follow_redirects=True)

            self.app.post('/login', data=dict(
                username="testuser",
                password="password"
            ), follow_redirects=True)

            self.app.post('/add', data=dict(
                title="Test Search",
                priority="Medium"
            ), follow_redirects=True)

            response = self.app.get('/search?query=Test', follow_redirects=True)
            self.assertIn(b"Test Search", response.data)

    def test_mark_all(self):
        """Test if user can mark all todos as complete or incomplete."""
        with app.app_context():
            self.app.post('/register', data=dict(
                username="testuser",
                password="password"
            ), follow_redirects=True)

            self.app.post('/login', data=dict(
                username="testuser",
                password="password"
            ), follow_redirects=True)

            self.app.post('/add', data=dict(
                title="Todo 1",
                priority="Medium"
            ), follow_redirects=True)

            self.app.post('/add', data=dict(
                title="Todo 2",
                priority="Low"
            ), follow_redirects=True)

            self.app.get('/mark_all/complete', follow_redirects=True)
            todos = Todo.query.all()
            for todo in todos:
                self.assertTrue(todo.complete)

            self.app.get('/mark_all/incomplete', follow_redirects=True)
            todos = Todo.query.all()
            for todo in todos:
                self.assertFalse(todo.complete)


if __name__ == "__main__":
    unittest.main()
