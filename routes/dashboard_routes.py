import os
import pandas as pd

from flask import Blueprint, render_template, request, current_app, send_file
from flask_login import login_required, current_user

# Import analysis services
from services.analysis_service import (
    generate_preview_table,
    generate_missing_values_table,
    generate_summary_statistics,
    generate_dataset_info,
    get_column_groups,
)

# Import chart services
from services.chart_service import generate_chart, generate_heatmap

# Create blueprint
dashboard_bp = Blueprint("dashboard", __name__)


# --------------------------------------------------
# Utility: Ensure folder exists
# --------------------------------------------------
def ensure_folder_exists(folder_path):
    """
    Create folder if it does not exist.
    """
    os.makedirs(folder_path, exist_ok=True)


# --------------------------------------------------
# Get user-specific upload folder
# --------------------------------------------------
def get_user_upload_folder():
    """
    Returns upload folder for current user.

    Example:
        uploads/user_1/
    """
    user_folder = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        f"user_{current_user.id}"
    )
    ensure_folder_exists(user_folder)
    return user_folder


# --------------------------------------------------
# Load DataFrame from request or saved file
# --------------------------------------------------
def load_dataframe(uploaded_file, saved_csv_path):
    """
    Load DataFrame from:
    - uploaded file OR
    - previously saved file
    """
    df = None
    file_name = None
    error = None

    if uploaded_file and uploaded_file.filename.strip():
        try:
            df = pd.read_csv(uploaded_file)
            df.to_csv(saved_csv_path, index=False)
            file_name = uploaded_file.filename
        except Exception as e:
            error = f"Error reading CSV: {e}"

    elif os.path.exists(saved_csv_path):
        df = pd.read_csv(saved_csv_path)
        file_name = "Previously Uploaded File"

    else:
        error = "Please upload a CSV file."

    return df, file_name, error


# --------------------------------------------------
# Main Dashboard Route
# --------------------------------------------------
@dashboard_bp.route("/", methods=["GET", "POST"])
@login_required
def home():
    """
    Main dashboard view.

    Features:
    - Upload CSV
    - Data analysis
    - Chart generation
    - Heatmap generation
    """

    # Context dictionary passed to template
    context = {
        "user": current_user,
        "file_name": None,
        "num_rows": None,
        "num_cols": None,
        "column_names": [],
        "preview_data": None,
        "missing_values": None,
        "summary_stats": None,
        "dataset_info": None,
        "chart_filename": None,
        "heatmap_filename": None,
        "numeric_columns": [],
        "categorical_columns": [],
        "plottable_columns": [],
        "selected_column": None,
        "chart_type": "histogram",
        "error": None,
    }

    # User-specific upload path
    user_upload_folder = get_user_upload_folder()

    saved_csv_path = os.path.join(
        user_upload_folder,
        current_app.config["LAST_UPLOADED_FILE"]
    )

    if request.method == "POST":
        uploaded_file = request.files.get("file")
        selected_column = request.form.get("selected_column")
        chart_type = request.form.get("chart_type", "histogram")

        context["selected_column"] = selected_column
        context["chart_type"] = chart_type

        df, file_name, error = load_dataframe(uploaded_file, saved_csv_path)

        context["file_name"] = file_name
        context["error"] = error

        if df is not None:
            # Dataset info
            context["num_rows"], context["num_cols"] = df.shape
            context["column_names"] = df.columns.tolist()

            # Analysis
            context["preview_data"] = generate_preview_table(df)
            context["missing_values"] = generate_missing_values_table(df)
            context["summary_stats"] = generate_summary_statistics(df)
            context["dataset_info"] = generate_dataset_info(df)

            # Column grouping
            numeric_columns, categorical_columns, plottable_columns = get_column_groups(df)

            context["numeric_columns"] = numeric_columns
            context["categorical_columns"] = categorical_columns
            context["plottable_columns"] = plottable_columns

            # Default column selection
            if not selected_column:
                if numeric_columns:
                    selected_column = numeric_columns[0]
                elif plottable_columns:
                    selected_column = plottable_columns[0]

            context["selected_column"] = selected_column

            # Generate chart
            chart_filename, chart_error = generate_chart(
                df,
                selected_column,
                chart_type,
                numeric_columns,
                current_app.static_folder,
                current_user.id
            )

            context["chart_filename"] = chart_filename
            if chart_error:
                context["error"] = chart_error

            # Generate heatmap
            heatmap_filename, heatmap_error = generate_heatmap(
                df,
                numeric_columns,
                current_app.static_folder,
                current_user.id
            )

            context["heatmap_filename"] = heatmap_filename
            if heatmap_error and not context["error"]:
                context["error"] = heatmap_error

    return render_template("dashboard.html", **context)


# --------------------------------------------------
# Download Route
# --------------------------------------------------
@dashboard_bp.route("/download")
@login_required
def download_file():
    """
    Download user-specific CSV file.
    """
    user_upload_folder = get_user_upload_folder()

    file_path = os.path.join(
        user_upload_folder,
        current_app.config["LAST_UPLOADED_FILE"]
    )

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)

    return "No file available."