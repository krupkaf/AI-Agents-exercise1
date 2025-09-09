# Claude Code Configuration

## Primary Task Assignment
Napiš Python skript, který zavolá LLM API, použije nástroj (např. výpočetní funkci) a vrátí odpověď zpět LLM.

## Project Commands

### Development
- `python main.py` - Run the puzzle solver agent
- `python test_agent_toolbox.py` - Run toolbox tests
- `python test_puzzle_environment.py` - Run puzzle environment tests
- `python test_schema_generator.py` - Run schema generator tests

### Linting and Type Checking
- `ruff check .` - Run linting
- `ruff format .` - Format code

## Environment Setup
- Copy `.env.example` to `.env`
- Set `OPENROUTER_API_KEY` with your API key
- Configure `MODEL` (default: "openrouter/openai/gpt-4-turbo")
- Set `MAX_STEP` for maximum solver iterations (default: 15)

## Project Structure
- `main.py` - Main puzzle solver with LLM integration
- `test_*.py` - Unit tests for components
- `.env` - Environment variables (not committed)
- `pyproject.toml` - Project dependencies and configuration