'''Docstring'''
import os
import json
from openai import AzureOpenAI
from slideshow_generator import SlideshowGenerator

client = AzureOpenAI(
  azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
  api_key=os.getenv("AZURE_OPENAI_API_KEY"),
  api_version="2023-07-01-preview"
)

msgs = [
    {"role": "system", "content": "You are a slideshow making assistant. "
                                  "You will use blanktheme.pptx as your theme unless told otherwise."
                                  ""},
    {"role": "user", "content": input()},
]

themes = [ "layoutslides", "test_notugly", "blanktheme" ]

''''''
def delegate_function_call(generator: SlideshowGenerator, name: str, arguments: str) -> str:
    args = json.loads(arguments)

    if name == 'create_title':
        generator.create_title(args["theme"], args["title"], args["subtitle"])
    elif name == 'save':
        generator.save("cool")

    return json.dumps({"result": "Task Executed Successfully"})

gen = SlideshowGenerator()

while True:
    RESPONSE = client.chat.completions.create(
        model="slidesai",
        messages=msgs,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "create_title",
                    "description": "Creates title slide, used best as first slide of presentation or to start a seperate section",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "theme": {
                                "type": "string",
                                "enum": themes,
                                "description": "The theme of the current slide. Should be kept consistent througout the slideshow except when specifically told otherwise.",
                            },
                            "title": {
                                "type": "string",
                                "description": "Text of Title of title slide",
                            },
                            "subtitle": {
                                "type": "string",
                                "description": "Text of subtitle of title slide",
                            },
                        },
                        "required": ["title", "subtitle", "theme"],
                    },
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_content_slide",
                    "description": "Creates a title and body slide, best used to convey information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "theme": {
                                "type": "string",
                                "enum": themes,
                                "description": "The theme of the current slide. Should be kept consistent througout the slideshow except when specifically told otherwise.",
                            },
                            "title": {
                                "type": "string",
                                "description": "Text of Title of title and body slide",
                            },
                            "content": {
                                "type": "string",
                                "description": "Text of body of title and body slide",
                            },
                        },
                        "required": ["title", "content", "theme"],
                    },
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "save",
                    "description": "Completes the slideshow, and sends it to the user.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        },
                        "required": [],
                    },
                }
            }
        ]
    )

    choice = RESPONSE.choices[0]
    if choice.message.content is None:
        choice.message.content = ""
    msgs.append(choice.message)

    if choice.finish_reason == 'tool_calls':
        for call in choice.message.tool_calls:
            function_name = call.function.name
            print(call)

            content = delegate_function_call(gen, call.function.name, call.function.arguments)

            print(content)
            msgs.append(
                {
                    "tool_call_id": call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": content,
                }
            )
    elif choice.finish_reason == 'stop':
        print(choice.message.content)
        msgs.append({"role": "user", "content": input()})


