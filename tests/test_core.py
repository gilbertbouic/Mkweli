import pytest
from app import app, db
from models import User, Log, Individual
from utils import perform_screening, generate_pdf_report, log_activity, update_sanctions_lists
from routes import login_required
from flask import session
from datetime import date
import os

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_user_model_validation():
    with pytest.raises(ValueError, match="Invalid username"):
        User(username="in!", password="SecurePass123!")
    with pytest.raises(ValueError, match="Password must be"):
        User(username="admin", password="short")
    user = User(username="Admin", password="SecurePass123!")
    assert user.username == "admin"
    assert user.check_password("SecurePass123!")

def test_login_function(client):
    with app.app_context():
        user = User(username="test", password="TestPass123!")
        db.session.add(user)
        db.session.commit()
    rv = client.post('/login', data={'username': 'test', 'password': 'TestPass123!'})
    assert rv.status_code == 302
    rv = client.post('/login', data={'username': 'test', 'password': 'wrong'})
    assert b'Invalid credentials' in rv.data

def test_login_required_decorator(client):
    @app.route('/protected')
    @login_required
    def protected():
        return "OK"
    rv = client.get('/protected')
    assert rv.status_code == 302
    with client:
        with client.session_transaction() as sess:
            sess['user_id'] = 1
        rv = client.get('/protected')
        assert b'OK' in rv.data

def test_update_sanctions_lists_missing_file():
    with pytest.raises(ValueError, match="Missing sanctions file"):
        update_sanctions_lists()  # Assumes no files in data/

def test_update_sanctions_lists_invalid_xml(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    app.config['DATA_DIR'] = str(data_dir)  # Override for test
    invalid_file = data_dir / "un_consolidated.xml"
    invalid_file.write_text("<invalid>")
    with pytest.raises(ValueError, match="Parse error"):
        update_sanctions_lists()

def test_perform_screening_valid_match(client):
    with app.app_context():
        ind = Individual(reference_number="TEST1", name="John Doe", dob=date(1990, 1, 1), nationality="USA", source="test")
        db.session.add(ind)
        db.session.commit()
        matches = perform_screening({'name': "John Doe", 'dob': date(1990, 1, 1), 'nationality': "USA"})
        assert len(matches) == 1
        assert matches[0]['score'] >= 82

def test_perform_screening_no_match(client):
    with app.app_context():
        matches = perform_screening({'name': "No Match"})
        assert len(matches) == 0

def test_perform_screening_invalid_input(client):
    with pytest.raises(ValueError, match="Client name required"):
        perform_screening({})

def test_generate_pdf_report_valid(client):
    report_data = {'title': 'Test Report', 'content': 'Details'}
    pdf, hash_val = generate_pdf_report(report_data)
    assert len(pdf) > 0
    assert len(hash_val) == 64

def test_generate_pdf_report_invalid(client):
    with pytest.raises(ValueError, match="Report data required"):
        generate_pdf_report(None)

def test_log_activity_valid(client):
    with app.app_context():
        user = User(username="logger", password="SecurePass123!")
        db.session.add(user)
        db.session.commit()
        log_activity(user.id, "Test Action", "test_hash")
        log_entry = Log.query.first()
        assert log_entry.action == "Test Action"
        assert log_entry.report_hash == "test_hash"

def test_log_activity_invalid(client):
    with pytest.raises(ValueError, match="User ID and action required"):
        log_activity(None, "")
