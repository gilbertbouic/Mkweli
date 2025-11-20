# clients.py - Blueprint for client screening (upload, fuzzy match, report gen). Modular; single responsibility.
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from functools import wraps
from routes import login_required  # Reuse auth decorator
from utils import perform_screening, generate_pdf_report  # Modular utils
from models import Individual, Alias  # For DB matching
import os
import pandas as pd
from io import BytesIO

clients = Blueprint('clients', __name__, template_folder='templates')

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@clients.route('/clients', methods=['GET', 'POST'])
@login_required
def clients_screening():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)  # Sanitize filename (security)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_excel(filepath)
                # Validate columns (security/performance)
                required_cols = ['name', 'dob', 'nationality']
                if not all(col in df.columns for col in required_cols):
                    raise ValueError("Missing required columns")
                results = perform_screening(df)  # Modular matching
                pdf_buffer = generate_pdf_report(results)  # Modular report
                flash('Screening complete', 'success')
                return send_file(pdf_buffer, attachment_filename='screening_report.pdf', as_attachment=True)
            except ValueError as ve:
                flash(str(ve), 'error')
            except Exception as e:
                flash('Error processing file—try again.', 'error')
            finally:
                os.remove(filepath)  # Cleanup (performance/security)
        else:
            flash('Invalid file type—use CSV or Excel.', 'error')
    return render_template('clients.html')  # Simple UI with upload form

# Add more routes if needed (e.g., view results)
