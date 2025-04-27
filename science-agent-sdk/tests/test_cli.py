import click
from click.testing import CliRunner
from dp.agent.cli.cli import cli

def test_cli_commands():
    runner = CliRunner()
    
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'fetch' in result.output
    assert 'run-lab' in result.output
    assert 'run-cloud' in result.output
    assert 'run-agent' in result.output
    assert 'debug-cloud' in result.output
    
    result = runner.invoke(cli, ['fetch', '--help'])
    assert result.exit_code == 0
    assert 'scaffolding' in result.output
    assert 'config' in result.output
    
    commands = [
        ['fetch', 'scaffolding'],
        ['fetch', 'config'],
        ['run-lab'],
        ['run-cloud'],
        ['run-agent'],
        ['debug-cloud']
    ]
    
    for command in commands:
        result = runner.invoke(cli, command)
        assert result.exit_code == 0
