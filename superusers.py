import click
from flask.cli import with_appcontext
from admin.model import Admin
from werkzeug.security import generate_password_hash
from mongoengine import connect
connect(db='ride_db', host='localhost',port=27017)

import hashlib
hashed_password = generate_password_hash("admin1123")  # werkzeug style

admin=Admin(username="admin", email="rivalondon7@gmail.com", is_superuser=True, password=hashed_password)
admin.save()


