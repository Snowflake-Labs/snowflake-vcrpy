import os
import pytest
import uuid
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

pytest_plugins = ["pytester"]


SKIP_LIVE_TEST = False
try:
    from parameters import CONNECTION_PARAMETERS

    if not CONNECTION_PARAMETERS:
        raise ImportError
except ImportError:
    SKIP_LIVE_TEST = True


RUNNING_ON_GH = os.getenv("GITHUB_ACTIONS") == "true"


try:
    from parameters import CLIENT_FAILOVER_PARAMETERS  # type: ignore
except ImportError:
    CLIENT_FAILOVER_PARAMETERS = {}  # type: ignore


try:
    from parameters import CONNECTION_PARAMETERS_ADMIN  # type: ignore
except ImportError:
    CONNECTION_PARAMETERS_ADMIN = {}  # type: ignore


if RUNNING_ON_GH:
    TEST_SCHEMA = "GH_JOB_{}".format(str(uuid.uuid4()).replace("-", "_"))
else:
    TEST_SCHEMA = "python_connector_tests_" + str(uuid.uuid4()).replace("-", "_")


DEFAULT_PARAMETERS = {
    "account": "<account_name>",
    "user": "<user_name>",
    "password": "<password>",
    "database": "<database_name>",
    "schema": "<schema_name>",
    "protocol": "https",
    "host": "<host>",
    "port": "443",
}


@pytest.fixture(scope="module")
def connector_conftest_content():
    if SKIP_LIVE_TEST:
        pytest.skip("Skip due to no credentials")
    return f"""
    import os
    import time
    import pytest
    import uuid
    from contextlib import contextmanager

    import snowflake.connector
    from snowflake.connector.compat import IS_WINDOWS
    from snowflake.connector.connection import DefaultConverterClass


    CONNECTION_PARAMETERS = {str(CONNECTION_PARAMETERS)}
    CLIENT_FAILOVER_PARAMETERS = {str(CLIENT_FAILOVER_PARAMETERS)}
    DEFAULT_PARAMETERS = {str(DEFAULT_PARAMETERS)}
    CONNECTION_PARAMETERS_ADMIN = {str(CONNECTION_PARAMETERS_ADMIN)}
    TEST_SCHEMA = "{str(TEST_SCHEMA)}"

    @pytest.fixture(scope="session")
    def db_parameters():
        return get_db_parameters()

    def get_db_parameters(connection_name: str = "default"):
        os.environ["TZ"] = "UTC"
        if not IS_WINDOWS:
            time.tzset()

        connections = {{
            "default": CONNECTION_PARAMETERS,
            "client_failover": CLIENT_FAILOVER_PARAMETERS,
        }}

        chosen_connection = connections[connection_name]
        if "account" not in chosen_connection:
            pytest.skip(f"{{connection_name}} connection is"
            f" unavailable in parameters.py")

        # testaccount connection info
        ret = {{**DEFAULT_PARAMETERS, **chosen_connection}}

        # snowflake admin account. Not available in GH actions
        for k, v in CONNECTION_PARAMETERS_ADMIN.items():
            ret["sf_" + k] = v

        if "host" in ret and ret["host"] == DEFAULT_PARAMETERS["host"]:
            ret["host"] = ret["account"] + ".snowflakecomputing.com"

        if "account" in ret and ret["account"] == DEFAULT_PARAMETERS["account"]:
            print_help()
            sys.exit(2)

        # a unique table name
        ret["name"] = "python_tests_" + str(uuid.uuid4()).replace("-", "_")
        ret["name_wh"] = ret["name"] + "wh"

        ret["schema"] = TEST_SCHEMA

        # This reduces a chance to exposing password in test output.
        ret["a00"] = "dummy parameter"
        ret["a01"] = "dummy parameter"
        ret["a02"] = "dummy parameter"
        ret["a03"] = "dummy parameter"
        ret["a04"] = "dummy parameter"
        ret["a05"] = "dummy parameter"
        ret["a06"] = "dummy parameter"
        ret["a07"] = "dummy parameter"
        ret["a08"] = "dummy parameter"
        ret["a09"] = "dummy parameter"
        ret["a10"] = "dummy parameter"
        ret["a11"] = "dummy parameter"
        ret["a12"] = "dummy parameter"
        ret["a13"] = "dummy parameter"
        ret["a14"] = "dummy parameter"
        ret["a15"] = "dummy parameter"
        ret["a16"] = "dummy parameter"
        return ret

    def create_connection(connection_name: str, **kwargs):
        ret = get_db_parameters(connection_name)
        ret.update(kwargs)
        connection = snowflake.connector.connect(**ret)
        return connection

    @pytest.fixture()
    def conn_testaccount(request):
        connection = create_connection("default")
        def fin():
            connection.close()  # close when done
        request.addfinalizer(fin)
        return connection

    @contextmanager
    def db(
        connection_name: str = "default",
        **kwargs,
    ):
        if not kwargs.get("timezone"):
            kwargs["timezone"] = "UTC"
        if not kwargs.get("converter_class"):
            kwargs["converter_class"] = DefaultConverterClass()
        cnx = create_connection(connection_name, **kwargs)
        try:
            yield cnx
        finally:
            cnx.close()

    @pytest.fixture()
    def conn_cnx():
        return db
    """


@pytest.fixture(scope="session")
def live_server():
    return LiveServer()


class LiveServer(object):
    def __init__(self) -> None:
        self.server = HTTPServer(("127.0.0.1", 0), TestHTTPHandler)
        self.thread = Thread(None, self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    @property
    def address(self):
        sockname = self.server.socket.getsockname()
        return "http://" + sockname[0] + ":" + str(sockname[1]) + "/"


class TestHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        response = ("Snowflake" * 10).encode("ascii")

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)
