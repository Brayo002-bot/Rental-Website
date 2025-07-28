from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

auth_routes = Blueprint('auth_routes', __name__)

# Example dummy register endpoint
@auth_routes.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = generate_password_hash(data.get('password'))

    # Normally insert into DB here...
    return jsonify({"message": "User registered", "user": {"name": name, "email": email}})
