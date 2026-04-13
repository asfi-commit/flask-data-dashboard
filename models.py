from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin

# Create extension objects
# These are initialized later inside app.py using init_app()
db = SQLAlchemy()
login_manager = LoginManager()


class User(UserMixin, db.Model):
    """
    User model for login and registration.
    Stores username, email, and password hash.
    """

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login uses this function to reload the user object
    from the user ID stored in the session.
    """
    return User.query.get(int(user_id))