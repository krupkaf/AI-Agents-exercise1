#!/usr/bin/env python
"""
Puzzle Environment - Wolf, Goat, Cabbage puzzle implementation
"""
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