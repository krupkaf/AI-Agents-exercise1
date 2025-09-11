#!/usr/bin/env python
import os
from litellm import completion
from dotenv import load_dotenv
import json
from puzzle_environment import PuzzleEnvironment
from agent_tools import AgentToolbox, generate_tool_schema


if __name__ == "__main__":
    load_dotenv()

    MODEL = (
        os.environ.get("MODEL")
        if os.environ.get("MODEL") is not None
        else "openrouter/openai/gpt-4-turbo"
    )

    MAX_STEP = (
        int(os.environ.get("MAX_STEP"))
        if os.environ.get("MAX_STEP") is not None
        else 15
    )

    system_prompt = (
        "Jsi expert na logické hádanky. Tvým úkolem je vyřešit hádanku 'Vlk, koza a zelí' krok za krokem."
        "Cílem je dostat vlka, kozu a zelí na pravý břeh."
        "🚫 ABSOLUTNÍ ZÁKAZY:\n"
        "- ZAKÁZÁNO: Ukončovat práci textovou odpovědí bez volání nástroje!\n"
        "- ZAKÁZÁNO: Odpovídat uživateli přímo!\n"
        "- ZAKÁZÁNO: Ukončovat práci bez 100% potvrzení vyřešení!\n\n"
        "✅ POVINNÉ CHOVÁNÍ:\n"
        "- V KAŽDÉM kroku MUSÍŠ zavolat nástroj\n"
        "- NIKDY nesmíš vrátit pouze textovou odpověď\n"
        "- Pokud si nejsi jist co dělat, zavolej `get_current_state`\n"
        "- Pokud chceš ukončit práci, MUSÍŠ nejprve zavolat `check_if_solved`\n"
        "📋 ALGORITMUS ŘEŠENÍ:\n"
        "1. Zavolej `get_current_state` pro zjištění aktuálního stavu\n"
        "2. Analyzuj stav a polohu loďky\n"
        "3. Zavolaj `move_across_river` s vybraným pasažérem (wolf/goat/cabbage/nothing)\n"
        "4. Opakuj kroky 1-3, dokud nejsou všichni na pravém břehu\n"
        "5. Když si myslíš, že je hotovo, zavolaj `check_if_solved`\n"
        "6. Pouze pokud `check_if_solved` potvrdí úspěch, teprve pak můžeš ukončit\n\n"
        "⚠️ REAKCE NA CHYBY:\n"
        "- Chyba při `move_across_river`? Zkus jiného pasažéra!\n"
        "- Nejsi si jist? Zavolej `get_current_state`!\n"
        "- NIKDY se nevzdávej a VŽDY pokračuj voláním nástrojů!\n\n"
        "💡 KLÍČOVÉ POZNATKY:\n"
        "- Převozník může jet i sám (passenger='nothing')\n"
        "- Někdy musíš vzít někoho zpět na levý břeh\n"
        "- Vlk a koza nesmí být sami, koza a zelí nesmí být sami\n"
    )

    puzzle_env = PuzzleEnvironment()
    toolbox = AgentToolbox(puzzle_env)

    tools_to_register = [toolbox.get_current_state,
                         toolbox.move_across_river, toolbox.check_if_solved]
    tools_schemas = [generate_tool_schema(func) for func in tools_to_register]

    available_tools = {func.__name__: func for func in tools_to_register}

    messages = [{"role": "system", "content": system_prompt}]

    print(f"\nMODEL: {MODEL}\n")

    print("--- START ŘEŠENÍ HÁDANKY ---")
    print(f"Počáteční stav:\n{puzzle_env.get_state_description()}\n")

    for step in range(1, MAX_STEP + 1):
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
            print(f"Agent ukončil práci a říká: {response_message.content}\n")
            # Tímto práce agenta končí - již vratil finalní odpověd.
            if puzzle_env.is_solved():
                print("🎉 OVĚŘENO: Agent hádanku skutečně vyřešil!")
            else:
                print(
                    "❌ CHYBA: Agent si myslel, že hádanku vyřešil (nebo se zasekl), ale neudělal to.")
                print(
                    f"Skutečný finální stav:\n{puzzle_env.get_state_description()}")
            break
    else:
        # Tento blok se spustí, pokud smyčka doběhla do konce bez 'break'
        print("❌ CHYBA: Agentovi se nepodařilo dokončit úkol v daném počtu kroků (nikdy nepřestal volat nástroje).")
