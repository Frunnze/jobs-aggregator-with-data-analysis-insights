import pytest
from app.models import User, Subscription
from app import db, create_app


# Helper function to create a test user
def create_test_user(client, name, email, password):
    return client.post('/sign-up', json={
        "name": name,
        "email": email,
        "password": password
    })

@pytest.fixture(scope='module')
def test_client():
    # Setup: Create a new app for testing
    flask_app = create_app()
    
    # Flask provides a way to access test request context
    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            # Create test database schema
            db.create_all()
            yield testing_client
            # Teardown: Drop the test database
            db.drop_all()

def test_status_endpoint(test_client):
    """Test the status endpoint"""
    response = test_client.get('/status')
    assert response.status_code == 200
    assert response.json == {"msg": "Service is running"}

def test_sign_up_successful(test_client):
    """Test the sign-up endpoint for a successful request"""
    response = create_test_user(test_client, "John Doe", "john@example.com", "password123")
    assert response.status_code == 201
    assert response.json["msg"] == "Successful sign up!"
    assert "user_id" in response.json

def test_sign_up_invalid_email(test_client):
    """Test sign-up with an invalid email format"""
    response = test_client.post('/sign-up', json={
        "name": "Jane Doe",
        "email": "invalidemail",
        "password": "password123"
    })
    assert response.status_code == 400
    assert response.json["msg"] == "Invalid email"

def test_sign_up_password_too_short(test_client):
    """Test sign-up with a password that's too short"""
    response = test_client.post('/sign-up', json={
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "123"
    })
    assert response.status_code == 400
    assert response.json["msg"] == "Password too short"

def test_sign_up_user_already_exists(test_client):
    """Test sign-up when user already exists"""
    create_test_user(test_client, "John Doe", "john@example.com", "password123")
    # Try to sign up again with the same email
    response = create_test_user(test_client, "John Doe", "john@example.com", "password123")
    assert response.status_code == 409
    assert response.json["msg"] == "User already exists"

def test_login_successful(test_client):
    """Test login with valid credentials"""
    # Create a user for login
    create_test_user(test_client, "John Doe", "john@example.com", "password123")
    
    # Login with valid credentials
    response = test_client.post('/login', json={
        "email": "john@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert response.json["msg"] == "Successful login!"
    assert "user_id" in response.json

def test_login_invalid_email(test_client):
    """Test login with an invalid email"""
    response = test_client.post('/login', json={
        "email": "invalid@example.com",
        "password": "password123"
    })
    assert response.status_code == 401
    assert response.json["msg"] == "Invalid email or password"

def test_login_invalid_password(test_client):
    """Test login with an invalid password"""
    # Create a user for login
    create_test_user(test_client, "John Doe", "john@example.com", "password123")
    
    # Login with wrong password
    response = test_client.post('/login', json={
        "email": "john@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert response.json["msg"] == "Invalid email or password"

def test_get_subscriptions(test_client):
    """Test fetching subscriptions for a user"""
    # Create a user
    create_test_user(test_client, "John Doe", "john@example.com", "password123")
    
    # Manually add subscriptions to the database
    user = User.query.filter_by(email="john@example.com").first()
    sub1 = Subscription(room_name="Room 1", user_id=user.id)
    sub2 = Subscription(room_name="Room 2", user_id=user.id)
    db.session.add(sub1)
    db.session.add(sub2)
    db.session.commit()
    
    # Fetch subscriptions for the user
    response = test_client.get(f'/get-subscriptions/{user.id}')
    assert response.status_code == 200
    assert response.json == ["Room 1", "Room 2"]