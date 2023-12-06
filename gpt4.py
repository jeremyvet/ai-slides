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

class Theme:
    def __init__(self, description, name) -> None:
        self.dec

SYSTEM_PROMPT = f"""You are a slideshow making assistant. The user will prompt you with an initial request.
                Your goal is to create a slideshow based on the users request.
                Your goal in this step is to walk the user through their request, you will suggest ideas for slides and ask the user to confirm.
                When making a slideshow always follow these steps before creating any slideshow elements:
                1. Start with a title slide unless told otherwise
                2. Use the available slide types to form a slideshow. Suggest the current slideshow form to the user
                3. If the user accepts this slideshow form, ask the user if they want to save the slideshow. If the user rejects this slideshow form, suggest another slideshow form.
                4. If the user accepts, save the slideshow and stop suggesting slides. If the user rejects, keep suggesting slides.
                """

themes = [ "blanktheme", "mellow_yellow", "starlight", "cavern", "forest_path" ]

tools = [
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
    {        "type": "function",

        "function": {
            "name": "create_content_slide",
            "description": "Creates a content slide. Each content slide has a title and a body, the title defines the main idea of the slide and the body goes into detail about the main idea of the slide. Use this slide for explaining proccesses or topics. When using this slide, make your responses detailed and specific, use 5-6 sentences.",
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
                        "description": "The title of this slide",
                    },
                    "content": {
                        "type": "string",
                        "description": "Provide a large and detialed paragraph description. This text is medium sized so a medium sized paragraph, which is about 5-6 sentences, should suffice",
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


''''''
def delegate_function_call(generator: SlideshowGenerator, name: str, arguments: str) -> str:
    args = json.loads(arguments)

    if name == 'create_title':
        generator.create_title(args["theme"], args["title"], args["subtitle"])
    elif name == 'create_content_slide':
        generator.create_content_slide(args["theme"], args["title"], args["content"])
    elif name == 'save':
        try:
            generator.save()
        except:
            return json.dumps({"result": "Save failed. Please try again!"})

    return json.dumps({"result": "Task Executed Successfully"})

gen = SlideshowGenerator()

if __name__ == "__main__":

    msgs = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": input()},
    ]

    while True:
        RESPONSE = client.chat.completions.create(
            model="slidesai",
            messages=msgs,
            tools=tools
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


