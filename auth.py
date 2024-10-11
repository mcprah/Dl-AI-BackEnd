from flask import Blueprint, request, jsonify, make_response
from bson import ObjectId
from flask_bcrypt import Bcrypt
import datetime
from utils import create_user_pseudo_id
from mongodb import users_collection
import logging

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()

        # Check if the user already exists
        existing_user = users_collection.find_one({"$or": [{"email": data['email']}, {"username": data['username']}]} )
        if existing_user:
            logging.debug('User already exists: %s', existing_user)
            return jsonify({'message': 'User already exists!'}), 400

        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        user_pseudo_id = create_user_pseudo_id()

        new_user = {
            "username": data['username'],
            "email": data['email'],
            "full_name": data['full_name'],
            "password": hashed_password,
            "user_pseudo_id": user_pseudo_id,
            "created_at": datetime.datetime.utcnow()
        }

        users_collection.insert_one(new_user)

        # Set cookie with userPseudoId, expiry in 2 years
        response = make_response(jsonify({'message': 'User created successfully!'}))
        expiry_date = datetime.datetime.utcnow() + datetime.timedelta(days=730)  # 2 years
        response.set_cookie('userPseudoId', user_pseudo_id, expires=expiry_date)
        
        logging.debug('User created successfully with pseudo ID: %s', user_pseudo_id)

        return response

    except Exception as e:
        logging.error('Error during signup: %s', str(e))
        return jsonify({'message': 'Internal Server Error'}), 500

# Login route
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    user = users_collection.find_one({"$or": [{"email": data['email_or_username']}, {"username": data['email_or_username']}]})

    if not user or not bcrypt.check_password_hash(user['password'], data['password']):
        return jsonify({'message': 'Login failed, check your credentials'}), 401

    # Set cookie with userPseudoId, expiry in 2 years
    response = make_response(jsonify({
        'username': user['username'],
        'email': user['email'],
        'full_name': user['full_name'],
        'user_pseudo_id': user['user_pseudo_id']
    }))
    expiry_date = datetime.datetime.utcnow() + datetime.timedelta(days=730)  # 2 years
    response.set_cookie('userPseudoId', user['user_pseudo_id'],expires=expiry_date, samesite='Lax', secure=False)

    return response
