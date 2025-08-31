# AI Agent Praktické cvičení - Lekce 1 - Řešitel hádanky (Vlk, Koza, Zelí)

Tento projekt je praktickým cvičením, které demonstruje schopnosti AI agenta řešit klasickou logickou hádanku: "Vlk, koza a zelí".

Cílem není jen najít řešení, ale ukázat, jak může velký jazykový model (LLM) interagovat se sadou námi definovaných nástrojů (`tools`), aby prozkoumal stavový prostor problému, dodržoval pravidla a postupně dospěl k cíli.

## Jak to funguje

Architektura projektu je založena na oddělení odpovědností:

1.  **AI Agent (LLM - mozek operace):**
    *   Jeho úkolem je **plánovat a navrhovat** další kroky.
    *   Na základě aktuálního stavu hádanky se rozhoduje, jaký tah provést.
    *   Nezná pravidla explicitně, ale učí se je skrze interakci s nástroji.

2.  **Python Skript (Prostředí a Nástroje - svět hádanky):**
    *   Definuje "svět" hádanky: kdo je na kterém břehu, kde je loďka.
    *   Drží veškerý stav v paměti (nevyužívá databázi).
    *   Poskytuje agentovi **klíčové nástroje**, pomocí kterých může svět ovlivňovat a zjišťovat jeho stav.
    *   Funguje jako **rozhodčí** – ověřuje, zda navržený tah neporušuje pravidla.

### Interakční smyčka

Agent řeší hádanku v cyklu:
1.  **Zjistí stav:** Zavolá nástroj `get_current_state()`.
2.  **Navrhne tah:** Na základě stavu se rozhodne, koho nebo co převeze.
3.  **Provede tah:** Zavolá nástroj `move_across_river()` s vybraným pasažérem.
4.  **Získá zpětnou vazbu:** Nástroj vrátí buď úspěch a nový stav, nebo chybu s vysvětlením, proč tah není možný.
5.  **Opakuje:** Agent pokračuje, dokud není hádanka vyřešena.
