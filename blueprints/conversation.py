'''Stores, and allows access to the conversation details.'''
from flask import Blueprint, request, jsonify
from uuid import uuid1, UUID
import json
import os
from threading import Lock
from openai import AzureOpenAI
from slideshow_generator import SlideshowGenerator
from gpt4 import client, SYSTEM_PROMPT, tools, delegate_function_call

'''Storage for Conversations'''


class Conversation:
    def __init__(self, account: str = None, json_input=None) -> None:
        if json_input is not None:
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
            "uuid": str(self.uuid),
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
            return [Conversation(json_input=obj) for obj in conversations if obj["account"] == user]


def add_new_conversation(conv: Conversation):
    with conversation_mutex:
        conversations = None

        with open('./conversations/list.json', 'r') as convs_file:
            conversations = json.loads(convs_file.read())

        with open('./conversations/list.json', 'w') as convs_file:
            conversations.append(conv.toJSON())

            convs_file.write(json.dumps(conversations))


def update_conversation(conv: Conversation):
    with conversation_mutex:
        conversations = None

        with open('./conversations/list.json', 'r') as convs_file:
            conversations = json.loads(convs_file.read())

        with open('./conversations/list.json', 'w') as convs_file:
            for i in range(len(conversations)):
                con = Conversation(json_input=conversations[i])

                if con.uuid == conv.uuid:
                    conversations[i] = conv.toJSON()

            convs_file.write(json.dumps(conversations))


def recreate_generator(messages: list) -> SlideshowGenerator:
    gen = SlideshowGenerator()

    for msg in messages:
        if msg.get('tool_calls'):
            for call in msg.get('tool_calls'):
                function = call.get('function')
                if function.get('name') == 'save':
                    continue
                delegate_function_call(gen, function.get('name'), function.get('arguments'))

    return gen


conversation_controller = Blueprint('conversation_controller', __name__)


@conversation_controller.route('/conversation/chat', methods=['POST'])
def chat():
    uuid = request.json.get('uuid')
    username = request.json.get('username')
    new_message = request.json.get('message')

    conv = None

    if uuid == 'create_new':
        conv = Conversation(account=username)
        add_new_conversation(conv)
    else:
        uuid = UUID(uuid)
        conversations = get_conversations(username)

        for conversation in conversations:
            if conversation.uuid == uuid:
                conv = conversation
                break

    if conv is None:
        return jsonify({"success": False, "message": "UUID not recognized"})

    conv.messages.append({"role": "user", "content": new_message})

    RESPONSE = client.chat.completions.create(
        model="slidesai",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conv.messages,
        tools=tools
    )

    choice = RESPONSE.choices[0]
    if choice.message.content is None:
        choice.message.content = ""

    gen = recreate_generator(conv.messages)

    model_json = json.loads(choice.message.model_dump_json())

    if not model_json.get("function_call"):
        model_json.pop("function_call")
    if not model_json.get("tool_calls"):
        model_json.pop("tool_calls")

    conv.messages.append(model_json)

    if choice.finish_reason == 'tool_calls':

        for call in choice.message.tool_calls:
            function_name = call.function.name
            print(call)

            content = delegate_function_call(gen, call.function.name, call.function.arguments)

            print(content)
            conv.messages.append(
                {
                    "tool_call_id": call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": content,
                }
            )

    update_conversation(conv)

    return jsonify(conv.toJSON())


@conversation_controller.route('/conversation/get_messages')
def get_message():
    uuid = request.json.get('uuid')
    username = request.json.get('username')

    conv = None

    if uuid == 'create_new':
        return jsonify({"success": False, "message": "UUID not recognized"})
    else:
        uuid = UUID(uuid)
        conversations = get_conversations(username)

        for conversation in conversations:
            if conversation.uuid == uuid:
                conv = conversation
                break

    if conv is None:
        return jsonify({"success": False, "message": "UUID not recognized"})

    return jsonify(conv.toJSON())


@conversation_controller.route('/conversation/list')
def list_conversations():
    pass


@conversation_controller.route('/conversation/get_presentation')
def get_presentation():
    pass
