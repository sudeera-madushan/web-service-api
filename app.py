from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os

import boto3
from botocore.exceptions import NoCredentialsError

# AWS S3 configuration
AWS_ACCESS_KEY_ID = 'AKIAU6GD2NZOEHFMXDZE'
AWS_SECRET_ACCESS_KEY = '7NHJqiVQZzIrtoD/z4Uj6nhK27GTuI2Ur/TRPWl+'
AWS_BUCKET_NAME = 'bigzkoop'
AWS_S3_REGION = 'ap-south-1'  # e.g., 'us-east-1'

s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_S3_REGION
)



app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:0000@localhost:3306/web_service_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    picture = db.Column(db.String(455), nullable=False)
    age = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'picture': self.picture,
            'date_of_birth': self.date_of_birth,
            'age': self.age
        }

from werkzeug.utils import secure_filename
import uuid


@app.route('/api/v1/user', methods=['POST'])
def add_user():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save image to S3
    filename = secure_filename(file.filename)
    unique_filename = str(uuid.uuid4()) + '-' + filename
    try:
        s3.upload_fileobj(file, AWS_BUCKET_NAME, unique_filename)
        file_url = f'https://{AWS_BUCKET_NAME}.s3.{AWS_S3_REGION}.amazonaws.com/{unique_filename}'
    except NoCredentialsError:
        return jsonify({'error': 'Credentials not available'}), 500

    data = request.form
    name = data['name']
    dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d')
    today = datetime.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    new_user = User(name=name, age=age, picture=file_url, date_of_birth=dob)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User added successfully'})

@app.route('/api/v1/user', methods=['GET'])
def get_all_users():
    users = User.query.all()
    return jsonify({'users': [user.to_dict() for user in users]})



@app.route('/api/v1', methods=['GET'])
def hello():
    return 'Hello, Python!'

if __name__ == '__main__':
    app.run(debug=True)
