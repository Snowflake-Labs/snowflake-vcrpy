from enum import Enum
import uuid


SNOWFLAKE_CREDENTIAL_HEADER_FIELDS = [
    "Authorization",
    "x-amz-server-side-encryption-customer-key-MD5",
    "x-amz-server-side-encryption-customer-key-md5",
    "x-amz-server-side-encryption-customer-key",
    "x-amz-server-side-encryption-customer-algorithm",
    "x-amz-id-2",
    "x-amz-request-id",
    "x-amz-version-id"
]


SNOWFLAKE_REQUEST_ID_STRINGS = [
    "request_guid",
    "request_id",
    "requestId",
    "Signature",
    "Expires",
    "AWSAccessKeyId",
    "x-amz-server-side-encryption-customer-algorithm",

]

SNOWFLAKE_DB_RELATED_FIELDS_IN_QUERY = [
    "databaseName",
    "roleName",
    "schemaName",
    "warehouse",
]

VOID_STRING = str(uuid.UUID(int=0))


class SnowflakeRecordMode(str, Enum):
    """Pytest options to specify running tests in record and replay mode"""

    # record and replay tests annotated with "snowflake_vcr"
    ANNOTATED = "annotated"
    # record and replay all tests
    ALL = "all"
    # do not record and replay any tests
    DISABLE = "disable"


class VcrpyRecordMode(str, Enum):
    ONCE = "once"
    NEW_EPISODES = "new_episodes"
    NONE = "none"
    ALL = "all"
