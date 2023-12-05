'''Stores, and allows access to the conversation details.'''
from flask import Blueprint, request, jsonify


conversation_controller = Blueprint('conversation_controller', __name__)


@conversation_controller.route('/conversation/chat')
def chat():
    pass

@conversation_controller.route('/conversation/get_messages')
def get_message():
    pass

@conversation_controller.route('/conversation/list')
def list_conversations():
    pass