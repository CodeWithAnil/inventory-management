import re
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    dob = db.Column(db.Date, nullable=True)
    phone_no = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)  # Use SHA-256 and shorter salt
        # Adjust salt_length to generate shorter hashes, e.g., salt_length=8

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def is_valid_email(email):
        # Simple regex for email validation
        pattern = r"^[a-zA-Z][a-zA-Z0-9_.]*@nucleusteq\.com$"
        return re.match(pattern, email) is not None
