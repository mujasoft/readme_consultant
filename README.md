# readme_consultant

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![LLM Powered](https://img.shields.io/badge/LLM-Ollama%20%2B%20Typer-informational)](https://ollama.ai)

`readme_consultant` is a CLI tool that uses local LLMs to **analyze, improve, and rewrite your GitHub README.md files** with professional tone, open-source best practices, and formatting polish.

---

## Features

- Reviews your `README.md` and gives structured feedback
- Uses `Ollama` to run local LLMs like `llama3` (no cloud API required)
- Enhances your README and returns a fully rewritten version
- Extracts `folder tree`, `git config`, and metadata automatically
- Outputs a structured change summary in both CLI and JSON
- Pretty CLI panels with `rich` and flexible `Typer` CLI options

---

## Installation

```bash
# clone the repo
git clone https://github.com/mujasoft/readme_consultant.git
cd readme_consultant

# install dependencies
pip install -r requirements.txt
```

> ✅ Requires: Python 3.9+, `ollama` running locally, and models like `llama3` downloaded.

---

## Usage

### 🔍 Review Mode

Get AI feedback on your current README:

```bash
python readme_consultant.py review -r /path/to/your/repo -o output.txt
```

### 💡 Enhanced README Generation

Generate a rewritten, improved `README.md`:

```bash
python readme_consultant.py generate-enhanced-readme -r /path/to/your/repo -o output_readme.md
```

---

## How It Works

- Parses your GitHub folder tree and `.git/config`
- Feeds the README and metadata to a local LLM (via `ollama`)
- Asks for improvements in clarity, structure, and professionalism
- Displays a rich summary of changes and writes output to file

---

## 🛠 Dependencies

- [Typer](https://typer.tiangolo.com/)
- [Rich](https://github.com/Textualize/rich)
- [Ollama](https://ollama.ai/)
- Python stdlib: `os`, `json`, `re`, `configparser`, etc.

---

## Example Output

```text
╭── Changes Made for "memory_pool_simulator" ──╮
│ • Improved formatting for section headers    │
│ • Rewrote project overview with more clarity │
│ • Added demo screenshot to Features section  │
╰──── LLM Powered Improvements by "llama3" ────╯

```

> And saves an improved `README.md` to your `--output` path.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Want to Help?

Pull requests, feedback, and stars welcome!
Or use it in your own GitHub projects and generate better READMEs with zero effort ✨
