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
        "NEMÁŠ vlastní znalosti o světě hádanky. Jediný způsob, jak můžeš interagovat se světem nebo zjišťovat jeho stav, je prostřednictvím poskytnutých nástrojů."
        "NESMÍŠ odpovídat přímo uživateli, dokud není úkol kompletně splněn."
        "VŽDY MUSÍŠ použít nástroj v každém kroku, dokud nedosáhneš finálního stavu."
        "DŮSLEDNĚ DODRŽUJ TENTO POSTUP MYŠLENÍ:"
        "1. Pokud si nejsi jist s aktuálním stavem, nejprve si zjisti aktuální stav pomocí nástroje `get_current_state`."
        "2. Na základě stavu, a hlavně polohy loďky, zvaž všechny možné platné tahy a proveď přesun pomocí `move_across_river`."
        "3. Pamatuj, že převozník se může vrátit i sám! Tah 'move_across_river' s pasažérem 'nothing' je často klíčový."
        "4. Vyber nejlepší tah a proveď ho."
        "5. Opakuj, dokud nejsou všechny položky na pravém břehu."
        "6. Pokud nástroj vrátí chybu, pečlivě si přečti její důvod a naplánuj nový, správný tah. Neopakuj chyby."
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
