#!/usr/bin/env python
import unittest
from puzzle_environment import PuzzleEnvironment


class TestPuzzleEnvironment(unittest.TestCase):
    def setUp(self):
        self.env = PuzzleEnvironment()

    def test_initial_state(self):
        """
        Testuje, zda je počáteční stav správně nastaven.
        """
        self.assertEqual(
            self.env.state["left_bank"],
            {"wolf", "goat", "cabbage"},
            "Na levém břehu mají být na začátku všichni.",
        )
        self.assertEqual(
            self.env.state["right_bank"], set(), "Pravý břeh má být na začátku prázdný."
        )
        self.assertEqual(
            self.env.state["boat_location"], "left", "Loďka má začínat na levém břehu."
        )

    def test_is_solved(self):
        """
        Testuje logiku pro rozpoznání vyřešené hádanky.
        """
        # 1. Počáteční stav není vyřešený
        self.assertFalse(
            self.env.is_solved(),
            "Počáteční stav by neměl být vyhodnocen jako vyřešený.",
        )

        # 2. Mezistav není vyřešený
        self.env.state = {
            "left_bank": {"wolf"},
            "right_bank": {"goat", "cabbage"},
            "boat_location": "right",
        }
        self.assertFalse(
            self.env.is_solved(), "Mezistav by neměl být vyhodnocen jako vyřešený."
        )

        # 3. Finální stav JE vyřešený
        self.env.state = {
            "left_bank": set(),
            "right_bank": {"wolf", "goat", "cabbage"},
            "boat_location": "right",
        }
        self.assertTrue(
            self.env.is_solved(), "Finální stav by MĚL být vyhodnocen jako vyřešený."
        )

    def test_is_valid_state_valid_scenarios(self):
        """
        Testuje scénáře, které JSOU podle pravidel platné.
        """

        # 1. Počáteční stav je platný
        self.assertTrue(
            self.env.is_valid_state(self.env.state), "Počáteční stav by měl být platný."
        )

        # 2. Vlk a zelí mohou být sami spolu
        state = {
            "left_bank": {"wolf", "cabbage"},
            "right_bank": {"goat"},
            "boat_location": "right",  # Převozník je s kozou
        }
        self.assertTrue(
            self.env.is_valid_state(state),
            "Vlk a zelí mohou být sami spolu bez dozoru.",
        )

        # 3. Vyřešený stav je platný
        state = {
            "left_bank": set(),
            "right_bank": {"wolf", "goat", "cabbage"},
            "boat_location": "right",  # Převozník je u nich
        }
        self.assertTrue(
            self.env.is_valid_state(state), "Vyřešený stav by měl být platný."
        )

    def test_is_valid_state_invalid_scenarios(self):
        """
        Testuje scénáře, které porušují pravidla a jsou NEPLATNÉ.
        """

        # Scénář 1: Vlk a koza sami na levém břehu
        with self.subTest(msg="Vlk a koza na levém břehu"):
            state = {
                "left_bank": {"wolf", "goat"},
                "right_bank": {"cabbage"},
                "boat_location": "right",  # Převozník odjel
            }
            self.assertFalse(
                self.env.is_valid_state(state), "Vlk nesmí být sám s kozou."
            )

        # Scénář 2: Vlk a koza sami na pravém břehu
        with self.subTest(msg="Vlk a koza na pravém břehu"):
            state = {
                "left_bank": {"cabbage"},
                "right_bank": {"wolf", "goat"},
                "boat_location": "left",  # Převozník odjel
            }
            self.assertFalse(
                self.env.is_valid_state(state), "Vlk nesmí být sám s kozou."
            )

        # Scénář 3: Koza a zelí sami na levém břehu
        with self.subTest(msg="Koza a zelí na levém břehu"):
            state = {
                "left_bank": {"goat", "cabbage"},
                "right_bank": {"wolf"},
                "boat_location": "right",  # Převozník odjel
            }
            self.assertFalse(
                self.env.is_valid_state(state), "Koza nesmí být sama se zelím."
            )

        # Scénář 4: Koza a zelí sami na pravém břehu
        with self.subTest(msg="Koza a zelí na pravém břehu"):
            state = {
                "left_bank": {"wolf"},
                "right_bank": {"goat", "cabbage"},
                "boat_location": "left",  # Převozník odjel
            }
            self.assertFalse(
                self.env.is_valid_state(state), "Koza nesmí být sama se zelím."
            )

    def test_get_state_description(self):
        """
        Testuje formátování textového popisu stavu.
        """

        # 1. Popis počátečního stavu
        initial_desc = self.env.get_state_description()
        self.assertIn("Levý břeh: [cabbage, goat, wolf]", initial_desc)
        self.assertIn("Pravý břeh: [prázdný]", initial_desc)
        self.assertIn("Loďka s převozníkem je na levém břehu", initial_desc)

        # 2. Popis finálního stavu
        self.env.state = {
            "left_bank": set(),
            "right_bank": {"wolf", "goat", "cabbage"},
            "boat_location": "right",
        }
        final_desc = self.env.get_state_description()
        self.assertIn("Levý břeh: [prázdný]", final_desc)
        self.assertIn("Pravý břeh: [cabbage, goat, wolf]", final_desc)
        self.assertIn("Loďka s převozníkem je na pravém břehu", final_desc)

    def test_attempt_move(self):
        """
        Testuje novou metodu pro provádění tahů.
        """

        # Úspěšný tah
        success, message = self.env.attempt_move("goat")
        self.assertTrue(success)
        self.assertIn("goat", self.env.state["right_bank"])

        # Neplatný tah - pravidla
        # Vrátíme loďku pro další test
        self.env.state["boat_location"] = "left"
        self.env.state["left_bank"].add("goat")
        self.env.state["right_bank"].remove("goat")

        success, message = self.env.attempt_move("wolf")
        self.assertFalse(success)
        self.assertIn("neplatný", message)

        # Neplatný tah - logistika
        self.env.state["boat_location"] = "right"  # Přesuneme loďku
        success, message = self.env.attempt_move("wolf")
        self.assertFalse(success)
        self.assertIn("není na stejném břehu", message)


if __name__ == "__main__":
    unittest.main()
