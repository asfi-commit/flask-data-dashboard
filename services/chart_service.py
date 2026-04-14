import os
import matplotlib

# --------------------------------------------------
# Use non-GUI backend for Flask apps
# --------------------------------------------------
# This prevents Tkinter-related errors and allows
# saving plots directly to files.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns


# --------------------------------------------------
# Utility: Ensure folder exists
# --------------------------------------------------
def ensure_folder_exists(folder_path):
    """
    Create a folder if it does not exist.

    Parameters:
        folder_path -> path of the folder
    """
    os.makedirs(folder_path, exist_ok=True)


# --------------------------------------------------
# Utility: Save plot safely
# --------------------------------------------------
def save_plot(figure, output_path):
    """
    Save matplotlib figure and close it to free memory.

    Parameters:
        figure      -> matplotlib figure
        output_path -> file path to save image
    """
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)


# --------------------------------------------------
# Create Histogram
# --------------------------------------------------
def create_histogram(df, selected_column):
    """
    Create histogram for numeric column.

    Parameters:
        df              -> pandas DataFrame
        selected_column -> numeric column name

    Returns:
        fig -> matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    # Remove missing values before plotting
    df[selected_column].dropna().plot(kind="hist", bins=20, ax=ax)

    ax.set_title(f"Histogram of {selected_column}")
    ax.set_xlabel(selected_column)
    ax.set_ylabel("Frequency")

    return fig


# --------------------------------------------------
# Create Bar Chart
# --------------------------------------------------
def create_bar_chart(df, selected_column):
    """
    Create bar chart using top 10 value counts.

    Works for:
    - categorical columns
    - numeric columns (converted to string)

    Parameters:
        df              -> pandas DataFrame
        selected_column -> column name

    Returns:
        fig -> matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    # Convert values to string to handle mixed types safely
    value_counts = df[selected_column].astype(str).value_counts().head(10)

    value_counts.plot(kind="bar", ax=ax)

    ax.set_title(f"Bar Chart of {selected_column}")
    ax.set_xlabel(selected_column)
    ax.set_ylabel("Count")

    # Rotate labels for better readability
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    return fig


# --------------------------------------------------
# Main Chart Generator
# --------------------------------------------------
def generate_chart(df, selected_column, chart_type, numeric_columns, static_folder, user_id):
    """
    Generate a chart and save it in a user-specific folder.

    Parameters:
        df              -> pandas DataFrame
        selected_column -> column selected by user
        chart_type      -> 'histogram' or 'bar'
        numeric_columns -> list of numeric columns
        static_folder   -> Flask static folder path
        user_id         -> current logged-in user ID

    Returns:
        chart_filename -> relative path for Flask
        error          -> error message or None
    """
    chart_filename = None
    error = None

    # Validate column
    if not selected_column:
        return None, "No column selected for chart."

    try:
        # -------------------------------
        # Histogram (only numeric)
        # -------------------------------
        if chart_type == "histogram":
            if selected_column not in numeric_columns:
                return None, "Histogram only works for numeric columns."
            fig = create_histogram(df, selected_column)

        # -------------------------------
        # Bar chart
        # -------------------------------
        elif chart_type == "bar":
            fig = create_bar_chart(df, selected_column)

        else:
            return None, "Invalid chart type."

        # -------------------------------
        # Create user-specific folder
        # -------------------------------
        user_static_folder = os.path.join(static_folder, f"user_{user_id}")
        ensure_folder_exists(user_static_folder)

        # Save chart
        chart_filename = f"user_{user_id}/chart.png"
        chart_path = os.path.join(static_folder, chart_filename)

        save_plot(fig, chart_path)

    except Exception as e:
        error = f"Error generating chart: {e}"

    return chart_filename, error


# --------------------------------------------------
# Heatmap Generator
# --------------------------------------------------
def generate_heatmap(df, numeric_columns, static_folder, user_id):
    """
    Generate correlation heatmap.

    Parameters:
        df              -> pandas DataFrame
        numeric_columns -> numeric columns list
        static_folder   -> Flask static folder
        user_id         -> current user ID

    Returns:
        heatmap_filename -> relative file path
        error            -> error message or None
    """
    heatmap_filename = None
    error = None

    # Need at least 2 numeric columns
    if len(numeric_columns) < 2:
        return None, None

    try:
        correlation_matrix = df[numeric_columns].corr()

        fig, ax = plt.subplots(figsize=(8, 6))

        sns.heatmap(
            correlation_matrix,
            annot=True,
            cmap="coolwarm",
            fmt=".2f",
            ax=ax
        )

        ax.set_title("Correlation Heatmap")

        # Create user-specific folder
        user_static_folder = os.path.join(static_folder, f"user_{user_id}")
        ensure_folder_exists(user_static_folder)

        # Save heatmap
        heatmap_filename = f"user_{user_id}/heatmap.png"
        heatmap_path = os.path.join(static_folder, heatmap_filename)

        save_plot(fig, heatmap_path)

    except Exception as e:
        error = f"Error generating heatmap: {e}"

    return heatmap_filename, error