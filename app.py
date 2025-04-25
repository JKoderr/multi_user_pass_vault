from flask import Flask, request, jsonify, redirect, url_for
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import jwt
import datetime
import random
import string
import os


#initializing Flask
app = Flask(__name__)

#configuring database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vault.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecret1234'

#initializing database
db = SQLAlchemy(app)


#User and password classes
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)


class PasswordEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(80), nullable=False)
    plain_password = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('passwords', lazy=True))

def pass_gen(size, chars=string.ascii_letters + string.digits + string.punctuation):
        return ''.join(random.choice(chars) for _ in range(size))

def load_create_key():
    if os.path.exists("key.key"):
        with open("key.key", "rb") as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open("key.key", "wb") as key_file:  
            key_file.write(key)
        return key

#default endpoint path 
@app.route('/', methods = ['GET'])
def home():
    return jsonify({"message": "Hello, this is Password Vault API"})

#registering endpoint
@app.route('/register', methods = ['POST'])
def register():
    
    data = request.get_json()
#checking if data provided is valid
    if not data or 'username' not in data or 'password' not in data:
         return jsonify({"error": "Provide requested information"}), 400 #sending data as json
    
    user_name = data['username']
    raw_password = data['password']
#checking if user exists
    user = User.query.filter_by(username=user_name).first()
   
    if user:
        return jsonify({"message": "User already exist"})
    else:    
        try:
#creating new user
            new_user = User(username=user_name, 
                            password_hash=generate_password_hash(raw_password, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            return jsonify({'message': f"{user_name} created"}), 201
        except ValueError:
            return jsonify({"error": "Could not add user"}), 400
    

#login endpoint
@app.route('/login', methods = ['POST'])
def login():
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
         return jsonify({"error": "Provide requested information"}), 400 #sending data as json
    
    user_name = data['username']
    raw_password = data['password']

    user = User.query.filter_by(username=user_name).first()
    if not user or not check_password_hash(user.password_hash, raw_password):
        return jsonify({"error": "Provided username or password is not correct"}), 400

    token = jwt.encode({'public_id': user.id, 
                        'exp': datetime.datetime.now() + datetime.timedelta(minutes=15)}, 
                        app.config['SECRET_KEY'], 
                        algorithm="HS256")
    return jsonify({"message": "Login successful", "token": token}), 200
#work in progress----------------------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        
        auth_request = request.headers.get("Authorization")
        if auth_request:
            try:
               token = auth_request.split()[1]
            except IndexError:
                return jsonify({"error": "Invalid token format"})
        else:
            return jsonify({"error": "Missing token"}), 401
#finish it!!!        
        try:
            decoded = jwt.decode(token, 
                                 app.config['SECRET_KEY'], 
                                 options={"verify_exp": True}, 
                                 algorithm="HS256")
            
            user = User.query.get(decoded['public_id'])
            if not user:
                return jsonify({"error": "User not found"}), 404

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Expired"})

        return f(user, *args, **kwargs)
    return decorated

@app.route('/generate-password', methods = ['POST'])
@token_required
def generate_password(user):
    data = request.get_json()
    current_time = datetime.datetime.now()
    if not data or 'length' not in data or 'service' not in data:
         return jsonify({"error": "Provide 'length' and 'service'"}), 400
    
    length = data['length']
    input_service = data['service']
    
    if not isinstance(length, int) or length < 5:
         return jsonify({"error": "Length must be a number bigger than 4"}), 400

    password = pass_gen(length)#passing length to randomizer

    key = load_create_key()#creating or using existing key
    cipher = Fernet(key)
    encrypted_password = cipher.encrypt(password.encode())#encrypting password

    new_record = PasswordEntry(service=input_service, 
                               plain_password=encrypted_password, 
                               timestamp=current_time,
                               user_id=user.id)
    db.session.add(new_record)
    db.session.commit()

    return jsonify({"status": "success", "Time": current_time.strftime("%Y-%m-%d %H:%M"), "password": password, "service": input_service}), 201
    
