from flask import Blueprint, render_template
from flask_login import login_required, current_user

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def home():
    """
    Protected dashboard route.
    Only logged-in users can access this page.
    """
    return render_template("dashboard.html", user=current_user)