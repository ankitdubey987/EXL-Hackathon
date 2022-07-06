from pymongo import MongoClient
import os

if os.getenv('APP_ENV'):
    MONGO_URI = 'mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOSTNAME'] + ':27017/' + os.environ['MONGODB_DATABASE']
    client = MongoClient(MONGO_URI)
else:
    client = MongoClient('localhost', 27017)
db = client.cloud_users
users = db.users