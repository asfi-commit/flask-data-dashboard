from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

# Create Blueprint for authentication-related routes
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Handle User Registration.

    GET -> show registration form.
    POST -> validate form data, hash password, save user in database.
    """
    # If user is already logged in , send them to dashboard
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))
    
    if request.method == "POST":
        # Get data from fields.
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirm_passwod = request.form.get("confirm_password", "").strip()

        # Basic Validation
        if not username or not email or not password or not confirm_passwod:
            flash("All fields are required.", "error")
            return redirect(url_for("auth.register"))
        
        if password != confirm_passwod:
            flash("Password do not match.", "error")
            return redirect(url_for("auth.register"))

        # Check if username already exist.
        existing_user_by_username = User.query.filter_by(username=username).first()
        if existing_user_by_username:
             flash("Username already exists. Please choose another one.", "error")
             return redirect(url_for("auth.register"))
        
        # Check email already exist 
        existing_user_by_email = User.query.filter_by(email=email).first()
        if existing_user_by_email:
            flash("Email already exists. Please choose another email.", "error")
            return redirect(url_for("auth.register"))
        
        # Hash Password before saving.
        hashed_password = generate_password_hash(password)

        # Create new user object.
        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        try:
            # Save user to database.
            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful. You can now log in.", "success")
            return redirect(url_for("auth.login"))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating user: {e}", "error")
            return redirect(url_for("auth.register"))
        
    # This handles GET Request
    return render_template("register.html")
        
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login.

    GET  -> show login form
    POST -> verify email and password, then log user in
    """
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(email=email).first()

        print("Entered email:", email)
        print("User found:", user)

        if user:
            print("Stored hashed password:", user.password)
            print("Password match:", check_password_hash(user.password, password))

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful.", "success")
            return redirect(url_for("dashboard.home"))

        flash("Invalid email or password.", "error")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """
    Log the current user out.
    """
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))

