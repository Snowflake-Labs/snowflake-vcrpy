# Introduction

snowflake-vcrpy is a library designed to allow you to record and replay HTTP interactions initiated by snowflake-connector-python for testing purposes. It is a pytest plugin built upon [VCR.py][vcrpy].
 Libraries like snowpark-python or snowflake-sqlalchemy depending
on the connector for HTTP interactions can also take advantage of the library.

snowflake-vcrpy provides the following features:

1. Pytest fixuture to enable record and replay http based tests
2. Pytest options to select the tests run in record and replay mode


# Installation

snowflake-vcrpy can be installed from soure code:

```bash
$ git clone git@github.com:Snowflake-Labs/snowflake-vcrpy.git
$ cd snowflake-vcrpy
$ pip install .
```

# Quick Start

## Annotate a test with pytest marker to run in record and replay

```python
# Annotate the test to run in record and replay mode
import snowflake.connector
@pytest.mark.snowflake_vcr
def test_method():
    CONNECTION_PARAMETERS = {} # snowflake credentials
    with snowflake.connector.connect(**CONNECTION_PARAMETERS) as conn, conn.cursor() as cursor:
        assert cursor.execute('select 1').fetchall() == [(1,)]
```


## Run with pytest

snowflake-vcrpy is a pytest plugin and by default it will identify tests annotated with `@pytest.mark.snowflake_vcr`
and run those tests in record and replay mode.

```bash
$pytest <test_file.py>
```

## Rationale

The utilization of [VCR.py][vcrpy] is incorporated into snowflake-vcrpy to facilitate the process of recording and replaying.

Upon the initial execution of the test, a recording file, consisting of HTTP requests and responses, will be generated and saved under the directory `<your_test_folder>/cassettes` with the naming convention of `<test_class_name>.<test_method_name>.yaml`.

VCR.py will retrieve the serialized requests and responses stored in the cassette file, and if it encounters any HTTP requests from the original test run, it will intercept them and return the relevant responses that were previously recorded.

To accommodate any changes made to the API of the server being tested or any alterations to the response, simply remove the existing cassette files and rerun your tests. VCR.py will identify the missing cassette files and automatically record all HTTP interactions, updating them accordingly.

For advanced topics like on how request matching happens and what options VCR.py provides, please refer to the [VCP.py documentation][vcrpy-doc]. To configure VCR.py within snowflake-vcrpy, please refer to section [Optional vcrpy configuration](#optional-vcrpy-configuration).

# pytest options to run tests in record and replay


### Specifying tests

A pytest option is provided to select the tests run in record and replay mode: `--snowflake-record-tests-selectio` and there are three modes `annotated`, `disable`, `all`:

- `annotated`: This is the default mode, pytest will only run the tests annotated with `@pytest.mark.snowflake_vcr` in record and replay mode.
- `disable`: This will disable record and replay for all tests.
- `all` This will all tests in record and replay regardless of whether the test is annotated with `@pytest.mark.snowflake_vcr`.

```bash
# run tests which are annotated with `@pytest.mark.snowflake_vcr` in record and replay, this is the default mode
$ pytest <tests>
# run tests which are annotated with `@pytest.mark.snowflake_vcr` in record and replay, with explicitly setting the default mode
$ pytest <tests> --snowflake-record-tests-selection annotated
# disable running record and replay mode for all the tests
$ pytest <tests> --snowflake-record-tests-selection disable
# run all the tests in record and replay regardless of whether the tests are being annotated with `@pytest.mark.snowflake_vcr`
$ pytest <tests> --snowflake-record-tests-selection all
```


## Optional vcrpy configuration

### Customized vcrpy config per test case

```python
vcr_config = {
    'path': '<path_to_recording>'
    # for more configs please refer to: https://vcrpy.readthedocs.io/en/latest/configuration.html
}
@pytest.mark.snowflake_vcr(**vcr_config)
def test_method_passing_vcr_config():
    pass
```

### Global pytest fixture

snowflake-vcrpy pytest plugin will read the pytest fixture `snowflake_vcr_config` to create module-scope
VCR instance. If configs are also provided through pytest marker kwargs, then
the global fixture configs will be overridden.

```python
@pytest.fixture(scope="module")
def snowflake_vcr_config():
    return {
        # your vcr config dict
    }
```


<!-- LINKS -->
[vcrpy]: https://github.com/kevin1024/vcrpy
[vcrpy-doc]: https://vcrpy.readthedocs.io/en/latest/index.html
