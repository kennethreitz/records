import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize('value', ['a=b', 'https://example.com/?a=b&c=d', '=leading=', 'plain', ''])
def test_cli_preserves_parameter_values(value):
    script = Path(__file__).resolve().parents[1] / 'records.py'
    result = subprocess.run(
        [sys.executable, str(script), 'select :value AS value', 'json',
         'value=' + value, '--url=sqlite:///:memory:'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert json.loads(result.stdout) == [{'value': value}]


def test_cli_rejects_parameter_without_equals():
    script = Path(__file__).resolve().parents[1] / 'records.py'
    result = subprocess.run(
        [sys.executable, str(script), 'select :value AS value', 'json',
         'invalid', '--url=sqlite:///:memory:'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    assert result.returncode == 64
    assert 'key=value' in result.stdout
