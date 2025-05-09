from flask import Flask, request, jsonify, redirect, url_for
from flask_cors import CORS
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
CORS(app, origins=["http://127.0.0.1:5500"])

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

#pseudo-randomizer
def pass_gen(size, chars=string.ascii_letters + string.digits + string.punctuation):
        return ''.join(random.choice(chars) for _ in range(size))

#key generating function
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
                            password_hash=generate_password_hash(raw_password))
            db.session.add(new_user)
            db.session.commit()
            return jsonify({'message': f"{user_name} created"}), 201
        except Exception as e:
            return jsonify({"error": f"Could not add user: {str(e)}"}), 400

    

#login endpoint
@app.route('/login', methods = ['POST'])
def login():
    data = request.get_json()
#checking if data is valid
    if not data or 'username' not in data or 'password' not in data:
         return jsonify({"error": "Provide requested information"}), 400 #sending data as json
    
    user_name = data['username']
    raw_password = data['password']
#checking data is in db
    user = User.query.filter_by(username=user_name).first()
    if not user or not check_password_hash(user.password_hash, raw_password):
        return jsonify({"error": "Provided username or password is not correct"}), 400
#creating token for logged user
    token = jwt.encode({'public_id': user.id, 
                        'exp': datetime.datetime.now() + datetime.timedelta(minutes=15)}, 
                        app.config['SECRET_KEY'], 
                        algorithm="HS256")
    return jsonify({"message": "Login successful", "token": token}), 200
#jwt verification decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
#checking header with jwt        
        auth_request = request.headers.get("Authorization")
        if auth_request:
            try:
               token = auth_request.split()[1]
            except IndexError:
                return jsonify({"error": "Invalid token format"})
        else:
            return jsonify({"error": "Missing token"}), 401
#decoding token if not expierd     
        try:
            decoded = jwt.decode(token, 
                                 app.config['SECRET_KEY'], 
                                 algorithms=["HS256"])
#checking user id            
            user = User.query.get(decoded['public_id'])
            if not user:
                return jsonify({"error": "User not found"}), 404

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Expired"})

        return f(user, *args, **kwargs)
    return decorated
#password generating function
@app.route('/generate-password', methods = ['POST'])
@token_required #verification decorator
def generate_password(user):
#getting data from user
    data = request.get_json()
    current_time = datetime.datetime.now()
    if not data or 'length' not in data or 'service' not in data:
         return jsonify({"error": "Provide 'length' and 'service'"}), 400
    
    length = data['length']
    input_service = data['service']
    
    if not isinstance(length, int) or length < 5:
         return jsonify({"error": "Length must be a number bigger than 4"}), 400
#generating random password
    password = pass_gen(length)
#creating key and encryption
    key = load_create_key()
    cipher = Fernet(key)
    encrypted_password = cipher.encrypt(password.encode())#encrypting password
#pushing input and password to db
    new_record = PasswordEntry(service=input_service, 
                               plain_password=encrypted_password, 
                               timestamp=current_time,
                               user_id=user.id)
    db.session.add(new_record)
    db.session.commit()

    return jsonify({"status": "success", "Time": current_time.strftime("%Y-%m-%d %H:%M"), "password": password, "service": input_service}), 201

#password showing function
@app.route('/get-passwords', methods = ['POST'])
@token_required #verification decorator
def get_passwords(user):
    key = load_create_key()#creating or using existing key
    cipher = Fernet(key)
    passwords = []
    entries = PasswordEntry.query.filter_by(user_id=user.id).all()

    for entry in entries:    
           decrypted_password = cipher.decrypt(entry.plain_password).decode()#decrypting password      
           passwords.append({
                "timestamp": entry.timestamp.strftime("%Y-%m-%d %H:%M"),
                "service": entry.service,
                "password": decrypted_password
                })
    

    return jsonify({"Your data": passwords}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


