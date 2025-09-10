#!/usr/bin/env python
import json
from typing import Literal
import inspect
from docstring_parser import parse
from puzzle_environment import PuzzleEnvironment


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

    def check_if_solved(self):
        """
        Zkontroluje, zda byla hádanka úspěšně vyřešena.
        Tento nástroj volej, vždy když si myslíš, že je hadanka vyřešena, aby jsi si to ověřil.
        """
        print("--- Nástroj 'check_if_solved' byl zavolán. ---")

        if self.puzzle_env.is_solved():
            return "Potvrzeno. Hádanka je skutečně vyřešena. Nyní můžeš napsat finální zprávu."
        else:
            current_state = self.puzzle_env.get_state_description()
            return f"Negativní. Hádanka ještě není vyřešena. Pokračuj v práci. Aktuální stav je:\n{current_state}"


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
