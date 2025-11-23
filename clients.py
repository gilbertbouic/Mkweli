from flask import Blueprint, render_template, request, flash, session
from functools import wraps
from routes import login_required

clients = Blueprint('clients', __name__)

@clients.route('/clients')
@login_required
def clients_screening():
    return render_template('name_checker.html')
