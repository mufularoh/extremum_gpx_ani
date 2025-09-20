from flask import Flask 
from . import cropper

def create_app(*args, **kwargs):
    app = Flask("cropper")
    app.register_blueprint(cropper.bp)


    return app


