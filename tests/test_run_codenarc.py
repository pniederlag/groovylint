# Copyright (c) 2019 Ableton AG, Berlin. All rights reserved.
#
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.

"""Tests for run_codenarc script."""

import os
import subprocess

from unittest.mock import patch

import pytest

from run_codenarc import (
    parse_args,
    parse_xml_report,
    run_codenarc,
)


def _report_file_contents(name):
    with open(_report_file_path(name)) as report_file:
        return report_file.read()


def _report_file_path(name):
    return os.path.join(os.path.dirname(__file__), 'xml-reports', name)


@pytest.mark.parametrize('report_file, return_code', [
    ('multiple-violations-multiple-files-2.xml', 5),
    ('multiple-violations-multiple-files.xml', 3),
    ('multiple-violations-single-file.xml', 3),
    ('single-violation-multiple-files.xml', 2),
    ('single-violation-single-file.xml', 1),
    ('success.xml', 0),
])
def test_parse_xml_report(report_file, return_code):
    """Test that parse_xml_report handles the given report file as expected.

    These report files were generated by CodeNarc itself.
    """
    assert return_code == parse_xml_report(_report_file_contents(report_file))


@patch('os.remove')
def test_run_codenarc(remove_mock):
    """Test that run_codenarc exits without errors if CodeNarc ran successfully."""
    with patch('subprocess.run') as subprocess_mock:
        subprocess_mock.return_value = subprocess.CompletedProcess(
            args='',
            returncode=0,
            stdout=b'',
        )

        output = run_codenarc(
            args=parse_args(args=[
                '--codenarc-version',
                '1.0',
                '--gmetrics-version',
                '1.0',
                '--slf4j-version',
                '1.0',
            ]),
            report_file=_report_file_path('success.xml'),
        )

    assert _report_file_contents('success.xml') == output


def test_run_codenarc_compilation_failure():
    """Test that run_codenarc raises an error if CodeNarc found compilation errors."""
    with patch('subprocess.run') as subprocess_mock:
        subprocess_mock.return_value = subprocess.CompletedProcess(
            args='',
            returncode=0,
            stdout=b"""
                [main] INFO org.codenarc.source.AbstractSourceCode - Compilation
                failed because of [org.codehaus.groovy.control.CompilationErrorsException]
                with message: [startup failed:
            """,
        )

        with pytest.raises(ValueError):
            run_codenarc(args=parse_args(args=[]))


def test_run_codenarc_failure_code():
    """Test that run_codenarc raises an error if CodeNarc failed to run."""
    with patch('subprocess.run') as subprocess_mock:
        subprocess_mock.return_value = subprocess.CompletedProcess(
            args='',
            returncode=1,
            stdout=b'',
        )

        with pytest.raises(ValueError):
            run_codenarc(args=parse_args(args=[]))


def test_run_codenarc_no_report_file():
    """Test that run_codenarc raises an error if CodeNarc did not produce a report."""
    with patch('subprocess.run') as subprocess_mock:
        subprocess_mock.return_value = subprocess.CompletedProcess(
            args='',
            returncode=0,
            stdout=b'',
        )

        with pytest.raises(ValueError):
            run_codenarc(args=parse_args(args=[]), report_file='invalid')
