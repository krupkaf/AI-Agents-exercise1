#!/usr/bin/env python
import unittest
from typing import Literal
from agent_tools import generate_tool_schema


class TestGenerateToolSchema(unittest.TestCase):
    def test_function_with_no_parameters(self):
        """
        Testuje generování schématu pro funkci bez parametrů.
        """

        def dummy_no_params():
            """Toto je krátký popis."""
            pass

        expected_schema = {
            "type": "function",
            "function": {
                "name": "dummy_no_params",
                "description": "Toto je krátký popis.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }

        generated_schema = generate_tool_schema(dummy_no_params)
        self.assertDictEqual(generated_schema, expected_schema)

    def test_function_with_required_parameters(self):
        """
        Testuje generování schématu pro funkci s povinnými parametry.
        """

        def dummy_with_params(name: str, count: int):
            """
            Popis funkce s parametry.

            :param name: Jméno uživatele.
            :param count: Počet položek.
            """
            pass

        expected_schema = {
            "type": "function",
            "function": {
                "name": "dummy_with_params",
                "description": "Popis funkce s parametry.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Jméno uživatele."},
                        "count": {"type": "integer", "description": "Počet položek."},
                    },
                    "required": ["name", "count"],
                },
            },
        }

        generated_schema = generate_tool_schema(dummy_with_params)
        self.assertDictEqual(generated_schema, expected_schema)

    def test_function_with_literal_enum(self):
        """
        Testuje správné zpracování typu Literal na pole enum.
        """

        def dummy_with_literal(passenger: Literal["wolf", "goat", "cabbage"]):
            """
            Funkce s omezeným výběrem.

            :param passenger: Pasažér k převozu.
            """
            pass

        expected_schema = {
            "type": "function",
            "function": {
                "name": "dummy_with_literal",
                "description": "Funkce s omezeným výběrem.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "passenger": {
                            "type": "string",
                            "description": "Pasažér k převozu.",
                            "enum": ["wolf", "goat", "cabbage"],
                        }
                    },
                    "required": ["passenger"],
                },
            },
        }

        generated_schema = generate_tool_schema(dummy_with_literal)
        self.assertDictEqual(generated_schema, expected_schema)


if __name__ == "__main__":
    unittest.main()
