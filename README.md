# Flask CSV Data Analysis Dashboard

A simple and reusable data analysis dashboard built with **Flask**, **Pandas**, **Matplotlib**, and **Seaborn**.  
This web application allows users to upload a CSV file and perform quick exploratory data analysis through tables and visualizations.

---

## Features

- Upload CSV files through a Flask web interface
- View basic dataset information
- Preview the first 5 rows
- Display column names
- Show missing values for each column
- Generate summary statistics
- Create histogram for numeric columns
- Create bar chart for numeric and categorical columns
- Generate correlation heatmap for numeric features
- Reusable and commented code structure for easy extension

---

## Tech Stack

- Python
- Flask
- Pandas
- Matplotlib
- Seaborn
- HTML
- CSS

---

## Project Structure

```bash
flask_data_dashboard/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── uploads/
│   └── last_uploaded.csv
│
├── static/
│   ├── style.css
│   ├── chart.png
│   └── heatmap.png
│
└── templates/
    └── index.html
```
