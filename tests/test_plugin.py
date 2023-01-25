import os
import pytest

basic_scripts = """
import pytest
from urllib.request import urlopen


@pytest.mark.snowflake_vcr
def test_with_marker():
    response = urlopen("ADDR").read()
    assert b'Snowflake' in response

def test_without_marker():
    response = urlopen("ADDR").read()
    assert b'Snowflake' in response
"""


@pytest.fixture(scope="session", autouse=True)
def plugin_was_loaded(pytestconfig):
    # Check that the plugin has been properly installed before proceeding
    assert pytestconfig.pluginmanager.hasplugin("snowflake-vcrpy")


def test_basic_marker_run_selective(pytester, live_server):
    record_marker_path = pytester.path / "cassettes" / "test_with_marker.yaml"
    record_without_marker_path = (
        pytester.path / "cassettes" / "test_without_marker.yaml"
    )
    pytester.makepyfile(basic_scripts.replace("ADDR", live_server.address))

    # run with default implicit selection 'annotated' which only run the tests annotated
    # with @pytest.mark.snowflake_vcr in record and replay mode
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=2)
    cassette_dir_path = pytester.path / "cassettes"
    assert (
        os.listdir(cassette_dir_path) == ["test_with_marker.yaml"]
        and os.path.getsize(record_marker_path) > 50
    )

    # run with explict selection 'annotated' which only run the tests annotated
    # with @pytest.mark.snowflake_vcr in record and replay mode
    result = pytester.runpytest("-v", "--snowflake-record-tests-selection=annotated")
    result.assert_outcomes(passed=2)
    cassette_dir_path = pytester.path / "cassettes"
    assert (
        os.listdir(cassette_dir_path) == ["test_with_marker.yaml"]
        and os.path.getsize(record_marker_path) > 50
    )

    # run with explict selection 'all' which runs all the tests annotated
    # with @pytest.mark.snowflake_vcr in record and replay mode
    result = pytester.runpytest("-v", "--snowflake-record-tests-selection=all")
    result.assert_outcomes(passed=2)
    cassette_dir_path = pytester.path / "cassettes"
    assert (
        os.listdir(cassette_dir_path)
        == ["test_without_marker.yaml", "test_with_marker.yaml"]
        and os.path.getsize(record_marker_path) > 50
        and os.path.getsize(record_without_marker_path) > 50
    )


def test_basic_marker_run_disable(pytester, live_server):
    # Run "disable" requires a clean directory
    pytester.makepyfile(basic_scripts.replace("ADDR", live_server.address))
    # run with explict selection 'disable' which only run the tests annotated
    # with @pytest.mark.snowflake_vcr in record and replay mode
    result = pytester.runpytest("-v", "--snowflake-record-tests-selection=disable")
    result.assert_outcomes(passed=2)
    assert not os.path.exists(pytester.path / "cassettes")


def test_vcr_config(pytester, live_server):
    pytester.makepyfile(
        f"""
from urllib.request import urlopen
import pytest

@pytest.fixture(scope='module')
def snowflake_vcr_config():
    return {{'record_mode': 'none'}}


@pytest.mark.snowflake_vcr
def test_with_vcr_none_record():
    response = urlopen("{live_server.address}").read()
    assert b'Snowflake' in response
"""
    )

    result = pytester.runpytest("-v")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(
        "*No similar requests, that have not been played, found."
    )
    assert not os.path.exists(pytester.path / "cassettes")
