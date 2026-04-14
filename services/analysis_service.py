import pandas as pd


def generate_preview_table(df):
    """
    Return the first 5 rows as an HTML table.
    """
    return df.head().to_html(classes="table", index=False)


def generate_missing_values_table(df):
    """
    Return missing value count per column as an HTML table.
    """
    missing_df = df.isnull().sum().reset_index()
    missing_df.columns = ["Column", "Missing Values"]
    return missing_df.to_html(classes="table", index=False)


def generate_summary_statistics(df):
    """
    Return summary statistics for all columns as an HTML table.
    """
    summary_df = df.describe(include="all").fillna("")
    return summary_df.to_html(classes="table", index=True)


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


def get_column_groups(df):
    """
    Return:
    - numeric columns
    - categorical columns
    - all plottable columns
    """
    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    categorical_columns = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    plottable_columns = df.columns.tolist()

    return numeric_columns, categorical_columns, plottable_columns