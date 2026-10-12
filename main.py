import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-eee",
}

ALIASES = {"NUM_WORKERS": "workers"}


def convert_value(key, value):
    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("true", "1", "yes", "on")

    return str(value)


def get_config():
    config = DEFAULTS.copy()

    # Layer 2: YAML configuration
    yaml_path = Path("config.development.yaml")
    if yaml_path.exists():
        with yaml_path.open(encoding="utf-8") as file:
            yaml_config = yaml.safe_load(file) or {}
        for key, value in yaml_config.items():
            if key in config:
                config[key] = convert_value(key, value)

    # Layer 3: .env configuration
    env_config = dotenv_values(".env")
    for name, value in env_config.items():
        key = ALIASES.get(name, name.removeprefix("APP_").lower())
        if key in config and value is not None:
            config[key] = convert_value(key, value)


    # Layer 4: operating-system environment variables
    for name, value in os.environ.items():
        if name.startswith("APP_") or name == "NUM_WORKERS":
            key = ALIASES.get(name, name.removeprefix("APP_").lower())

            if key in config:
                config[key] = convert_value(key, value)

    return config


@app.get("/effective-config")
def effective_config(request: Request):
    config = get_config()



    # Layer 5: CLI-style query overrides
    for name, value in request.query_params.items():
        if name.startswith("set:"):
            key = name[4:].strip().lower()
        else:
            key = name.strip().lower()

        if key in config:
            config[key] = convert_value(key, value)



    # Never reveal the actual API key
    config["api_key"] = "****"

    return config
