# clients.py - Updated to log report with SHA256
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, session, current_app
from werkzeug.utils import secure_filename
from routes import login_required
from utils import perform_screening, generate_pdf_report, log_activity
from models import User, UserDetails
from extensions import db
import os
import pandas as pd
from io import BytesIO
from datetime import datetime

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
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_excel(filepath)
                
                required_cols = ['name', 'dob', 'nationality']
                if not all(col in df.columns for col in required_cols):
                    raise ValueError("Missing required columns: name, dob, nationality")
                
                results = perform_screening(df)
                
                # Get user details for header
                user = User.query.get(session['user_id'])
                user_details_dict = {
                    'org_company': user.user_details.org_company if user.user_details else '',
                    'address': user.user_details.address if user.user_details else '',
                    'phone': user.user_details.phone if user.user_details else '',
                    'tax_reg': user.user_details.tax_reg if user.user_details else ''
                } if user.user_details else None
                
                pdf_buffer, report_hash = generate_pdf_report(results, user_details_dict)
                
                # Log the report generation
                log_activity(
                    action='Screening',
                    details=f"Report generated with {len(results)} matches",
                    report_hash=report_hash
                )
                
                flash('Screening complete – report downloaded', 'success')
                return send_file(pdf_buffer, download_name=f"screening_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", as_attachment=True)
            except ValueError as ve:
                flash(str(ve), 'error')
            except Exception as e:
                flash('Error processing file—try again.', 'error')
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)
        else:
            flash('Invalid file type—use CSV or Excel.', 'error')
    return render_template('clients.html')
