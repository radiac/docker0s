import re


sanitise_pattern = re.compile(r"[^A-Za-z0-9_\- ]")
word_pattern = re.compile(r"([A-Z])")


def normalise_name(name: str):
    """
    Normalise camelCase, snake_case and kebab-case to PascalCase

    Numbers are treated as lower-case characters, but cannot start the string
    """
    # Strip anything outside A-Z, 0-9, space, dash or underscore
    norm = sanitise_pattern.sub("", name)

    # Add a space before each capital so we preserve camelCase and PascalCase
    norm = word_pattern.sub(r" \1", norm)

    # Remove snake and kebab joins, title everything and remove spaces
    norm = norm.replace("_", " ").replace("-", " ").title().replace(" ", "")

    # Check it starts with A-Z
    if not word_pattern.match(norm):
        raise ValueError(f"Names must start with A-Z: {name}")

    return norm


def pascal_to_snake(name: str):
    """
    Convert a PascalCase name to snake_case, for use in Docker containers

    Assumed to have come from a normalised_name so no sanitation required
    """
    # Add a _ before each capital and remove the first
    name = word_pattern.sub(r"_\1", name).lstrip("_")

    return name.lower()
