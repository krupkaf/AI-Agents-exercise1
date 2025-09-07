#!/usr/bin/env python
import unittest
import json
import copy
from unittest.mock import patch
from main import PuzzleEnvironment, AgentToolbox


@patch("builtins.print")
class TestAgentToolbox(unittest.TestCase):
    def setUp(self):
        self.env = PuzzleEnvironment()
        self.toolbox = AgentToolbox(self.env)

    def test_get_current_state(self, mocked_print):
        """
        Testuje, zda nástroj pro zjištění stavu vrací správný formát.
        """

        expected_description = self.env.get_state_description()
        tool_description = self.toolbox.get_current_state()
        self.assertEqual(
            tool_description,
            expected_description,
            "Nástroj get_current_state by měl vracet přesně to, co PuzzleEnvironment.get_state_description.",
        )

    def test_successful_move(self, mocked_print):
        """
        Testuje úspěšný a platný přesun.
        """

        result_json = self.toolbox.move_across_river(passenger="goat")
        result_data = json.loads(result_json)

        self.assertEqual(
            result_data["status"],
            "úspěch",
            "Status by měl být 'úspěch' při platném tahu.",
        )
        self.assertIn(
            "goat", self.env.state["right_bank"], "Koza by měla být na pravém břehu."
        )
        self.assertNotIn(
            "goat", self.env.state["left_bank"], "Koza by neměla být na levém břehu."
        )
        self.assertEqual(
            self.env.state["boat_location"],
            "right",
            "Loďka by měla být na pravém břehu.",
        )

    def test_invalid_move_due_to_rules(self, mocked_print):
        """
        Testuje neúspěšný tah, který porušuje pravidla hry.
        """

        initial_state = copy.deepcopy(self.env.state)

        # Pokus o přesun vlka, což by zanechalo kozu se zelím
        result_json = self.toolbox.move_across_river(passenger="wolf")
        result_data = json.loads(result_json)

        self.assertEqual(
            result_data["status"],
            "chyba",
            "Status by měl být 'chyba' při neplatném tahu.",
        )
        self.assertIn(
            "neplatný",
            result_data["duvod"],
            "Důvod chyby by měl zmiňovat neplatnost tahu.",
        )

        self.assertEqual(
            self.env.state,
            initial_state,
            "Stav prostředí by se po neplatném tahu neměl měnit.",
        )

    def test_invalid_move_due_to_location(self, mocked_print):
        """
        Testuje logisticky nemožný tah (pasažér je na špatném břehu).
        """

        # Nejprve provedeme platný tah, abychom dostali loďku na druhý břeh
        self.toolbox.move_across_river(passenger="goat")

        intermediate_state = copy.deepcopy(self.env.state)
        self.assertEqual(
            self.env.state["boat_location"],
            "right",
            "Předpoklad: Loďka je na pravém břehu.",
        )
        self.assertIn(
            "wolf",
            self.env.state["left_bank"],
            "Předpoklad: Vlk je stále na levém břehu.",
        )

        # Nyní se pokusíme z pravého břehu sebrat vlka, který je na levém
        result_json = self.toolbox.move_across_river(passenger="wolf")
        result_data = json.loads(result_json)

        self.assertEqual(
            result_data["status"],
            "chyba",
            "Status by měl být 'chyba' při logisticky nemožném tahu.",
        )
        self.assertIn(
            "není na stejném břehu",
            result_data["duvod"],
            "Důvod chyby by měl zmiňovat špatný břeh.",
        )

        self.assertEqual(
            self.env.state,
            intermediate_state,
            "Stav prostředí by se po logisticky nemožném tahu neměl měnit.",
        )

    def test_check_if_solved_when_not_solved(self, mocked_print):
        """
        Testuje nástroj check_if_solved ve výchozím (nevyřešeném) stavu.
        """
        # Akce: Zavoláme nástroj
        result_string = self.toolbox.check_if_solved()

        # Ověření: Zkontrolujeme, zda odpověď obsahuje negativní zprávu
        self.assertIn("Negativní", result_string)
        self.assertIn("není vyřešena", result_string)
        # Ověříme, že odpověď obsahuje i aktuální stav pro pomoc agentovi
        self.assertIn("Levý břeh:", result_string)

    def test_check_if_solved_when_solved(self, mocked_print):
        """
        Testuje nástroj check_if_solved, když je hádanka ve vyřešeném stavu.
        """
        # Příprava: Manuálně nastavíme prostředí do vyřešeného stavu
        self.env.state = {
            "left_bank": set(),
            "right_bank": {"wolf", "goat", "cabbage"},
            "boat_location": "right"
        }

        # Akce: Zavoláme nástroj
        result_string = self.toolbox.check_if_solved()

        # Ověření: Zkontrolujeme, zda odpověď obsahuje potvrzující zprávu
        self.assertIn("Potvrzeno", result_string)
        self.assertIn("je skutečně vyřešena", result_string)


if __name__ == "__main__":
    unittest.main()
