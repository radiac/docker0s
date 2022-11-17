import pytest

from docker0s.app.base import AppsTemplateContext, BaseApp, EnvTemplateContext


@pytest.fixture
def contexts(mk_manifest):
    class TestApp1(BaseApp):
        compose_context = {
            "foo1": "bar1",
        }
        env = {
            "baz1": "qux1",
        }

    class TestApp2(BaseApp):
        compose_context = {
            "foo2": "bar2",
        }
        env = {
            "baz2": "qux2",
        }

    # Create and sanity check
    manifest = mk_manifest(TestApp1, TestApp2)
    apps = manifest.init_apps()
    assert len(apps) == 2
    app1, app2 = apps
    assert isinstance(app1, TestApp1)
    assert isinstance(app2, TestApp2)
    return [app.get_compose_context() for app in apps]


def test_apps_template_context__get__returns_context(contexts):
    context1, context2 = contexts
    assert isinstance(context1["apps"], AppsTemplateContext)
    assert context1["apps"].get("TestApp2")["foo2"] == "bar2"
    assert context1["apps"]["TestApp2"]["foo2"] == "bar2"
    assert context1["apps"].TestApp2["foo2"] == "bar2"
    assert context1["apps"].test_app2["foo2"] == "bar2"
    assert context1["apps"].testApp2["foo2"] == "bar2"


def test_env_template_context__get__returns_env_val(contexts):
    context1, context2 = contexts
    assert isinstance(context1["env"], EnvTemplateContext)
    assert isinstance(context1["apps"].TestApp2["env"], EnvTemplateContext)
    assert context1["env"]["baz1"] == "qux1"
    assert context1["apps"].TestApp2["env"]["baz2"] == "qux2"


def test_apps_template_context__in__bool_correct(contexts):
    context1, context2 = contexts
    assert "TestApp1" in context1["apps"]
    assert "test_app2" in context1["apps"]


def test_apps_template_env__in__bool_correct(contexts):
    context1, context2 = contexts
    assert "baz1" in context1["env"]
    assert "baz2" in context1["apps"].TestApp2["env"]
