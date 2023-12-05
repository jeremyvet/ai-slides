'''Main File'''
from flask import Flask
from waitress import serve
from blueprints.conversation import conversation_controller

if __name__ == "__main__":
    app = Flask(__name__)

    app.register_blueprint(conversation_controller)

    print('starting server...')

    serve(app, host='0.0.0.0', port="80")