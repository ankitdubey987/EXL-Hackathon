import logging
import os
from typing import Any
from flask import (
    Flask,
    jsonify,
    make_response,
    request,
    abort)
from cloud_providers.platforms import FileUploadError, RequriedParameterMissing, FileDownloadError, AzureConnectionError,AWSConnectionError
from cloud_providers.platforms import CloudProviderType
from cloud_providers.services import (
    get_storage_provider,
    get_service_provider_client,
    map_cloud_providers)
from uuid import uuid4
from werkzeug.security import (
    generate_password_hash,
    check_password_hash)
from datetime import datetime, timedelta
from database.db_handler import users
from models.users import create_user,set_azure_cloud_details, set_aws_cloud_details
from functools import wraps
import jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'this-really-needs-to-be-changed'


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        # return 401 if token is not passed
        if not token:
            return jsonify({'message': 'Token is missing !!'}), 401

        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')
            print(data)
            current_user = users.find_one({
                "public_id": data.get('public_id')
            })
        except Exception:
            return jsonify({
                'message': 'Token is invalid !!'
            }), 401
        # returns the current logged in users contex to the routes
        return f(current_user, *args, **kwargs)
    return decorated


@app.route('/upload-public', methods=['POST'])
def upload_anonymously_data():
    # For this we assume that bucket is publically accessible
    if not request.method == 'POST':
        abort(405)
    provider: str = request.form['provider']
    file_data = request.files.get('file')
    form_data = request.form
    try:
        storage_provider = get_storage_provider(provider, form_data)
        service_provider = get_service_provider_client(storage_provider)
        service_provider.provider.upload_blob_public(file_data)
    except RequriedParameterMissing as pre:
        return make_response(
            str(pre),
            400
        )
    except FileUploadError as fe:
        return make_response(
            str(fe),
            400
        )
    except (AzureConnectionError,AWSConnectionError) as ace:
        return jsonify(make_response(
            str(ace),
            409
        ))
    return jsonify(status=200,message='Upload success!')


@app.route('/view-public', methods=['POST'])
def get_public_data_url():
    # For this we assume that bucket is publically accessible
    if not request.method == 'POST':
        abort(405)
    filename: str = request.form['filename']
    provider: str = request.form['provider']
    form_data = request.form
    try:
        storage_provider = get_storage_provider(provider, form_data)
        service_provider = get_service_provider_client(storage_provider)
    except (AzureConnectionError,AWSConnectionError) as ace:
        return jsonify(make_response(
            str(ace),
            409
        ))
    return jsonify(service_provider.provider.get_temp_blob_link(filename))


@app.route('/delete', methods=['POST'])
@token_required
def delete_blob(current_user):
    if not request.method == 'POST':
        abort(405)
    provider: str = request.form['provider']
    cloud_providers_list =list(users.find(
        filter={'public_id':current_user.get('public_id')}
        ))
    if not cloud_providers_list:
        return make_response(
            'Cloud providers not present for the user!',
            404
        )
    if not (provider in [user_cloud.get('cloud_provider') for user_cloud in cloud_providers_list]):
        return make_response(
            'Cloud providers not present for the user!',
            404
        )
    cloud_providers_list = users.find_one(filter={'public_id':current_user.get('public_id'), 'cloud_provider': provider})
    filename: str = request.form['filename']
    try:
        storage_provider = get_storage_provider(
            cloud_providers_list.get('cloud_provider'),
            cloud_providers_list)
        service_provider = get_service_provider_client(storage_provider)
    except (AzureConnectionError,AWSConnectionError) as ace:
        return jsonify(make_response(
            str(ace),
            409
        ))
    ret = service_provider.provider.delete_blob(filename)
    if not ret:
        return make_response(jsonify(status=400, message='Encountered Error while deleting the object!', data=None), 400)
    return make_response(jsonify(status=200, message='Success', data=ret), 200)


@app.route('/all', methods=['POST'])
@token_required
def list_blobs(current_user):
    if not request.method == 'POST':
        abort(405)
    provider: str = request.form['provider']
    cloud_providers_list =list(users.find(
        filter={'public_id':current_user.get('public_id')}
        ))
    if not cloud_providers_list:
        return make_response(
            'Cloud providers not present for the user!',
            404
        )
    if not (provider in [user_cloud.get('cloud_provider') for user_cloud in cloud_providers_list]):
        return make_response(
            'Cloud providers not present for the user!',
            404
        )
    cloud_providers_list = users.find_one(filter={'public_id':current_user.get('public_id'), 'cloud_provider': provider})
    
    try:
        storage_provider = get_storage_provider(
            cloud_providers_list.get('cloud_provider'),
            cloud_providers_list)
        service_provider = get_service_provider_client(storage_provider)
        data = service_provider.provider.list_blob()
        print(data)
        return jsonify(status=200, message='Success', data= data)
    except RequriedParameterMissing as rpe:
        return jsonify(make_response(
            str(rpe),
            412
        ))
    except (AzureConnectionError,AWSConnectionError) as ace:
        return jsonify(make_response(
            str(ace),
            409
        ))


@app.route('/download', methods=['POST'])
@token_required
def download_data(current_user):
    if not request.method == 'POST':
        abort(405)
    provider: str = request.form['provider']
    filename: str = request.form['filename']
    cloud_providers_list =list(users.find(
        filter={'public_id':current_user.get('public_id')}
        ))
    if not cloud_providers_list:
        return jsonify(make_response(
            'Cloud providers not present for the user!',
            404
        ))
    if not (provider in [user_cloud.get('cloud_provider') for user_cloud in cloud_providers_list]):
        return jsonify(make_response(
            'Cloud providers not present for the user!',
            404
        ))
    cloud_providers_list = users.find_one(filter={'public_id':current_user.get('public_id'), 'cloud_provider': provider})
    
    try:
        storage_provider = get_storage_provider(
            cloud_providers_list.get('cloud_provider'),
            cloud_providers_list)
        service_provider = get_service_provider_client(storage_provider)
        data = service_provider.provider.download_blob(filename)
    except FileDownloadError as fe:
        return jsonify(make_response(
            str(fe),
            409
        ))
    except (AzureConnectionError,AWSConnectionError) as ace:
        return jsonify(make_response(
            str(ace),
            409
        ))
    
    return jsonify(status=200,message='Success', data= data)


@app.route('/upload', methods=['POST'])
@token_required
def upload_data(current_user):
    if not request.method == 'POST':
        abort(405)
    data: Any = request.files.get('file')
    provider: str = request.form['provider']
    cloud_providers_list =list(users.find(
        filter={'public_id':current_user.get('public_id')}
        ))
    if not cloud_providers_list:
        return make_response(
            'Cloud providers not present for the user!',
            404
        )
    if not (provider in [user_cloud.get('cloud_provider') for user_cloud in cloud_providers_list]):
        return make_response(
            'Cloud providers not present for the user!',
            404
        )
    cloud_providers_list = users.find_one(filter={'public_id':current_user.get('public_id'), 'cloud_provider': provider})
    try:
        storage_provider = get_storage_provider(
            cloud_providers_list.get('cloud_provider'),
            cloud_providers_list)
        service_provider = get_service_provider_client(storage_provider)
        service_provider.provider.upload_blob(data)
    except Exception as e:
        logging.error(e)
        return make_response(
            str(e),
            400
        )
    return jsonify(status=200,message='Upload Done!')


@app.route('/add', methods=['POST'])
@token_required
def add_cloud_cred(current_user):
    form = request.form
    cloud_provider = form.get('cloud_provider')
    if not cloud_provider:
        return make_response(
            'Required parameter missing!',
            409
        )
    if cloud_provider == CloudProviderType.AWS.value:
        access_key_id = form.get('access_key')
        secret_access_key = form.get('secret_access_key')
        bucket_name = form.get('bucket_name')
        if not (access_key_id or secret_access_key or bucket_name):
            return make_response(
                'Required parameter missing!',
                409
            )
        user_cloud_info = set_aws_cloud_details(
            public_id=current_user.get('public_id'),
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            bucket_name=bucket_name
        )
    if cloud_provider == CloudProviderType.AZ.value:
        connection_string = form.get('connection_string')
        container_name = form.get('bucket_name')
        if not (connection_string or container_name):
            return make_response(
                'Required parameter missing!',
                409
            )
        user_cloud_info = set_azure_cloud_details(
            public_id=current_user.get('public_id'),
            az_connection_string=connection_string,
            bucket_name=container_name
        )
    if not user_cloud_info:
        return make_response('Something went wrong try again!', 304)
    return make_response('Successfully, Cloud Info registered.', 201)


@app.route('/login', methods=['POST'])
def login():
    auth = request.form
    if not auth or not auth.get('email') or not auth.get('password'):
        return make_response(
            'Could not verify',
            401,
            {'WWW-Authenticate': 'Basic realm ="Login Required!"'}
        )
    user = users.find_one({
        "email": auth.get('email')
    })
    if not user:
        return make_response(
            'Could not verify',
            401,
            {'WWW-Authenticate': 'Basic realm ="Login Required!"'}
        )
    if check_password_hash(user.get('password'), auth.get('password')):
        token: str = jwt.encode({
            'public_id': user.get('public_id'),
            'exp': datetime.utcnow() + timedelta(minutes=30)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return make_response(
            jsonify(
                token=token
            ), 201
        )
    return make_response(
        'Could not Verify',
        403,
        {'WWW-Authenticate': 'Basic realm ="Wrong Password !!"'}
    )


@app.route('/signup', methods=['POST'])
def signup():
    # creates a dictionary of the form data
    data = request.form
    # gets name, email and password
    name, email = data.get('name'), data.get('email')
    password = data.get('password')
    provider = data.get('provider')
    # checking for existing user
    ext_user = users.find_one({"email": email})
    if not ext_user:
        # database ORM object
        new_user = create_user(
            str(uuid4()),
            name,
            email,
            generate_password_hash(password),
            provider
        )
        return make_response(f'UserId:{new_user} Successfully registered.', 201)
    else:
        # returns 202 if user already exists
        return make_response('User already exists. Please Log in.', 202)


@app.route('/', methods=['GET'])
def index():
    if not request.method == 'GET':
        abort(405)
    return jsonify(
        status_code=200,
        message='Success',
        data="Welcome to common solution for EXL Hackathons"
    )


if __name__ == '__main__':
    if os.getenv('APP_ENV'):
        ENVIRONMENT_DEBUG = os.environ.get("APP_DEBUG", True)
        ENVIRONMENT_PORT = os.environ.get("APP_PORT", 5000)
        app.run(host='0.0.0.0', port=ENVIRONMENT_PORT, debug=ENVIRONMENT_DEBUG)
    else:
        app.run(use_reloader=True)
