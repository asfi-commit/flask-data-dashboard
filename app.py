from flask import Flask 
from config import Config
from models import db, login_manager

def create_app():
    """
    Application factory function.
    Creates and configures the Flask app cleanly.
    """

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    #Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)

    #Login manager settings
    login_manager.login_view = "auth.login"

    #Ensure important folder exist
    import os
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    # Import and register blueprints
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

