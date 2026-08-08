"""
Orchestrateur véhicule <-> IA (API Claude).

This module :
1. Describe the tools available to Claude (set_music_state, ...)
2. Send the user message to Claude and get a response, which may include tool calls
3. Execute the requested tools and send the results back to Claude
4. send the final response from Claude back to the user

prerequisites:
    pip install python-dotenv:
    pip install anthropic
    export ANTHROPIC_API_KEY="my-secret-api-key" (Done automatically in .env file)
"""

import os                       #Let you access environment variables
import json                     #Let you handle JSON data
import anthropic                #Let you interact with the Claude API
from dotenv import load_dotenv  #Let you load environment variables from a .env file

from vehicle_controllers import set_music_state, set_music_volume, set_music_station, set_temperature_value, set_speed_value, set_lights_state, set_lights_luminosity, set_navigation_destination, set_fuel_level, get_fuel_level, get_state

# Charge automatically the environment variables from a .env file if it exists
# Must be called before using os.environ.get("ANTHROPIC_API_KEY")
load_dotenv()


# --- 1. Description of the tools for Claude ---------------------------

TOOLS = [
    {
        "name": "set_music_state",
        "description": "turn on/off the music in the vehicle.",
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "boolean",
                    "description": "true to turn the music on, false to turn it off"
                }
            },
            "required": ["state"]
        }
    },
    {
        "name": "set_music_volume",
        "description": "Set the music volume in the vehicle, between 0 and 100.",
        "input_schema": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "integer",
                    "description": "Target volume level (0 to 100)"
                }
            },
            "required": ["value"]
        }
    },
    {
        "name": "set_music_station",
        "description": "Set the music station in the vehicle (e.g., 'Radio 1', 'Radio 2', 'Spotify').",
        "input_schema": {
            "type": "object",
            "properties": {
                "station": {
                    "type": "string",
                    "description": "Target music station"
                }
            },
            "required": ["station"]
        }
    },
    {
        "name": "set_temperature_value",
        "description": "Set the target temperature in the vehicle, between 16 and 30 degrees Celsius.",
        "input_schema": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "integer",
                    "description": "Target temperature in degrees Celsius (16 to 30)"
                }
            },
            "required": ["value"]
        }
    },
    {
        "name": "set_speed_value",
        "description": "Set the target speed of the vehicle (e.g., cruise control), between 0 and 200 km/h.",
        "input_schema": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "integer",
                    "description": "Target speed in km/h (0 to 200)"
                }
            },
            "required": ["value"]
        }
    },
    {
        "name": "set_lights_state",
        "description": "Turn the vehicle's headlights on or off.",
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "boolean",
                    "description": "true to turn the headlights on, false to turn them off"
                }
            },
            "required": ["state"]
        }
    },
    {
        "name": "set_lights_luminosity",
        "description": "Set the luminosity of the vehicle's lights, between 0 and 100.",
        "input_schema": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "integer",
                    "description": "Target luminosity level (0 to 100)"
                }
            },
            "required": ["value"]
        }
    },
    {
        "name": "set_navigation_destination",
        "description": "Set the navigation destination of the vehicle.",
        "input_schema": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "Target destination for navigation"
                }
            },
            "required": ["destination"]
        }
    },
    {
        "name": "set_fuel_level",
        "description": "Set the fuel level of the vehicle, between 0 and 100%.",
        "input_schema": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "integer",
                    "description": "Target fuel level in percentage (0 to 100)"
    }
            },
            "required": ["value"]
        }
    },
    {
        "name": "get_fuel_level",
        "description": "Get the current fuel level of the vehicle.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_state",
        "description": "Return the complete current state of the vehicle (useful for debugging or display).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
]


# --- 2. Correspondance table Name -> Python Function associated -----------------

FUNCTION_MAP = {
    "set_music_state": lambda state: set_music_state(state),
    "set_music_volume": lambda value: set_music_volume(value),
    "set_music_station": lambda station: set_music_station(station),
    "set_temperature_value": lambda value: set_temperature_value(value),
    "set_speed_value": lambda value: set_speed_value(value),
    "set_lights_state": lambda state: set_lights_state(state),
    "set_lights_luminosity": lambda value: set_lights_luminosity(value),
    "set_navigation_destination": lambda destination: set_navigation_destination(destination),
    "set_fuel_level": lambda value: set_fuel_level(value),
    "get_fuel_level": lambda: get_fuel_level(),
    "get_state": lambda: get_state(),
}


def execute_tool(name: str, tool_input: dict) -> str:
    """Execute the tool corresponding to the given name with the provided input, and return the result as a string."""
    if name not in FUNCTION_MAP:
        return f"Error : unknown function '{name}'"
    try:
        return FUNCTION_MAP[name](**tool_input)
    except Exception as e:
        return f"Error during execution of '{name}': {e}"

# --- 3. Principal function of orchestration -------------------------------------
# Return the final answer from Claude after executing any requested tools.
def run_command(user_message: str, messages:str, client: anthropic.Anthropic, model: str = "claude-sonnet-4-6") -> str:

    # 'messages' is the conversation history : it is modified (.append) so it 'memorizes' the previous messages.
    messages.append({"role": "user", "content": user_message})

    while True:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=(
                "You are a vehicle assistant. You can control the vehicle using the following tools: " \
                "" + ", ".join(tool["name"] for tool in TOOLS) + ". " \
                "You have access to conversation history so use it to understand inputs like 'a bit more' or 'Put it back the way it was'. " \
                "When you want to use a tool, respond with a 'tool_use' block specifying the tool name and its input parameters in JSON format. " \
                "If you don't need to use any tools, respond with a 'text' block containing your final answer to the user."
            ),
            tools=TOOLS,
            messages=messages,
        )
        """ Note : The conversation history becoming bigger and bigger, it may be necessary to limit its size in the future because each API call will cost more and more tokens.
        For the future : limit the number of messages in the conversation history to the last N messages, or limit the total number of tokens in the conversation history.
        """
        # If Claude's response does not contain any tool_use blocks, return the text content as the final answer
        if response.stop_reason != "tool_use":
            return "".join(block.text for block in response.content if block.type == "text")

        # Else, if Claude's response contains tool_use blocks, execute the requested tools and send the results back to Claude
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })

        messages.append({"role": "user", "content": tool_results})


# --- 4. Testing entry point ---------------------------------

if __name__ == "__main__":
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  environment variable ANTHROPIC_API_KEY not set. Please set it to your Claude API key.")
        exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    conversation_history = [] # Store the conversation history between the user and Claude while the program is running

    print("Orchestrtor ready. Write 'quit' or 'exit' to exit. Write 'reset' to forget conversation history\n")
    while True:
        user_input = input("User input : ")
        if user_input.lower() in ("quit", "exit"):
            break
        if user_input.lower() == "reset":
            conversation_history = []
            print("Conversation history reset.")
            continue
        reply = run_command(user_input, conversation_history, client)
        print(f"Vehicle > {reply}\n")