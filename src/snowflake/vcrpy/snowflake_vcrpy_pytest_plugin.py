import pytest
import json
import gzip
import os
import urllib.parse
from ._vendored.vcrpy import VCR
from ._constant import (
    SnowflakeRecordMode,
    VcrpyRecordMode,
    SNOWFLAKE_REQUEST_ID_STRINGS,
    SNOWFLAKE_DB_RELATED_FIELDS_IN_QUERY,
    SNOWFLAKE_CREDENTIAL_HEADER_FIELDS,
    VOID_STRING,
)


# Internal switch controlling _process_request_recording to scrub information or not
_SCRUB_SNOWFLAKE_INFO = True


def _process_request_recording(request):
    """Process request before recording

    Filter and scrub Snowflake credentials.
    """
    # filter request id
    if _SCRUB_SNOWFLAKE_INFO:
        for key, value in request.query:
            if (
                key in SNOWFLAKE_REQUEST_ID_STRINGS
                or key in SNOWFLAKE_DB_RELATED_FIELDS_IN_QUERY
            ):
                request.uri = request.uri.replace(urllib.parse.quote_plus(value) if request.uri.find(value) == -1 else value, VOID_STRING)
        # scrub snowflake account information
        if request.host.endswith(".snowflakecomputing.com"):
            account = request.host.split(".snowflakecomputing.com")[0]
            request.uri = request.uri.replace(account, VOID_STRING)

        if request.host.endswith(".amazonaws.com"):
            # extract account information from amazon aws request
            account = request.host.split(".amazonaws.com")[0]
            # extract result id from amazon aws request
            code = request.uri.split("/results/")[1].split("/")[0]
            request.uri = request.uri.replace(account, VOID_STRING)
            request.uri = request.uri.replace(code, VOID_STRING)

        # TODO: add filter for gcp and azure cloud service in future work, JIRA ticket:SNOW-954706

    # The following line is to note how to decompress body in request
    # dict_body = json.loads(gzip.decompress(request.body).decode('UTF-8'))

    # Strip sensitive PASSWORD from recorded request.
    # There is a bug in core VCRPY that prevents stripping post body keys when the request body is compressed.
    # SEE: https://github.com/kevin1024/vcrpy/issues/660
    if request.path == '/session/v1/login-request':
        request_json = json.loads(gzip.decompress(request.body).decode('UTF-8'))
        if request_body_data := request_json.get('data'):
            if 'PASSWORD' in request_body_data:
                # Delete sensitive secret
                del request_json['data']['PASSWORD']

                # Re-compress body
                request.body = gzip.compress(json.dumps(request_json).encode('UTF-8'))

                # Update length header
                del request.headers['Content-Length']
                request.headers['Content-Length'] = len(request.body)


    return request


def _process_response_recording(response):
    """Process response recording"""

    # The following line is to note how to decompress body in request
    # dict_body =\
    #  json.loads(gzip.decompress(response["body"]["string"]).decode('UTF-8'))
    for key in SNOWFLAKE_CREDENTIAL_HEADER_FIELDS:
        response["headers"].pop(key, None)
    return response


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "snowflake_vcr: Mark the test as using Snowflake VCR."
    )


@pytest.fixture(autouse=True)
def _snowflake_vcr_marker(request):
    snowflake_record_mode = request.config.getoption(
        "--snowflake-record-tests-selection"
    )
    marker = request.node.get_closest_marker("snowflake_vcr")
    if snowflake_record_mode == SnowflakeRecordMode.ALL or (
        snowflake_record_mode == SnowflakeRecordMode.ANNOTATED and marker
    ):
        request.getfixturevalue("snowflake_vcr_cassette")
    else:
        return


def _update_kwargs(request, kwargs):
    marker = request.node.get_closest_marker("snowflake_vcr")
    if marker:
        kwargs.update(marker.kwargs)


@pytest.fixture
def snowflake_vcr_cassette_name(request):
    """Name of the VCR cassette"""
    test_class = request.cls
    if test_class:
        return "{}.{}".format(test_class.__name__, request.node.name)
    return request.node.name


def pytest_addoption(parser):
    group = parser.getgroup("snowflake-vcrpy")
    group.addoption(
        "--snowflake-vcr-mode",
        action="store",
        dest="snowflake_vcr_mode",
        default=None,
        choices=[e.value for e in VcrpyRecordMode],
        help="Set the recording mode for VCR.py. For more details, "
        "please refer to"
        " https://vcrpy.readthedocs.io/en/latest/usage.html#record-modes.",
    )
    group.addoption(
        "--snowflake-record-tests-selection",
        action="store",
        dest="snowflake_record_tests-selection",
        default=SnowflakeRecordMode.ANNOTATED,
        choices=[e.value for e in SnowflakeRecordMode],
        help="Select the tests to be recorded. `annotated` to "
        "record and replay annotated tests,"
        " `disable` to disable record and play, "
        "`all` to record and replay all the tests.",
    )


@pytest.fixture
def snowflake_vcr_cassette(request, snowflake_vcr, snowflake_vcr_cassette_name):
    kwargs = {}
    _update_kwargs(request, kwargs)
    with snowflake_vcr.use_cassette(snowflake_vcr_cassette_name, **kwargs) as cassette:
        yield cassette


@pytest.fixture(scope="module")
def snowflake_vcr(request, snowflake_vcr_cassette_dir, snowflake_vcr_config):
    kwargs = dict(
        cassette_library_dir=snowflake_vcr_cassette_dir,
        path_transformer=VCR.ensure_suffix(".yaml"),
        before_record_request=_process_request_recording,
        before_record_response=_process_response_recording,
        filter_headers=SNOWFLAKE_CREDENTIAL_HEADER_FIELDS
        if _SCRUB_SNOWFLAKE_INFO
        else [],
        **(snowflake_vcr_config or {})
    )
    _update_kwargs(request, kwargs)
    vcr = VCR(**kwargs)
    return vcr


@pytest.fixture(scope="module")
def snowflake_vcr_cassette_dir(request):
    test_dir = request.node.fspath.dirname
    return os.path.join(test_dir, "cassettes")


@pytest.fixture(scope="module")
def snowflake_vcr_config():
    """
    This is the default empty config.
    Users' definition of snowflake_vcr_config fixture will override the empty config.
    """
    return {}
