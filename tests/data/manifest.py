from docker0s import App, Host


class TestApp(App):
    # Set test ID for easy class identification
    test_id = "manifest"

    # Extend second
    extends = "extends_base_first.py"


class OtherApp(App):
    path = "other_app"


class Vagrant(Host):
    name = "localhost"
    port = 2222
    user = "vagrant"
