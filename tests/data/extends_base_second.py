from docker0s.app.base import BaseApp


class TestApp(BaseApp):
    # Set test ID for easy class identification
    test_id = "second"

    # First sets compose, it should override this
    compose = "second"

    # First does not set env_file, this should win
    env_file = "second"
