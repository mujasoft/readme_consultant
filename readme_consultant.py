# MIT License

# Copyright (c) 2025 Mujaheed Khan

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import configparser
import json
import os
import re
import sys
from pathlib import Path

import requests
import typer

import ollama

from rich import print
from rich.console import Console
from rich.panel import Panel


app = typer.Typer(
    help="AI powered tool to review and enhance READMEs for better"
         " communication."
)

console = Console()


def get_readme_contents(repo_dir):
    """Returns contents of a README.md or None otherwise.

    Args:
        repo_dir (str): path to repo.

    Returns:
        str: a large text block containing output from README.md.
    """

    return read_text(os.path.join(repo_dir, "README.md"))


def get_owner_and_repo_from_git_config(repo_dir):
    """Returns 'owner' and 'repo_name' from git repo directory

    Args:
        repo_dir (str): location of repo.

    Returns:
        owner(str): name of owner. 'None' if not found.
        repo(str): name of repo. 'None' if not found.
    """

    config_path = os.path.join(repo_dir, ".git", "config")
    if not os.path.exists(config_path):
        print(f"*** ERROR: File not found: {config_path}")
        return None, None

    config = configparser.ConfigParser()
    config.read(config_path)

    try:
        url = config['remote "origin"']['url']
    except KeyError:
        print("Could not find 'origin' remote in git config.")
        return None, None

    # Match both HTTPS and SSH GitHub URLs
    match = re.match(r"(?:https://github\.com/|git@github\.com:)([^/]+)/([^.]+)(\.git)?", url)
    if match:
        owner, repo = match.group(1), match.group(2)
        return owner, repo
    else:
        print("Could not parse GitHub owner/repo from URL.")
        return None, None


def get_latest_release_tag_using_internal(owner: str, repo: str) -> str:
    """Get the latest tag using github api.

    Args:
        owner (str): Name of owner.
        repo (str): Name of repo.

    Returns:
        str: Latest release version tag. E.g. "v1.0.1"
    """

    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data.get("tag_name")
    elif response.status_code == 404:
        print("No releases found — this repo may" +
              " use tags without GitHub releases.")
        return None
    else:
        print(f"Error fetching release: {response.status_code}")
        return None


def read_text(filepath):
    """Given a filepath, returns contents of file.

    Args:
        filepath (str): Path to file to read.

    Returns:
        str: Contents of file.
    """

    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def get_git_config(repo_dir):
    """Returns content of .git/config from repo.

    Args:
        repo_dir (str): location of repo.

    Returns:
        str: contents of repo.
    """

    return read_text(os.path.join(repo_dir, ".git", "config"))


def get_folder_structure(path: str, max_depth: int = None,
                         ignore_dirs=[".git"]) -> str:
    """Walks the folder structure and returns its tree as a string.

    The output is similar to the 'tree' tool.

    Args:
        path (str): Folderpath to traverse.
        max_depth (int, optional): Maximum level to recurse. Defaults to None.
        ignore_dirs (str, optional): Folders to ignore. Defaults to None.

    Returns:
        str: _description_
    """
    base = Path(path).resolve()
    ignore_dirs = set(ignore_dirs)
    tree_output = ["."]

    for entry in sorted(base.rglob("*")):
        if any(part in ignore_dirs for part in entry.parts):
            continue

        rel_path = entry.relative_to(base)
        depth = len(rel_path.parts)
        if max_depth is not None and depth > max_depth:
            continue
        indent = "    " * (depth - 1)
        tree_output.append(f"{indent}└── {rel_path.name}")

    return "\n".join(tree_output)


def send_prompt_to_LLM(prompt: str, model: str = "llama3") -> str:
    """Sends prompt to specified LLM and returns output.

    Args:
        prompt (str): Block of text containg prompt.
        model (str, optional): Name of model. Defaults to "llama3".

    Returns:
        str: response from LLM.
    """

    with console.status("[bold green]Analyzing your README with LLM...[/]"):
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
    return response['message']['content']


def extract_json_block(text: str) -> dict:
    """Extracts last JSON code block from a string and returns it as a dict."""

    pattern = r"```json\s*({.*?})\s*```"
    match = re.search(pattern, text, re.DOTALL)

    if not match:
        raise ValueError("No valid JSON block found in the input.")

    json_str = match.group(1)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON content: {e}")


def get_real_path(filepath: str) -> str:
    """Return real path from a given path

    Args:
        filepath (str): Path to file.

    Returns:
        str: Real filepath.
    """
    return str(Path(filepath).resolve())


def extract_markdown_block(text: str) -> str:
    """
    Extracts the first markdown code block from a string.

    Returns the markdown code as a string.
    """
    pattern = r"```markdown\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_changes_made_block(text: str) -> list:
    """Extracts changes made by the LLM as a list.

    Args:
        text (str): output from LLM.

    Returns:
        bool: True if match found otherwise false.
        list: Changes made by LLM.
    """

    pattern = r"```json\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)

    if len(matches) == 0:
        return False, []
    block = matches[-1].strip() if matches else ""

    data = json.loads(block)

    return True, data['changes_made']


def validate_setup(repo_dir):
    """Fail if repo_dir doesn't exist or README.md is not there".

    Args:
        repo_dir (str): location of repo.
    """

    if repo_dir is None:
        sys.exit("ERROR: You must specify a repo directory.")

    if not os.path.exists(repo_dir):
        sys.exit(f"ERROR: \"{repo_dir}\" does not exist.")

    if not os.path.exists(os.path.join(repo_dir, "README.md")):
        sys.exit("ERROR: Please ensure there is a README.md in your repo.")


@app.command()
def review(repo_dir: str = typer.Option(None, "--repo-dir", "-r",
                                        help="Location of where the"
                                             " repo is cloned."),
           output: str = typer.Option("output.txt", "--output", "-o",
                                      help="Location of where to save"
                                           " formula file."),
           model: str = typer.Option("llama3", "--model", "-m",
                                     help="Name of model.")
           ):
    """Goes through your README.md and provides feedback."""

    validate_setup(repo_dir)

    if ".txt" not in output:
        output = os.path.join(output, ".txt")

    # Extract information.
    git_config_info = get_git_config(repo_dir)
    owner, repo = get_owner_and_repo_from_git_config(repo_dir)
    readme_file_output = get_readme_contents(repo_dir)
    folder_tree = get_folder_structure(repo_dir)

    prompt = f"""
You are an expert in open source documentation. You are going to review my
README.md file. Give me the report in a text block. I intend to show this
report to my client.

The repo folder Tree:
----
{folder_tree}
----
The README
_____
{readme_file_output}
_____

The .git/config file looks like:
____
{git_config_info}
____

Please do the following:
- mention what I am doing well and what I could improve on.
- if any sections are missing like 'usage', 'requirements', etc.
- check for professional tone.
- mention best open source practices.
"""

    results = send_prompt_to_LLM(prompt, model)

    console.print(Panel.fit(f"{results}",
                            title="[bold cyan]Review for"
                                  f" \"{repo}\"[/]",
                            subtitle="[cyan]LLM Powered Improvements by"
                                     f" \"{model}\"[/]",
                            style="green")
                  )

    # Start writing results to file.
    output_filepath = get_real_path(output)
    with open(output, 'w') as f:
        print()
        console.print(f"[bold cyan]Output saved to:[/] {output_filepath}")
        f.write(results)

    print()
    console.print("[bold yellow]WARNING: Please double-check since"
                  " LLMs can make still make mistakes.[/]")


@app.command()
def generate_enhanced_readme(
    repo_dir: str = typer.Option(None, "--repo-dir", "-r",
                                 help="Location of where the repo is cloned."),
    output: str = typer.Option("output_readme.md", "--output", "-o",
                               help="Location of where to save"
                                    " formula file."),
    model: str = typer.Option("llama3", "--model", "-m", help="Name of model.")
                             ):
    """Uses LLM to generate an improved README file."""

    validate_setup(repo_dir)

    if ".md" not in output:
        output = os.path.join(output, ".md")

    # Extract information.
    git_config_info = get_git_config(repo_dir)
    owner, repo = get_owner_and_repo_from_git_config(repo_dir)
    readme_file_output = get_readme_contents(repo_dir)
    folder_tree = get_folder_structure(repo_dir)

    prompt = f"""
You are an expert in open source documentation.

Please improve the following README.md file with better formatting, clearer
sectioning, and enhanced writing quality with a professional tone.

Requirements:
- Do not remove any existing GIFs, demo sections, or badge links.
- Return the **entire updated README** in valid Markdown.
- Be verbose and explain in reasonable detail.

Format your response as:

```markdown
# README

<Improved README content here>

```

At the end, include the JSON block inside a triple backtick block labeled json:
```json
{{
  "changes_made": [
    "Improved formatting for section headers",
    "Rewrote project overview with more clarity",
    "Added demo screenshot to Features section"
  ]
}}

This will allow me to extract the README and track improvements separately.
You CANNOT forget the json block.

The repo folder Tree:
----
{folder_tree}
----
The README
_____
{readme_file_output}
_____

The .git/config file looks like:
____
{git_config_info}
____
Do not print git config info.
"""

    # AI an hallucinate and act unpredictably so try multiple times.
    no_of_attempts = 3
    for x in range(no_of_attempts):
        results = send_prompt_to_LLM(prompt, model)
        readme_contents = extract_markdown_block(results)
        got_match, changes_made = extract_changes_made_block(results)

        if got_match:
            break

    if not got_match:
        sys.exit("ERROR: Could not extract \"changes made\" from LLM.")

    pretty_changes = "\n".join(f"• {item}" for item in changes_made)
    print()
    console.print(
                  Panel.fit(f"{pretty_changes}",
                            title="[bold cyan]Changes Made for"
                                  f" \"{repo}\"[/]",
                            subtitle="[cyan]LLM Powered Improvements by"
                                     f" \"{model}\"[/]",
                            style="green")
                 )

    # Start writing results to file.
    output_filepath = get_real_path(output)
    with open(output, 'w') as f:
        f.write(readme_contents)

    print()
    console.print("[bold yellow]WARNING: Please double-check since"
                  " LLMs can make still make mistakes.[/]")
    print()
    console.print(f"[bold cyan]Output saved to:[/] {output_filepath}")


if __name__ == "__main__":
    app()
