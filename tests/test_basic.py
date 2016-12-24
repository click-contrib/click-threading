import pytest

import click_threading
from click_threading._compat import PY2

import click
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


def test_context_pushing_thread(runner):
    @click.command()
    @click.pass_context
    def cli(ctx):
        contexts = []

        def check_ctx():
            contexts.append(click.get_current_context())

        t = click_threading.Thread(target=check_ctx)
        t.start()
        t.join()

        assert contexts == [ctx]

    runner.invoke(cli, catch_exceptions=False)


def test_ui_worker_basic(runner):
    @click.command()
    def cli():

        ui = click_threading.UiWorker()

        def target():
            click.prompt('two')
            ui.shutdown()

        click.prompt('one')

        with ui.patch_click():
            t = click_threading.Thread(target=target)
            t.start()
            ui.run()

        click.prompt('three')
        t.join()

    result = runner.invoke(cli, catch_exceptions=False, input='y\n' * 3)
    assert result.output.splitlines() == ['one: y', 'two: y', 'three: y']


def test_monkey_patch(capsys):
    old_echo = click.echo
    if PY2:
        old_code = old_echo.func_code
    else:
        old_code = old_echo.__code__

    def wrapper(f, info):
        def new_f(*a, **kw):
            assert old_echo is not f
            if PY2:
                assert f.func_code is old_code
            else:
                assert f.__code__ is old_code

            print("LOL")
            rv = f(*a, **kw)
            print("LOL")
            return rv
        return new_f

    with click_threading.monkey.patch_ui_functions(wrapper):
        assert click.echo is old_echo
        click.echo('Hello world')

    assert click.echo is old_echo
    click.echo('Hello second world')

    out, err = capsys.readouterr()
    assert out.splitlines() == [
        'LOL',
        'Hello world',
        'LOL',
        'Hello second world'
    ]
