from flask import Flask
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from auth import auth_bp
from discovery_engine import discovery_bp
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)
bcrypt = Bcrypt(app)

# Register Blueprints for modular structure
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(discovery_bp, url_prefix='/discovery')

# Secret key for JWT
app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG')

@app.route('/')
def hello_world():
    return "DennisLaw Python Backend is Live Now!"

if __name__ == '__main__':
    app.run(debug=True)
