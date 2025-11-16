# HomeAssistant Entity Renamer

This project provides a Python script that allows you to list and rename entities in HomeAssistant based on regular expressions. It leverages the HomeAssistant API and WebSockets to interact with the HomeAssistant server.

The `homeassistant-entity-renamer.py` script provides the following functionality:

-   List entities: You can retrieve a list of entities in HomeAssistant and display their friendly names and entity IDs. You can optionally filter entities using a regular expression.
-   Rename entities: You can rename entities by specifying a search regular expression and a replace regular expression (see Python's [re.sub()](https://docs.python.org/3/library/re.html#re.sub)). The script will display a table with the current entity IDs, new entity IDs, and friendly names. It will ask for confirmation before renaming the entities.
-   Update entities from CSV: You can upload a CSV file containing entity IDs and new friendly names to update entity friendly names in bulk.
-   Search output written to CSV: The script now also writes the search output to a CSV file named `output.csv` in addition to printing it in the terminal.

Preserves the history of renamed entities since it uses the same code path for renaming as the HomeAssistant UI (which preserves history since the release 2022.4). See [this websocket callback](https://github.com/home-assistant/core/blob/2023.7.2/homeassistant/components/config/entity_registry.py#L147).

Tested on HomeAssistant 2023.7.2.

## Requirements

- Python 3.6 or above
- Packages listed in `requirements.txt`

## Installation & Setup

### Quick Setup (Recommended)

Run the provided setup script to automatically create a virtual environment and install dependencies:

```bash
./setup.sh
```

This script will:
- Create a Python virtual environment in the `venv/` directory
- Install all required packages from `requirements.txt`
- Configure the script to run directly without manual environment activation

### Manual Setup

If you prefer manual setup or encounter issues with the quick setup:

1. **Create a virtual environment** (recommended to avoid Python version conflicts):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Option A - Use with virtual environment activation**:
   ```bash
   source venv/bin/activate
   python homeassistant-entity-renamer.py --search <pattern>
   ```

4. **Option B - Use the generated wrapper script** (recommended):
   ```bash
   ./run.sh --search <pattern>
   ```

### Python Version Compatibility Notes

This project has been tested with Python 3.14 and uses a virtual environment to ensure dependency compatibility. If you encounter `ModuleNotFoundError` issues:

1. **Check Python version mismatch**: Different `pip` and `python3` versions can cause import errors
2. **Use virtual environment**: This isolates dependencies and avoids system Python conflicts
3. **Run the setup script**: `./setup.sh` handles environment setup automatically

The setup script creates a `run.sh` wrapper that automatically activates the virtual environment and runs the script, ensuring consistent dependency resolution across different systems.

## Usage

### Command-line Options

- `--search <regex>`: Regular expression for searching entity IDs.
- `--replace <regex>`: Regular expression for replacing in entity IDs. Requires `--search`.
- `--input-file <path>`: Input CSV file containing Friendly Name, Current Entity ID, and New Entity ID.
- `--output-file <path>`: Output CSV file to export the results.
- `-y`, `--yes`: Skip confirmation prompt and proceed non-interactively. **Intended for automated scripts and Docker runs.**
  
### Typical Workflow

1. **Run the setup script** (first time only):
   ```bash
   ./setup.sh
   ```

2. **Configure HomeAssistant connection**: Rename `config.py.example` to `config.py` and modify the configuration variables according to your HomeAssistant setup.

3. **Run the script** with the desired options:
   ```bash
   ./homeassistant-entity-renamer.py --search <search_regex> --replace <replace_regex>
   ```
   
   Replace `<search_regex>` with the regular expression that matches the entities you want to rename. Replace `<replace_regex>` with the regular expression used to rename the entities. Note that you can use all the regex capabilities provided by Python's `re.sub()` function.

4. The script will display a table of entities and, by default, ask for confirmation before renaming unless you specify `--yes` or `-y` to skip the prompt and proceed non-interactively.

> **Note**: After running `./setup.sh` once, the script can be executed directly with `./homeassistant-entity-renamer.py` without needing to activate the virtual environment manually.

## Usage (with Docker)

> **Important: Skipping Confirmation in Non-Interactive Environments**
>
> By default, the script prompts for confirmation before changing entities. If you run this script in Docker **without** allocating an interactive terminal (i.e., without `-it`) and **without** `--yes`/`-y`, you will get an `EOFError` at the prompt.
> Use `--yes` (or `-y`) to proceed non-interactively and suppress the confirmation prompt in Docker/automation.

1. Rename `config.py.example` to `config.py` and modify the configuration variables according to your HomeAssistant setup.
2. `docker build -t homeassistant-renamer .`
3. **Non-interactive safe execution:**
   ```sh
   docker run homeassistant-renamer --search sensor --yes
   ```
   Alternatively, short form:
   ```sh
   docker run homeassistant-renamer --search sensor -y
   ```

> **Warning:**
> When using the `--output-file` option with Docker, the file path must point to a directory that is mapped to your host using Docker's `-v` (volume) flag, otherwise the output file will not be accessible from your computer.

**Example:**
To make the output file accessible on your host, map a local directory (e.g., `$(pwd)/output`) to a container directory (e.g., `/data`):

```sh
docker run -v $(pwd)/output:/data homeassistant-renamer --search sensor --output-file /data/results.csv --yes
```

After the command completes, the file `results.csv` will appear in your local `output` directory.

If you do *not* use a volume mapping, any output file written within the container will only be accessible inside the container, and will not persist or be reachable from your host system.

## Examples

```
$ ./homeassistant-entity-renamer.py --search "interesting"
| Friendly Name              | Entity ID                               |
|----------------------------|-----------------------------------------|
| Interesting Testbutton 1   | input_button.interesting_testbutton_1   |
| Interesting Testdropdown 1 | input_select.interesting_testdropdown_1 |
| Interesting Testentity 1   | input_button.interesting_testentity_1   |
| Interesting testnumber 1   | input_number.interesting_testnumber_1   |
| interesting testtext 1     |   input_text.interesting_testtext_1     |
```
```
$ ./homeassistant-entity-renamer.py --search "interesting_test(.*)_1" --replace "just_another_\1"
| Friendly Name              | Current Entity ID                       | New Entity ID                      |
|----------------------------|-----------------------------------------|------------------------------------|
| Interesting Testbutton 1   | input_button.interesting_testbutton_1   | input_button.just_another_button   |
| Interesting Testdropdown 1 | input_select.interesting_testdropdown_1 | input_select.just_another_dropdown |
| Interesting Testentity 1   | input_button.interesting_testentity_1   | input_button.just_another_entity   |
| Interesting testnumber 1   | input_number.interesting_testnumber_1   | input_number.just_another_number   |
| interesting testtext 1     |   input_text.interesting_testtext_1     |   input_text.just_another_text     |

Do you want to proceed with renaming the entities? (y/N): 
Renaming process aborted.
```
```
$ ./homeassistant-entity-renamer.py --search "interesting_test(.*)_1" --replace "just_another_\1"
| Friendly Name              | Current Entity ID                       | New Entity ID                      |
|----------------------------|-----------------------------------------|------------------------------------|
| Interesting Testbutton 1   | input_button.interesting_testbutton_1   | input_button.just_another_button   |
| Interesting Testdropdown 1 | input_select.interesting_testdropdown_1 | input_select.just_another_dropdown |
| Interesting Testentity 1   | input_button.interesting_testentity_1   | input_button.just_another_entity   |
| Interesting testnumber 1   | input_number.interesting_testnumber_1   | input_number.just_another_number   |
| interesting testtext 1     |   input_text.interesting_testtext_1     |   input_text.just_another_text     |

Do you want to proceed with renaming the entities? (y/N): y
Entity 'input_button.interesting_testbutton_1' renamed to 'input_button.just_another_button' successfully!
Entity 'input_select.interesting_testdropdown_1' renamed to 'input_select.just_another_dropdown' successfully!
Entity 'input_button.interesting_testentity_1' renamed to 'input_button.just_another_entity' successfully!
Entity 'input_number.interesting_testnumber_1' renamed to 'input_number.just_another_number' successfully!
Entity 'input_text.interesting_testtext_1' renamed to 'input_text.just_another_text' successfully!

```

## Advanced Regex Usage: Capture Groups and Replacement Pitfalls

### Using Capture Groups in `--search` and `--replace`

This script's `--search` and `--replace` options support Python regular expressions, including capture groups, exactly as in [`re.sub()`](https://docs.python.org/3/library/re.html#re.sub). Capture groups—expressions wrapped in parentheses—allow you to reference parts of the matched text when rewriting entity IDs.

**Syntax Recap:**
- In `--search`, define your capture groups with parentheses: e.g. `garage_powerstrip_(.*)1`
- In `--replace`, refer to each capture group by `\1`, `\2`, etc. (or `\\1` as needed for your shell/environment)

### Canonical Example: Inserting a Space

**Goal:** Convert all entity IDs like `garage_powerstrip_x1` to `garage_powerstrip_x 1` (insert a space before the final `1`).

**Command:**
```bash
./homeassistant-entity-renamer.py --search "garage_powerstrip_(.*)1" --replace "garage_powerstrip_\\1 1"
```
- In the search: `garage_powerstrip_(.*)1` matches anything after the underscore up to the trailing `1`, capturing it as group 1.
- In the replace: `garage_powerstrip_\\1 1` reconstructs the string, inserting a space before the final 1, with `\\1` referencing the captured group.

> **Why `\\1` and Not Just `\1`?**
>
> In a Python string, `\1` references the first capture group. However, in most Unix shells (including Bash), a single backslash is consumed by the shell before Python ever sees it. To ensure Python receives `\1`, you must escape the backslash: use `\\1` on the command line. Otherwise, your replacement might not use the intended group—or may fail entirely.
>
> **Example evolution:**
> - In Python code: `re.sub(r"garage_powerstrip_(.*)1", r"garage_powerstrip_\1 1", ...)`
> - In Bash CLI: `--replace "garage_powerstrip_\\1 1"` (**double backslash!**)
>
> On Windows (especially Command Prompt), a single backslash might work, but double-backslash is always safe and recommended for cross-platform compatibility.

### Quoting and Backslash Pitfalls

- **Always quote** regex strings to avoid shell interpretation of spaces or special characters, e.g. use `"pattern"` not only `pattern`.
- **Whitespace matters**: accidental spaces in your regex or replacement may change the output.
- On UNIX/Bash, **backslashes must be doubled** (i.e. `\\1`) for the replacement to work as intended. On Windows Command Prompt, `\1` may work, but `\\1` is safer.
- The same escaping rules apply in Docker: `--replace "garage_powerstrip_\\1 1"`.

### Common Issues and Troubleshooting

- If you see the literal string `\1` in your replacement output, you may have under-escaped your backslash and the shell stripped it before Python.
- If you see errors or nothing is replaced, check for extra spaces in your pattern, missed quotes, or incorrect backslash count.
- If in doubt, echo your command and inspect what string is being passed into the script, or put your replacement string in a variable and echo it before running.

**Summary:**
Always use double backslashes (`\\1`, `\\2`, etc.) for capture groups within `--replace` when running from a command shell, and surround all regex arguments with quotes to preserve spacing and special characters.

## Troubleshooting

### Common Issues

#### ModuleNotFoundError: No module named 'requests'

**Problem**: You see an error like:
```
ModuleNotFoundError: No module named 'requests'
```

**Cause**: This typically occurs when:
- Multiple Python versions are installed (e.g., system Python 3.11 and Homebrew Python 3.14)
- Packages were installed with a different `pip` than the `python3` interpreter being used
- The script is trying to use system Python while packages were installed in a user environment

**Solution**:
1. **Use the setup script** (recommended):
   ```bash
   ./setup.sh
   ```

2. **Or manually create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the script**:
   ```bash
   ./homeassistant-entity-renamer.py --search <pattern>
   ```

#### Script won't execute directly

**Problem**: Running `./homeassistant-entity-renamer.py` gives permission denied or interpreter errors.

**Solution**:
1. Ensure the script is executable:
   ```bash
   chmod +x homeassistant-entity-renamer.py
   ```

2. If you see interpreter errors, the shebang line may need updating. Run the setup script:
   ```bash
   ./setup.sh
   ```

#### Virtual Environment Not Found

**Problem**: The script references a virtual environment that doesn't exist.

**Solution**: Run the setup script to recreate the virtual environment:
```bash
./setup.sh
```

## Acknowledgements

This project was developed in cooperation with ChatGPT, a large language model trained by OpenAI, based on the GPT-3.5 & 4.1 architecture.

Feel free to explore and modify the script to suit your specific needs. If you encounter any issues or have suggestions for improvements, please submit them to the project's issue tracker.
