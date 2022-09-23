import re


sanitise_pattern = re.compile(r"[^A-Za-z_\- ]")
word_pattern = re.compile(r"([A-Z])")


def normalise_name(name: str):
    """
    Normalise camelCase, snake_case and kebab-case to PascalCase
    """
    # Strip anything outside A-Z, space, dash or underscore
    name = sanitise_pattern.sub("", name)

    # Add a space before each capital so we preserve camelCase and PascalCase
    name = word_pattern.sub(r" \1", name)

    # Remove snake and kebab joins, title everything and remove spaces
    return name.replace("_", " ").replace("-", " ").title().replace(" ", "")
