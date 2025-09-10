# Claude Code Configuration

## Primary Task Assignment
Napiš Python skript, který zavolá LLM API, použije nástroj (např. výpočetní funkci) a vrátí odpověď zpět LLM.

## Project Commands

### Development
- `uv run python main.py` - Run the puzzle solver agent
- `uv run python test_agent_toolbox.py` - Run toolbox tests
- `uv run python test_puzzle_environment.py` - Run puzzle environment tests
- `uv run python test_schema_generator.py` - Run schema generator tests

### Testing
- `uv run python -m unittest discover -s . -p "test_*.py" -v` - Run all unit tests

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
- `agent_tools.py` - AgentToolbox class and tool schema generation
- `puzzle_environment.py` - PuzzleEnvironment class (Wolf, Goat, Cabbage puzzle logic)
- `test_*.py` - Unit tests for components
- `.env` - Environment variables (not committed)
- `pyproject.toml` - Project dependencies and configuration