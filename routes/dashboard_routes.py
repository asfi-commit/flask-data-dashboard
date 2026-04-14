import os
import pandas as pd

from flask import (
    Blueprint,
    render_template,
    request,
    current_app,
    send_file
)

from flask_login import login_required, current_user

# Import reusable analysis helper functions
from services.analysis_service import (
    generate_preview_table,
    generate_missing_values_table,
    generate_summary_statistics,
    generate_dataset_info,
    get_column_groups,
)

# Import reusable chart helper functions
from services.chart_service import (
    generate_chart,
    generate_heatmap,
)

# Create blueprint for dashboard-related routes
dashboard_bp = Blueprint("dashboard", __name__)


# --------------------------------------------------
# Helper function: Load DataFrame from request
# --------------------------------------------------
def load_dataframe_from_request(uploaded_file, saved_csv_path):
    """
    Load a pandas DataFrame either from:
    1. a newly uploaded CSV file, or
    2. the previously saved CSV file.

    Parameters:
        uploaded_file   -> file object from Flask request
        saved_csv_path  -> path to stored CSV file

    Returns:
        df        -> pandas DataFrame or None
        file_name -> uploaded filename or fallback saved filename
        error     -> error message or None
    """
    df = None
    file_name = None
    error = None

    # Case 1: User uploads a new CSV file
    if uploaded_file and uploaded_file.filename.strip() != "":
        try:
            # Read uploaded CSV into DataFrame
            df = pd.read_csv(uploaded_file)

            # Save a reusable copy for later chart generation / download
            df.to_csv(saved_csv_path, index=False)

            # Keep original uploaded filename for display
            file_name = uploaded_file.filename

        except Exception as e:
            error = f"Error reading uploaded CSV file: {e}"

    # Case 2: No new file uploaded, use previously saved CSV
    elif os.path.exists(saved_csv_path):
        try:
            df = pd.read_csv(saved_csv_path)
            file_name = current_app.config["LAST_UPLOADED_FILE"]

        except Exception as e:
            error = f"Error loading previously uploaded CSV file: {e}"

    # Case 3: No file exists at all
    else:
        error = "Please upload a CSV file first."

    return df, file_name, error


# --------------------------------------------------
# Main dashboard route
# --------------------------------------------------
@dashboard_bp.route("/", methods=["GET", "POST"])
@login_required
def home():
    """
    Protected dashboard route.

    Features:
    - Only logged-in users can access
    - Upload CSV
    - Display dataset information
    - Show preview, missing values, summary statistics
    - Generate chart
    - Generate correlation heatmap
    """

    # Context dictionary sent to HTML template
    # Centralized so template rendering stays clean and scalable
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

    # Path to the reusable "latest uploaded" CSV file
    saved_csv_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        current_app.config["LAST_UPLOADED_FILE"]
    )

    # Process form submission only when request is POST
    if request.method == "POST":
        # File comes from upload form
        uploaded_file = request.files.get("file")

        # Chart settings come from chart-generation form
        selected_column = request.form.get("selected_column")
        chart_type = request.form.get("chart_type", "histogram")

        # Store user selections in context
        context["selected_column"] = selected_column
        context["chart_type"] = chart_type

        # Load DataFrame from uploaded file or previously stored file
        df, file_name, error = load_dataframe_from_request(uploaded_file, saved_csv_path)

        # Store file information / initial error if any
        context["file_name"] = file_name
        context["error"] = error

        # Continue only if DataFrame loaded successfully
        if df is not None:
            try:
                # ------------------------------------------
                # Basic dataset details
                # ------------------------------------------
                context["num_rows"], context["num_cols"] = df.shape
                context["column_names"] = df.columns.tolist()

                # ------------------------------------------
                # Generate analysis outputs
                # ------------------------------------------
                context["preview_data"] = generate_preview_table(df)
                context["missing_values"] = generate_missing_values_table(df)
                context["summary_stats"] = generate_summary_statistics(df)
                context["dataset_info"] = generate_dataset_info(df)

                # ------------------------------------------
                # Detect column groups
                # ------------------------------------------
                numeric_columns, categorical_columns, plottable_columns = get_column_groups(df)

                context["numeric_columns"] = numeric_columns
                context["categorical_columns"] = categorical_columns
                context["plottable_columns"] = plottable_columns

                # ------------------------------------------
                # Set default selected column safely
                # ------------------------------------------
                # On first upload, there is usually no selected column yet.
                # Prefer numeric column for histogram by default.
                if not context["selected_column"] or context["selected_column"] not in plottable_columns:
                    if numeric_columns:
                        context["selected_column"] = numeric_columns[0]
                    elif plottable_columns:
                        context["selected_column"] = plottable_columns[0]

                # ------------------------------------------
                # Debug prints (useful during development)
                # Remove later if you want a cleaner terminal
                # ------------------------------------------
                print("Numeric columns:", numeric_columns)
                print("Categorical columns:", categorical_columns)
                print("Plottable columns:", plottable_columns)
                print("Selected column:", context["selected_column"])
                print("Chart type:", context["chart_type"])

                # ------------------------------------------
                # Generate main chart
                # ------------------------------------------
                if context["selected_column"]:
                    chart_filename, chart_error = generate_chart(
                        df=df,
                        selected_column=context["selected_column"],
                        chart_type=context["chart_type"],
                        numeric_columns=numeric_columns,
                        static_folder=current_app.static_folder
                    )

                    context["chart_filename"] = chart_filename

                    print("Generated chart filename:", chart_filename)
                    print("Chart error:", chart_error)

                    # If chart-specific error occurs, show it
                    if chart_error:
                        context["error"] = chart_error

                # ------------------------------------------
                # Generate correlation heatmap
                # ------------------------------------------
                heatmap_filename, heatmap_error = generate_heatmap(
                    df=df,
                    numeric_columns=numeric_columns,
                    static_folder=current_app.static_folder
                )

                context["heatmap_filename"] = heatmap_filename

                print("Generated heatmap filename:", heatmap_filename)
                print("Heatmap error:", heatmap_error)

                # Show heatmap error only if no previous error exists
                if heatmap_error and not context["error"]:
                    context["error"] = heatmap_error

            except Exception as e:
                context["error"] = f"Error processing data: {e}"

    # Render the protected dashboard page
    return render_template("dashboard.html", **context)


# --------------------------------------------------
# Download route
# --------------------------------------------------
@dashboard_bp.route("/download")
@login_required
def download_file():
    """
    Download the last uploaded CSV file.

    This route is protected, so only logged-in users can use it.
    """
    file_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        current_app.config["LAST_UPLOADED_FILE"]
    )

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)

    return "No file available for download."