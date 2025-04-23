from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os
import string


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

#default endpoint path 
@app.route('/', methods = ['GET'])
def home():
    return jsonify({"message": "Hello, this is Password Vault API"})

#registering endpoint
@app.route('/register', methods = ['POST'])
def register():
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
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
            new_user = User(username=user_name, password_hash=generate_password_hash(raw_password, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            return jsonify({'message': f"{user_name} created"}), 201
        except ValueError:
            return jsonify({"error": "Could not add user"}), 400

#login endpoint
@app.route('/login', methods = ['POST'])
def login():
    return
