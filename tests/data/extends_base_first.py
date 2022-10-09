from docker0s.app import BaseApp


class TestApp(BaseApp):
    # Set test ID for easy class identification
    test_id = "first"

    # Extend second
    extends = "extends_base_second.py"

    # Second defines compose, this should override
    compose = "first"
