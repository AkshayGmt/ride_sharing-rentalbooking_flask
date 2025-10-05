from flask import Flask
from flask_mongoengine import MongoEngine
from socket_event import socketio
from admin.routes import admin_bp
from flask_wtf.csrf import CSRFProtect
#from flask.ext.superadmin import Admin, model
db = MongoEngine()




def create_app():
    app = Flask(__name__)
    app.config["MONGODB_SETTINGS"] = {
        "db": "ride_db",
        "host": "localhost",
        "port": 27017
    }
    app.config["MONGO_URI"] = "mongodb://localhost:27017/ride_db"

    db.init_app(app)
    socketio.init_app(app)
    
    

    app.secret_key = "3b340eb4de50295ba76cec8d8743581528d6101891039812c45503ad33ddc0c5"
    # app.config["SECRET_KEY"] = "3b340eb4de50295ba76cec8d8743581528d6101891039812c45503ad33ddc0c5"
    # Import blueprints
    from core.routes import core_bp
    from passenger.routes import passenger_bp
    from driver.routes import driver_bp
    # Enable CSRF protection
    csrf = CSRFProtect(app)
    
    app.register_blueprint(core_bp)
    app.register_blueprint(passenger_bp, url_prefix="/passenger")
    app.register_blueprint(driver_bp, url_prefix="/driver")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    #socketio = SocketIO(app, cors_allowed_origins="*")

    print(app.url_map)

    return app


if __name__ == "__main__":
    app = create_app()
    socketio.run(app,port=5001, debug=True)
