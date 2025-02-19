# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import contextlib
import json
import os
import pathlib
import subprocess
import sys

import pytest
from typing import Dict, List, Union

SCRIPT_PATH = pathlib.Path(__file__).parent.parent / "installed_check.py"
TEST_DATA = pathlib.Path(__file__).parent / "test_data"
DEFAULT_SEVERITY = 3


@contextlib.contextmanager
def generate_file(base_file: pathlib.Path):
    basename = "pyproject.toml" if "pyproject" in base_file.name else "requirements.txt"
    fullpath = base_file.parent / basename
    if fullpath.exists():
        os.unlink(os.fspath(fullpath))
    fullpath.write_text(base_file.read_text(encoding="utf-8"))
    try:
        yield fullpath
    finally:
        os.unlink(str(fullpath))


def run_on_file(file_path: pathlib.Path) -> List[Dict[str, Union[str, int]]]:
    result = subprocess.run(
        [
            sys.executable,
            os.fspath(SCRIPT_PATH),
            os.fspath(file_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    assert result.returncode == 0
    assert result.stderr == b""
    return json.loads(result.stdout)


EXPECTED_DATA = {
    "missing-deps": [
        {
            "line": 6,
            "character": 0,
            "endLine": 6,
            "endCharacter": 10,
            "package": "flake8-csv",
            "code": "not-installed",
            "severity": 3,
        },
        {
            "line": 10,
            "character": 0,
            "endLine": 10,
            "endCharacter": 11,
            "package": "levenshtein",
            "code": "not-installed",
            "severity": 3,
        },
    ],
    "no-missing-deps": [],
    "pyproject-missing-deps": [
        {
            "line": 8,
            "character": 34,
            "endLine": 8,
            "endCharacter": 44,
            "package": "flake8-csv",
            "code": "not-installed",
            "severity": 3,
        }
    ],
    "pyproject-no-missing-deps": [],
}


@pytest.mark.parametrize("test_name", EXPECTED_DATA.keys())
def test_installed_check(test_name: str):
    base_file = TEST_DATA / f"{test_name}.data"
    with generate_file(base_file) as file_path:
        result = run_on_file(file_path)
        assert result == EXPECTED_DATA[test_name]
