import pytest

import click_threading

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
    orig_click_prompt = click.prompt

    @click.command()
    def cli():

        ui = click_threading.UiWorker()

        def target():
            assert click.prompt is not orig_click_prompt
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
