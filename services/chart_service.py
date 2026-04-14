import os
import matplotlib

# --------------------------------------------------
# Use a non-GUI backend for Flask applications
# --------------------------------------------------
# This avoids Tkinter / main loop errors on Windows
# and allows matplotlib to save images directly to files.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns


# --------------------------------------------------
# Helper function: Save matplotlib figure safely
# --------------------------------------------------
def save_plot(figure, output_path):
    """
    Save a matplotlib figure to the given file path
    and close it properly to free memory.

    Parameters:
        figure      -> matplotlib figure object
        output_path -> full path where image will be saved
    """
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)


# --------------------------------------------------
# Helper function: Generate histogram
# --------------------------------------------------
def create_histogram(df, selected_column):
    """
    Create a histogram for a numeric column.

    Parameters:
        df              -> pandas DataFrame
        selected_column -> numeric column name

    Returns:
        figure -> matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    # Drop missing values before plotting
    df[selected_column].dropna().plot(kind="hist", bins=20, ax=ax)

    ax.set_title(f"Histogram of {selected_column}")
    ax.set_xlabel(selected_column)
    ax.set_ylabel("Frequency")

    return fig


# --------------------------------------------------
# Helper function: Generate bar chart
# --------------------------------------------------
def create_bar_chart(df, selected_column):
    """
    Create a bar chart for a column using top 10 value counts.

    Works for:
    - categorical columns
    - numeric columns (as category-like counts)

    Parameters:
        df              -> pandas DataFrame
        selected_column -> column name

    Returns:
        figure -> matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    # Convert values to string so both numeric and categorical columns work safely
    value_counts = df[selected_column].astype(str).value_counts().head(10)

    value_counts.plot(kind="bar", ax=ax)

    ax.set_title(f"Bar Chart of {selected_column}")
    ax.set_xlabel(selected_column)
    ax.set_ylabel("Count")

    # Rotate labels for better readability
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    return fig


# --------------------------------------------------
# Main chart generator
# --------------------------------------------------
def generate_chart(df, selected_column, chart_type, numeric_columns, static_folder):
    """
    Generate a chart based on selected chart type.

    Supported chart types:
    - histogram (numeric columns only)
    - bar (numeric or categorical columns)

    Parameters:
        df              -> pandas DataFrame
        selected_column -> selected column name
        chart_type      -> 'histogram' or 'bar'
        numeric_columns -> list of numeric columns
        static_folder   -> Flask static folder path

    Returns:
        chart_filename -> saved image filename or None
        error          -> error message or None
    """
    chart_filename = None
    error = None

    # Validate selected column
    if not selected_column:
        return None, "No column selected for chart generation."

    try:
        # ------------------------------------------
        # Histogram: only numeric columns allowed
        # ------------------------------------------
        if chart_type == "histogram":
            if selected_column not in numeric_columns:
                return None, "Histogram can only be generated for numeric columns."

            fig = create_histogram(df, selected_column)

        # ------------------------------------------
        # Bar chart: works for both numeric and categorical columns
        # ------------------------------------------
        elif chart_type == "bar":
            fig = create_bar_chart(df, selected_column)

        # ------------------------------------------
        # Invalid chart type
        # ------------------------------------------
        else:
            return None, "Invalid chart type selected."

        # Save chart image
        chart_filename = "chart.png"
        chart_path = os.path.join(static_folder, chart_filename)

        save_plot(fig, chart_path)

    except Exception as e:
        error = f"Error generating chart: {e}"

    return chart_filename, error


# --------------------------------------------------
# Heatmap generator
# --------------------------------------------------
def generate_heatmap(df, numeric_columns, static_folder):
    """
    Generate a correlation heatmap using numeric columns.

    Heatmap is created only if at least 2 numeric columns exist.

    Parameters:
        df              -> pandas DataFrame
        numeric_columns -> list of numeric columns
        static_folder   -> Flask static folder path

    Returns:
        heatmap_filename -> saved image filename or None
        error            -> error message or None
    """
    heatmap_filename = None
    error = None

    # Need at least 2 numeric columns for meaningful correlation
    if len(numeric_columns) < 2:
        return None, None

    try:
        # Compute correlation matrix
        correlation_matrix = df[numeric_columns].corr()

        # Create figure
        fig, ax = plt.subplots(figsize=(8, 6))

        sns.heatmap(
            correlation_matrix,
            annot=True,
            cmap="coolwarm",
            fmt=".2f",
            ax=ax
        )

        ax.set_title("Correlation Heatmap")

        # Save heatmap image
        heatmap_filename = "heatmap.png"
        heatmap_path = os.path.join(static_folder, heatmap_filename)

        save_plot(fig, heatmap_path)

    except Exception as e:
        error = f"Error generating heatmap: {e}"

    return heatmap_filename, error