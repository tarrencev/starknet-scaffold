# starknet-scaffold

Scaffold a starknet cairo project.

Includes:
- Python virtual env with poetry
- Containerized runtime w/ `nile` + `cairo`
- Cached test fixtures + cache buster
- Github Actions for testing
- VSCode devcontainer

# Usage

## Compile

```sh
bin/compile
```

Compile project contracts using `nile`

## Test 

```sh
bin/test
```

Run the project test suite. Tests will utilize a cached base deployment defined at `test/conftest.py:build_cache`. Updates to the `conftest.py` file will automatically trigger a contract rebuild.

See example test at:

`test/Contract_test.py`

New tests require a new entry in `bin/test`.

## Deploy

```sh
bin/deploy
```

Deploy a projects contracts. Create a `*.deployments.txt` file to track deployment addresses.

## Development

If you are using VSCode, we provide a development container with all required dependencies.
When opening VS Code, it should ask you to re-open the project in a container, if it finds
the .devcontainer folder. If not, you can open the Command Palette (`cmd + shift + p`),
and run “Remote-Containers: Reopen in Container”.