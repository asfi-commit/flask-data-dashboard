from flask import Flask, render_template, request
import os
import pandas as pd
import matplotlib

# Use a non-GUI backend for server-side chart generation
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns


# --------------------------------------------------
# Flask app setup
# --------------------------------------------------
app = Flask(__name__)

# Folder where uploaded CSV will be stored
UPLOAD_FOLDER = "uploads"

# Name of the file that stores the latest uploaded CSV
LAST_UPLOADED_FILE = "last_uploaded.csv"

# Configure upload folder in Flask app config
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create upload folder if it does not already exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --------------------------------------------------
# Helper function: Load uploaded CSV or previously saved CSV
# --------------------------------------------------
def load_dataframe_from_request(uploaded_file, saved_csv_path):
    """
    Load a DataFrame from either:
    1. a newly uploaded CSV file, or
    2. the previously saved CSV file.

    Returns:
        df (pd.DataFrame or None)
        file_name (str or None)
        error (str or None)
    """
    df = None
    file_name = None
    error = None

    # Case 1: User uploaded a new file
    if uploaded_file and uploaded_file.filename.strip() != "":
        try:
            df = pd.read_csv(uploaded_file)
            df.to_csv(saved_csv_path, index=False)   # Save a reusable copy
            file_name = uploaded_file.filename
        except Exception as e:
            error = f"Error reading uploaded CSV file: {e}"

    # Case 2: No new file uploaded, use previous saved CSV
    elif os.path.exists(saved_csv_path):
        try:
            df = pd.read_csv(saved_csv_path)
            file_name = LAST_UPLOADED_FILE
        except Exception as e:
            error = f"Error loading previously uploaded CSV file: {e}"

    # Case 3: No file available at all
    else:
        error = "Please upload a CSV file first."

    return df, file_name, error


# --------------------------------------------------
# Helper function: Generate main analysis outputs
# --------------------------------------------------
def generate_basic_analysis(df):
    """
    Generate reusable analysis outputs from the DataFrame.

    Returns:
        A dictionary containing:
        - row/column counts
        - column names
        - HTML preview table
        - HTML missing values table
        - HTML summary statistics table
        - numeric columns
        - categorical columns
        - all plottable columns
    """
    analysis = {}

    # Shape of dataset
    analysis["num_rows"], analysis["num_cols"] = df.shape

    # List of all column names
    analysis["column_names"] = df.columns.tolist()

    # Show first 5 rows as HTML table
    analysis["preview_data"] = df.head().to_html(classes="table", index=False)

    # Missing values per column
    missing_df = df.isnull().sum().reset_index()
    missing_df.columns = ["Column", "Missing Values"]
    analysis["missing_values"] = missing_df.to_html(classes="table", index=False)

    # Summary statistics
    # include="all" allows both numeric and non-numeric columns to be summarized
    summary_stats_df = df.describe(include="all").fillna("")
    analysis["summary_stats"] = summary_stats_df.to_html(classes="table", index=True)

    # Detect numeric columns
    analysis["numeric_columns"] = df.select_dtypes(include="number").columns.tolist()

    # Detect categorical/text/bool columns
    analysis["categorical_columns"] = df.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    # All columns can be shown in dropdown
    analysis["plottable_columns"] = df.columns.tolist()

    return analysis


# --------------------------------------------------
# Helper function: Generate chart image
# --------------------------------------------------
def generate_chart(df, selected_column, chart_type, numeric_columns, static_folder):
    """
    Generate either a histogram or a bar chart based on user selection.

    Returns:
        chart_filename (str or None)
        error (str or None)
    """
    chart_filename = None
    error = None

    if selected_column is None:
        return None, "No column selected for chart generation."

    plt.figure(figsize=(8, 5))

    # Histogram only for numeric columns
    if chart_type == "histogram":
        if selected_column in numeric_columns:
            df[selected_column].dropna().plot(kind="hist", bins=20)
            plt.title(f"Histogram of {selected_column}")
            plt.xlabel(selected_column)
            plt.ylabel("Frequency")
        else:
            plt.close()
            return None, "Histogram can only be generated for numeric columns."

    # Bar chart for both numeric and categorical columns
    elif chart_type == "bar":
        value_counts = df[selected_column].astype(str).value_counts().head(10)
        value_counts.plot(kind="bar")
        plt.title(f"Bar Chart of {selected_column}")
        plt.xlabel(selected_column)
        plt.ylabel("Count")
        plt.xticks(rotation=45, ha="right")

    else:
        plt.close()
        return None, "Invalid chart type selected."

    plt.tight_layout()

    chart_filename = "chart.png"
    chart_path = os.path.join(static_folder, chart_filename)
    plt.savefig(chart_path)
    plt.close()

    return chart_filename, error


# --------------------------------------------------
# Helper function: Generate correlation heatmap
# --------------------------------------------------
def generate_heatmap(df, numeric_columns, static_folder):
    """
    Generate a correlation heatmap using numeric columns only.

    Returns:
        heatmap_filename (str or None)
        error (str or None)
    """
    heatmap_filename = None
    error = None

    # Heatmap needs at least 2 numeric columns for meaningful correlation
    if len(numeric_columns) < 2:
        return None, None

    try:
        correlation_matrix = df[numeric_columns].corr()

        plt.figure(figsize=(8, 6))
        sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", fmt=".2f")
        plt.title("Correlation Heatmap")
        plt.tight_layout()

        heatmap_filename = "heatmap.png"
        heatmap_path = os.path.join(static_folder, heatmap_filename)
        plt.savefig(heatmap_path)
        plt.close()

    except Exception as e:
        error = f"Error generating heatmap: {e}"

    return heatmap_filename, error


# --------------------------------------------------
# Main route
# --------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    """
    Main dashboard route.

    Handles:
    - CSV upload
    - Data analysis
    - Chart generation
    - Heatmap generation
    """

    # Default values passed to template
    context = {
        "file_name": None,
        "num_rows": None,
        "num_cols": None,
        "column_names": [],
        "preview_data": None,
        "missing_values": None,
        "summary_stats": None,
        "chart_filename": None,
        "heatmap_filename": None,
        "numeric_columns": [],
        "categorical_columns": [],
        "plottable_columns": [],
        "selected_column": None,
        "chart_type": "histogram",
        "error": None,
    }

    saved_csv_path = os.path.join(app.config["UPLOAD_FOLDER"], LAST_UPLOADED_FILE)

    # Only process form data when request is POST
    if request.method == "POST":
        uploaded_file = request.files.get("file")
        selected_column = request.form.get("selected_column")
        chart_type = request.form.get("chart_type", "histogram")

        # Store user-selected options in context
        context["selected_column"] = selected_column
        context["chart_type"] = chart_type

        # Load dataframe
        df, file_name, error = load_dataframe_from_request(uploaded_file, saved_csv_path)

        context["file_name"] = file_name
        context["error"] = error

        # Proceed only if DataFrame loaded successfully
        if df is not None:
            try:
                # Generate core analysis
                analysis = generate_basic_analysis(df)
                context.update(analysis)

                # Decide default selected column if user has not selected one yet
                if context["selected_column"] not in context["plottable_columns"]:
                    if context["numeric_columns"]:
                        context["selected_column"] = context["numeric_columns"][0]
                    elif context["plottable_columns"]:
                        context["selected_column"] = context["plottable_columns"][0]

                # Generate main chart
                chart_filename, chart_error = generate_chart(
                    df=df,
                    selected_column=context["selected_column"],
                    chart_type=context["chart_type"],
                    numeric_columns=context["numeric_columns"],
                    static_folder=app.static_folder
                )

                context["chart_filename"] = chart_filename

                # If chart-specific error exists, show it
                if chart_error:
                    context["error"] = chart_error

                # Generate heatmap
                heatmap_filename, heatmap_error = generate_heatmap(
                    df=df,
                    numeric_columns=context["numeric_columns"],
                    static_folder=app.static_folder
                )

                context["heatmap_filename"] = heatmap_filename

                # Only overwrite error if no previous major error exists
                if heatmap_error and not context["error"]:
                    context["error"] = heatmap_error

            except Exception as e:
                context["error"] = f"Error processing data: {e}"

    # Render dashboard page
    return render_template("index.html", **context)


# --------------------------------------------------
# Run the Flask app
# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)