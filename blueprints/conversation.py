'''Stores, and allows access to the conversation details.'''
from flask import Blueprint, request, jsonify
from uuid import uuid1, UUID
import json
import os
from threading import Lock
from openai import AzureOpenAI
from slideshow_generator import SlideshowGenerator

client = AzureOpenAI(
  azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
  api_key=os.getenv("AZURE_OPENAI_API_KEY"),
  api_version="2023-07-01-preview"
)

'''Storage for Conversations'''
class Conversation:
    def __init__(self, account:str=None, json_input=None) -> None:
        if json is not None:
            self.uuid = UUID(json_input["uuid"])
            self.messages = json_input["messages"]
            self.presentations = json_input["presentations"]
            self.account = json_input["account"]
        else:
            self.uuid = uuid1()
            self.messages = []
            self.presentations = []
            self.account = account
    
    def toJSON(self):
        return {
            "uuid": self.uuid,
            "messages": self.messages,
            "presentations": self.presentations,
            "account": self.account
        }

conversation_mutex = Lock()

def get_conversations(user=None):
    with conversation_mutex:
        conversations = None
        

        with open('./conversations/list.json', 'r') as convs_file:
            conversations = json.loads(convs_file.read())
        
        if user is None:
            return [Conversation(json_input=conversations) for obj in conversations]
        else:
            return [Conversation(json_input=obj) for obj in conversations if obj.account == user]

def add_new_conversation(conv: Conversation):
    with conversation_mutex:
        conversations = None
        

        with open('./conversations/list.json', 'w') as convs_file:
            conversations = json.loads(convs_file.read())

            conversations.append(conv.toJSON())
            
            convs_file.write(json.dumps(conversations))


conversation_controller = Blueprint('conversation_controller', __name__)

@conversation_controller.route('/conversation/chat')
def chat():
    
    uuid = UUID(request.json.get('uuid'))
    username = request.json.get('username')
    new_message = request.json.get('message')

    conv = None

    if uuid == 'create_new':
        conv = Conversation(username)
        add_new_conversation(conv)
    else:
        conversations = get_conversations(username)

        for conversation in conversations:
            if conversation.uuid == uuid:
                conv = conversation
                break
    
    if conversation is None:
        return jsonify({"success": False, "message": "UUID not recognized"})
    
    conversation.messages.append({"role": "user", "content": new_message})

    


    


@conversation_controller.route('/conversation/get_messages')
def get_message():
    pass

@conversation_controller.route('/conversation/list')
def list_conversations():
    pass

@conversation_controller.route('/conversation/get_presentation')
def get_presentation():
    pass