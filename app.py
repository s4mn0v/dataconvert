from flask import Flask, render_template, request, send_file, url_for, redirect
from werkzeug.utils import secure_filename
import io
from excel_processor import combine_excel_sheets
import pandas as pd

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file_type = request.form['file_type']
        upload_type = request.form['upload_type']
        
        files_to_process = []

        if upload_type == 'file':
            if 'file' not in request.files:
                return render_template('index.html', error='No file part')
            file = request.files['file']
            if file.filename == '':
                return render_template('index.html', error='No selected file')
            if file and allowed_file(file.filename):
                files_to_process.append((file.filename, file.read()))
            else:
                return render_template('index.html', error='File type not allowed')
        elif upload_type == 'folder':
            if 'folder' not in request.files:
                return render_template('index.html', error='No folder selected')
            files = request.files.getlist('folder')
            for file in files:
                if file and allowed_file(file.filename):
                    files_to_process.append((file.filename, file.read()))

        if not files_to_process:
            return render_template('index.html', error='No valid files to process')

        try:
            data, log = combine_excel_sheets(files_to_process, file_type)
            if not data.empty:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    data.to_excel(writer, index=False)
                output.seek(0)
                return send_file(
                    output,
                    as_attachment=True,
                    download_name='processed_data.xlsx',
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            else:
                return render_template('index.html', error='No data to process', log=log)
        except Exception as e:
            return render_template('index.html', error=str(e))
    
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)