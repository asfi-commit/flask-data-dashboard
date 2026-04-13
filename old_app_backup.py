from flask import Flask, render_template, request, send_file
import os
import pandas as pd
import matplotlib

# Use a non-GUI backend so matplotlib works safely in Flask
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns


# --------------------------------------------------
# Flask app configuration
# --------------------------------------------------
app = Flask(__name__)

# Folder to store uploaded CSV files
UPLOAD_FOLDER = "uploads"

# Name of the file where the latest uploaded CSV will be saved
LAST_UPLOADED_FILE = "last_uploaded.csv"

# Save upload folder in Flask config
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create upload folder if it does not exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --------------------------------------------------
# Helper function: Load DataFrame
# --------------------------------------------------
def load_dataframe_from_request(uploaded_file, saved_csv_path):
    """
    Load a DataFrame either from:
    1. a newly uploaded CSV file, or
    2. the previously saved CSV file.

    Parameters:
        uploaded_file: file object from Flask request
        saved_csv_path: path of last uploaded CSV

    Returns:
        df        -> pandas DataFrame or None
        file_name -> original uploaded filename or fallback filename
        error     -> error message or None
    """
    df = None
    file_name = None
    error = None

    # Case 1: User uploads a new file
    if uploaded_file and uploaded_file.filename.strip() != "":
        try:
            df = pd.read_csv(uploaded_file)

            # Save a copy for future chart generation and download
            df.to_csv(saved_csv_path, index=False)

            file_name = uploaded_file.filename

        except Exception as e:
            error = f"Error reading uploaded CSV file: {e}"

    # Case 2: No new file uploaded, use previously saved CSV
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
# Helper function: Generate dataset preview
# --------------------------------------------------
def generate_preview_table(df):
    """
    Return the first 5 rows as an HTML table.
    """
    return df.head().to_html(classes="table", index=False)


# --------------------------------------------------
# Helper function: Generate missing values table
# --------------------------------------------------
def generate_missing_values_table(df):
    """
    Return missing value count per column as an HTML table.
    """
    missing_df = df.isnull().sum().reset_index()
    missing_df.columns = ["Column", "Missing Values"]
    return missing_df.to_html(classes="table", index=False)


# --------------------------------------------------
# Helper function: Generate summary statistics table
# --------------------------------------------------
def generate_summary_statistics(df):
    """
    Return summary statistics for all columns as an HTML table.
    """
    summary_df = df.describe(include="all").fillna("")
    return summary_df.to_html(classes="table", index=True)


# --------------------------------------------------
# Helper function: Generate dataset info table
# --------------------------------------------------
def generate_dataset_info(df):
    """
    Return dataset information including:
    - column name
    - data type
    - non-null count
    """
    info_df = pd.DataFrame({
        "Column": df.columns,
        "Data Type": df.dtypes.astype(str).values,
        "Non-Null Count": df.notnull().sum().values
    })

    return info_df.to_html(classes="table", index=False)


# --------------------------------------------------
# Helper function: Get column groups
# --------------------------------------------------
def get_column_groups(df):
    """
    Detect numeric columns, categorical columns, and all plottable columns.

    Returns:
        numeric_columns
        categorical_columns
        plottable_columns
    """
    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    categorical_columns = df.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()
    plottable_columns = df.columns.tolist()

    return numeric_columns, categorical_columns, plottable_columns


# --------------------------------------------------
# Helper function: Generate chart
# --------------------------------------------------
def generate_chart(df, selected_column, chart_type, numeric_columns, static_folder):
    """
    Generate either:
    - histogram (numeric columns only)
    - bar chart (numeric or categorical columns)

    Parameters:
        df
        selected_column
        chart_type
        numeric_columns
        static_folder

    Returns:
        chart_filename
        error
    """
    chart_filename = None
    error = None

    if not selected_column:
        return None, "No column selected for chart generation."

    plt.figure(figsize=(8, 5))

    # Histogram: only numeric columns allowed
    if chart_type == "histogram":
        if selected_column in numeric_columns:
            df[selected_column].dropna().plot(kind="hist", bins=20)
            plt.title(f"Histogram of {selected_column}")
            plt.xlabel(selected_column)
            plt.ylabel("Frequency")
        else:
            plt.close()
            return None, "Histogram can only be generated for numeric columns."

    # Bar chart: works for both numeric and categorical columns
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
    Generate a correlation heatmap using numeric columns.

    Heatmap is created only when at least 2 numeric columns exist.

    Returns:
        heatmap_filename
        error
    """
    heatmap_filename = None
    error = None

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
# Main dashboard route
# --------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    """
    Main route of the dashboard.

    Handles:
    - file upload
    - loading last uploaded file
    - data analysis
    - chart generation
    - heatmap generation
    """

    # Dictionary to store everything passed to HTML template
    context = {
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

    # Full path of last uploaded file
    saved_csv_path = os.path.join(app.config["UPLOAD_FOLDER"], LAST_UPLOADED_FILE)

    # Process only when form is submitted
    if request.method == "POST":
        uploaded_file = request.files.get("file")
        selected_column = request.form.get("selected_column")
        chart_type = request.form.get("chart_type", "histogram")

        context["selected_column"] = selected_column
        context["chart_type"] = chart_type

        # Load dataframe from uploaded file or previously saved file
        df, file_name, error = load_dataframe_from_request(uploaded_file, saved_csv_path)

        context["file_name"] = file_name
        context["error"] = error

        # If dataframe loaded successfully, continue analysis
        if df is not None:
            try:
                # Basic dataset shape
                context["num_rows"], context["num_cols"] = df.shape

                # Column names
                context["column_names"] = df.columns.tolist()

                # Analysis outputs
                context["preview_data"] = generate_preview_table(df)
                context["missing_values"] = generate_missing_values_table(df)
                context["summary_stats"] = generate_summary_statistics(df)
                context["dataset_info"] = generate_dataset_info(df)

                # Detect column groups
                numeric_columns, categorical_columns, plottable_columns = get_column_groups(df)
                context["numeric_columns"] = numeric_columns
                context["categorical_columns"] = categorical_columns
                context["plottable_columns"] = plottable_columns

                # If selected column is invalid or empty, choose a default one
                if context["selected_column"] not in plottable_columns:
                    if numeric_columns:
                        context["selected_column"] = numeric_columns[0]
                    elif plottable_columns:
                        context["selected_column"] = plottable_columns[0]

                # Generate main chart
                chart_filename, chart_error = generate_chart(
                    df=df,
                    selected_column=context["selected_column"],
                    chart_type=context["chart_type"],
                    numeric_columns=numeric_columns,
                    static_folder=app.static_folder
                )

                context["chart_filename"] = chart_filename

                if chart_error:
                    context["error"] = chart_error

                # Generate heatmap
                heatmap_filename, heatmap_error = generate_heatmap(
                    df=df,
                    numeric_columns=numeric_columns,
                    static_folder=app.static_folder
                )

                context["heatmap_filename"] = heatmap_filename

                # Show heatmap error only if no previous error exists
                if heatmap_error and not context["error"]:
                    context["error"] = heatmap_error

            except Exception as e:
                context["error"] = f"Error processing data: {e}"

    return render_template("index.html", **context)


# --------------------------------------------------
# Download route
# --------------------------------------------------
@app.route("/download")
def download_file():
    """
    Download the last uploaded CSV file.
    """
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], LAST_UPLOADED_FILE)

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)

    return "No file available for download."


# --------------------------------------------------
# Run Flask app
# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)