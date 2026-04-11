from flask import Flask, render_template, request
import os
import pandas as pd

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')

        if uploaded_file and uploaded_file.filename != '':
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            uploaded_file.save(file_path)

            #Read CSV file
            df = pd.read_csv(file_path)

            #Basic information
            file_name = uploaded_file.filename
            num_rows, num_cols = df.shape
            column_names = df.columns.tolist()
            preview_data = df.head().to_html(index=False)

            #Missing values
            missing_values = df.isnull().sum().to_frame(name="Missing Values")
            missing_values_html = missing_values.to_html()

            #Summary Statistics
            summary_stats = df.describe().to_html()

            return render_template(
                'index.html',
                file_name = file_name,
                num_rows = num_rows,
                num_cols = num_cols,
                column_names = column_names,
                preview_data = preview_data,
                missing_values = missing_values_html,
                summary_stats = summary_stats
            )
        
        return "No file selected"
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)