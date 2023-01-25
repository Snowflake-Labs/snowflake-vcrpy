import os


basic_script = """
import pytest


@pytest.mark.snowflake_vcr
def test_basic_with_marker(conn_cnx):
    with conn_cnx() as conn, conn.cursor() as cursor:
        assert cursor.execute("select 1;").fetchall() == [(1,)]


def test_basic_without_marker(conn_cnx):
    with conn_cnx() as conn, conn.cursor() as cursor:
        assert cursor.execute("select 1;").fetchall() == [(1,)]
"""


def test_basic_marker_run_all(pytester, connector_conftest_content):
    pytester.makeconftest(connector_conftest_content)
    pytester.makepyfile(basic_script)
    # run with explict selection 'all' which runs all the tests annotated
    # with @pytest.mark.snowflake_vcr in record and replay mode
    result = pytester.runpytest("-v", "--snowflake-record-tests-selection=all")
    result.assert_outcomes(passed=2)
    cassette_dir_path = pytester.path / "cassettes"
    assert os.listdir(cassette_dir_path) == [
        "test_basic_with_marker.yaml",
        "test_basic_without_marker.yaml",
    ]
