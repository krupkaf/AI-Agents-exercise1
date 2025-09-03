#!/usr/bin/env python
import os
from litellm import completion
from dotenv import load_dotenv
import json
from typing import Literal
import inspect
from docstring_parser import parse
import copy


class PuzzleEnvironment:
    """
    Zapouzdřuje stav a pravidla hádanky Vlk, koza, zelí.
    """

    def __init__(self):
        self.state = {
            "left_bank": {"wolf", "goat", "cabbage"},
            "right_bank": set(),
            "boat_location": "left",
        }

    def get_state_description(self):
        """
        Vrátí lidsky čitelný popis aktuálního stavu.
        """
        left = ", ".join(sorted(list(self.state["left_bank"]))) or "prázdný"
        right = ", ".join(sorted(list(self.state["right_bank"]))) or "prázdný"
        boat = "levém" if self.state["boat_location"] == "left" else "pravém"
        return (
            f"Levý břeh: [{left}].\n"
            f"Pravý břeh: [{right}].\n"
            f"Loďka s převozníkem je na {boat} břehu."
        )

    def is_valid_state(self, state_to_check):
        """
        Zkontroluje, zda daný stav neporušuje pravidla.
        Vrací True, pokud je stav v pořádku.
        """
        # Zkontrolujeme levý břeh, POKUD je loďka na pravém
        if state_to_check["boat_location"] == "right":
            if (
                "wolf" in state_to_check["left_bank"]
                and "goat" in state_to_check["left_bank"]
            ):
                return False
            if (
                "goat" in state_to_check["left_bank"]
                and "cabbage" in state_to_check["left_bank"]
            ):
                return False

        # Zkontrolujeme pravý břeh, POKUD je loďka na levém
        if state_to_check["boat_location"] == "left":
            if (
                "wolf" in state_to_check["right_bank"]
                and "goat" in state_to_check["right_bank"]
            ):
                return False
            if (
                "goat" in state_to_check["right_bank"]
                and "cabbage" in state_to_check["right_bank"]
            ):
                return False

        # Pokud žádné pravidlo nebylo porušeno
        return True

    def attempt_move(self, passenger: str):
        """
        Pokusí se provést tah. Obsahuje veškerou logiku a validaci.
        Pokud je tah platný, změní vnitřní stav.
        Vrací: (bool: úspěch, str: zpráva)
        """
        current_location_key = self.state["boat_location"] + "_bank"

        # 1. Logistická kontrola
        if passenger != "nothing" and passenger not in self.state[current_location_key]:
            return (False, f"Pasažér '{passenger}' není na stejném břehu jako loďka.")

        # 2. Simulace tahu
        potential_state = copy.deepcopy(self.state)
        target_location_key = (
            "right_bank" if self.state["boat_location"] == "left" else "left_bank"
        )
        potential_state["boat_location"] = (
            "right" if self.state["boat_location"] == "left" else "left"
        )
        if passenger != "nothing":
            potential_state[current_location_key].remove(passenger)
            potential_state[target_location_key].add(passenger)

        # 3. Validace pravidel
        if self.is_valid_state(potential_state):
            # 4. Pokud je vše OK, POTVRDÍME změnu stavu
            self.state = potential_state
            return (True, f"Převozník úspěšně převezl '{passenger}'.")
        else:
            return (
                False,
                "Tento tah je neplatný, protože by vedl k porušení pravidel. Zkus jiný tah.",
            )

    def is_solved(self):
        return len(self.state["left_bank"]) == 0 and len(self.state["right_bank"]) == 3


class AgentToolbox:
    """
    Obsahuje sadu nástrojů, které může AI agent používat k interakci se světem.
    """

    def __init__(self, puzzle_env: PuzzleEnvironment):
        self.puzzle_env = puzzle_env

    def get_current_state(self):
        """
        Získá aktuální stav hádanky – kdo je na kterém břehu a kde je loďka.
        """
        print("--- Nástroj 'get_current_state' byl zavolán. ---")
        return self.puzzle_env.get_state_description()

    def move_across_river(
        self, passenger: Literal["wolf", "goat", "cabbage", "nothing"]
    ):
        """
        Pokusí se převézt pasažéra na druhý břeh.

        :param passenger: Koho převézt. Možnosti jsou 'wolf', 'goat', 'cabbage' nebo 'nothing' (převozník jede sám).
        """
        print(
            f"--- Nástroj 'move_across_river' byl zavolán s pasažérem: '{passenger}' ---"
        )
        passenger = passenger.lower()

        success, message = self.puzzle_env.attempt_move(passenger)

        if success:
            response = {
                "status": "úspěch",
                "popis": message,
                "novy_stav": self.puzzle_env.get_state_description(),
            }
        else:
            response = {"status": "chyba", "duvod": message}

        return json.dumps(response, ensure_ascii=False)


def generate_tool_schema(func):
    """
    Generuje OpenAI JSON schéma pro danou funkci pomocí introspekce.
    """
    # Získáme podpis funkce (parametry, anotace)
    signature = inspect.signature(func)
    # Zparsujeme docstring pro získání popisů
    docstring = parse(func.__doc__)

    # Mapa Python typů na JSON Schema typy
    type_mapping = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
    }

    properties = {}
    required = []

    for param in signature.parameters.values():
        param_name = param.name
        param_type_name = (
            param.annotation.__name__
            if hasattr(param.annotation, "__name__")
            else str(param.annotation)
        )

        schema_type = type_mapping.get(param_type_name, "string")

        # Najdeme popis parametru v docstringu
        param_doc = next(
            (d for d in docstring.params if d.arg_name == param_name), None
        )
        description = param_doc.description if param_doc else ""

        properties[param_name] = {
            "type": schema_type, "description": description}

        # Zpracování typu Literal pro vytvoření 'enum'
        if "Literal" in str(param.annotation):
            # Získáme hodnoty z Literal['a', 'b', ...]
            properties[param_name]["enum"] = list(param.annotation.__args__)

        # Pokud parametr nemá výchozí hodnotu, je povinný
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    tool_schema = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": docstring.short_description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }
    return tool_schema


if __name__ == "__main__":
    load_dotenv()

    MODEL = (
        os.environ.get("MODEL")
        if os.environ.get("MODEL") is not None
        else "openrouter/openai/gpt-4-turbo"
    )

    system_prompt = (
        "Jsi expert na logické hádanky. Tvým úkolem je vyřešit hádanku 'Vlk, koza a zelí' krok za krokem."
        "Cílem je dostat vlka, kozu a zelí na pravý břeh."
        "DŮSLEDNĚ DODRŽUJ TENTO POSTUP MYŠLENÍ:"
        "1. Pokud si nejsi jist s aktuálním stavem, nejprve si zjisti aktuální stav pomocí nástroje `get_current_state`."
        "2. Na základě stavu, a hlavně polohy loďky, zvaž všechny možné platné tahy."
        "3. Pamatuj, že převozník se může vrátit i sám! Tah 'move_across_river' s pasažérem 'nothing' je často klíčový."
        "4. Vyber nejlepší tah a proveď ho."
        "5. Pokud nástroj vrátí chybu, pečlivě si přečti její důvod a naplánuj nový, správný tah. Neopakuj chyby."
    )

    puzzle_env = PuzzleEnvironment()
    toolbox = AgentToolbox(puzzle_env)

    tools_to_register = [toolbox.get_current_state, toolbox.move_across_river]
    tools_schemas = [generate_tool_schema(func) for func in tools_to_register]

    available_tools = {func.__name__: func for func in tools_to_register}

    messages = [{"role": "system", "content": system_prompt}]

    print(f"\nMODEL: {MODEL}\n")

    print("--- START ŘEŠENÍ HÁDANKY ---")
    print(f"Počáteční stav:\n{puzzle_env.get_state_description()}\n")

    max_steps = 15
    for step in range(1, max_steps + 1):
        print(f"--- KROK {step} ---")

        response = completion(
            model=MODEL,
            messages=messages,
            tools=tools_schemas,
            tool_choice="auto",
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_tools[function_name]
                function_args = json.loads(tool_call.function.arguments)

                print(
                    f"Agent navrhuje akci: {function_name} s argumenty {function_args}"
                )

                function_response = function_to_call(**function_args)

                print(f"Výsledek nástroje: {function_response}\n")

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
        else:
            print(f"Agent říká: {response_message.content}\n")

        if puzzle_env.is_solved():
            print("🎉 HÁDANKA ÚSPĚŠNĚ VYŘEŠENA! 🎉")
            print(f"Finální stav:\n{puzzle_env.get_state_description()}")
            break
    else:
        print("Agentovi se nepodařilo vyřešit hádanku v daném počtu kroků.")
