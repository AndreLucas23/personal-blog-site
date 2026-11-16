import os

TRUE_VALUES = {'1', 'true', 'yes', 'on'}


def env_flag(name: str) -> bool:
    """Whether an environment variable switches something on. Unset means off."""
    return os.environ.get(name, '').strip().lower() in TRUE_VALUES
