#!/usr/bin/env python
import unittest
import json
from unittest.mock import patch
from mcp_server import PuzzleMCPServer, create_mcp_server


@patch("builtins.print")
class TestMCPServer(unittest.TestCase):
    def setUp(self):
        self.server = create_mcp_server()

    def test_server_creation(self, mocked_print):
        """
        Testuje vytvoření MCP serveru a základní inicializaci.
        """
        self.assertIsNotNone(self.server)
        self.assertIsNotNone(self.server.puzzle_env)
        self.assertIsInstance(self.server._tools, dict)

    def test_get_tools(self, mocked_print):
        """
        Testuje získání seznamu dostupných nástrojů.
        """
        tools = self.server.get_tools()
        self.assertIsInstance(tools, list)
        self.assertEqual(len(tools), 4)
        
        tool_names = [tool['name'] for tool in tools]
        expected_tools = ["get_current_state", "move_across_river", "check_if_solved", "reset_puzzle"]
        
        for expected_tool in expected_tools:
            self.assertIn(expected_tool, tool_names)
        
        # Ověříme strukturu prvního nástroje
        first_tool = tools[0]
        self.assertIn('name', first_tool)
        self.assertIn('description', first_tool)
        self.assertIn('inputSchema', first_tool)

    def test_get_current_state_tool(self, mocked_print):
        """
        Testuje nástroj pro získání aktuálního stavu.
        """
        result = self.server.call_tool("get_current_state", {})
        
        self.assertIn('content', result)
        self.assertIsInstance(result['content'], list)
        self.assertEqual(len(result['content']), 1)
        self.assertEqual(result['content'][0]['type'], 'text')
        
        # Ověříme, že výsledek obsahuje očekávané informace o stavu
        text = result['content'][0]['text']
        self.assertIn('Levý břeh', text)
        self.assertIn('Pravý břeh', text)
        self.assertIn('Loďka', text)

    def test_move_across_river_success(self, mocked_print):
        """
        Testuje úspěšný přesun přes řeku.
        """
        result = self.server.call_tool("move_across_river", {"passenger": "goat"})
        
        self.assertIn('content', result)
        self.assertNotIn('isError', result)
        
        # Parsujeme JSON odpověď
        response_text = result['content'][0]['text']
        response_data = json.loads(response_text)
        
        self.assertEqual(response_data['status'], 'úspěch')
        self.assertIn('popis', response_data)
        self.assertIn('novy_stav', response_data)

    def test_move_across_river_invalid_passenger(self, mocked_print):
        """
        Testuje přesun s neplatným pasažérem.
        """
        result = self.server.call_tool("move_across_river", {"passenger": "invalid"})
        
        self.assertIn('content', result)
        self.assertTrue(result.get('isError', False))
        
        error_text = result['content'][0]['text']
        self.assertIn('Invalid passenger', error_text)

    def test_move_across_river_missing_passenger(self, mocked_print):
        """
        Testuje přesun bez zadání pasažéra.
        """
        result = self.server.call_tool("move_across_river", {})
        
        self.assertIn('content', result)
        self.assertTrue(result.get('isError', False))
        
        error_text = result['content'][0]['text']
        self.assertIn("Parameter 'passenger' is required", error_text)

    def test_check_if_solved_not_solved(self, mocked_print):
        """
        Testuje kontrolu vyřešení v nevyřešeném stavu.
        """
        result = self.server.call_tool("check_if_solved", {})
        
        self.assertIn('content', result)
        self.assertNotIn('isError', result)
        
        text = result['content'][0]['text']
        self.assertIn('Negativní', text)
        self.assertIn('není vyřešena', text)

    def test_check_if_solved_when_solved(self, mocked_print):
        """
        Testuje kontrolu vyřešení ve vyřešeném stavu.
        """
        # Nastavíme stav na vyřešený
        self.server.puzzle_env.state = {
            "left_bank": set(),
            "right_bank": {"wolf", "goat", "cabbage"},
            "boat_location": "right"
        }
        
        result = self.server.call_tool("check_if_solved", {})
        
        self.assertIn('content', result)
        self.assertNotIn('isError', result)
        
        text = result['content'][0]['text']
        self.assertIn('Potvrzeno', text)
        self.assertIn('skutečně vyřešena', text)

    def test_reset_puzzle(self, mocked_print):
        """
        Testuje resetování hádanky.
        """
        # Nejprve změníme stav
        self.server.puzzle_env.state["boat_location"] = "right"
        
        # Resetujeme
        result = self.server.call_tool("reset_puzzle", {})
        
        self.assertIn('content', result)
        self.assertNotIn('isError', result)
        
        text = result['content'][0]['text']
        self.assertIn('resetována', text)
        self.assertIn('počátečního stavu', text)
        
        # Ověříme, že stav byl skutečně resetován
        self.assertEqual(self.server.puzzle_env.state["left_bank"], {"wolf", "goat", "cabbage"})
        self.assertEqual(self.server.puzzle_env.state["right_bank"], set())
        self.assertEqual(self.server.puzzle_env.state["boat_location"], "left")

    def test_unknown_tool(self, mocked_print):
        """
        Testuje volání neexistujícího nástroje.
        """
        result = self.server.call_tool("unknown_tool", {})
        
        self.assertIn('content', result)
        self.assertTrue(result.get('isError', False))
        
        error_text = result['content'][0]['text']
        self.assertIn("Unknown tool 'unknown_tool'", error_text)

    def test_tool_schemas(self, mocked_print):
        """
        Testuje správnost schémat nástrojů.
        """
        tools = self.server.get_tools()
        
        # Najdeme nástroj move_across_river
        move_tool = None
        for tool in tools:
            if tool['name'] == 'move_across_river':
                move_tool = tool
                break
        
        self.assertIsNotNone(move_tool)
        
        # Ověříme schéma
        schema = move_tool['inputSchema']
        self.assertEqual(schema['type'], 'object')
        self.assertIn('passenger', schema['properties'])
        self.assertEqual(schema['properties']['passenger']['type'], 'string')
        self.assertIn('enum', schema['properties']['passenger'])
        self.assertEqual(
            set(schema['properties']['passenger']['enum']),
            {"wolf", "goat", "cabbage", "nothing"}
        )

    def test_multiple_moves_sequence(self, mocked_print):
        """
        Testuje sekvenci několika tahů pro ověření správné funkce.
        """
        # Tah 1: Převez kozu
        result1 = self.server.call_tool("move_across_river", {"passenger": "goat"})
        self.assertNotIn('isError', result1)
        
        # Tah 2: Vrať se sám
        result2 = self.server.call_tool("move_across_river", {"passenger": "nothing"})
        self.assertNotIn('isError', result2)
        
        # Tah 3: Převez vlka
        result3 = self.server.call_tool("move_across_river", {"passenger": "wolf"})
        self.assertNotIn('isError', result3)
        
        # Zkontroluj současný stav
        state_result = self.server.call_tool("get_current_state", {})
        state_text = state_result['content'][0]['text']
        
        # Vlk by měl být na pravé straně, koza na levé - ověříme, že se stav změnil
        self.assertIn('wolf', state_text.lower())


if __name__ == '__main__':
    unittest.main()