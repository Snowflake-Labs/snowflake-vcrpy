# Introduction

snowflake-vcrpy is designed to enhance local development experiences for applications
built on top of snowflake-connector-python. Libraries like snowpark-python or snowflake-sqlalchemy which depends
on the connector for http communication can also take advantage of the tool.

snowflake-vcrpy provides the following features:

1. Record and replay http based tests for faster local development


# Installation from source code

```bash
$git clone git@github.com:sfc-gh-aling/snowflake-vcrpy.git
$cd snowflake-vcrpy
$pip install .
```

# Quick Start

## Annotate a test to run with record and replay

```python
# Annotate the test to run in record and replay mode
@pytest.mark.snowflake_vcr
def test_method():
    pass
```


## Run with pytest

snowflake-vcrpy is a pytest plugin and by default it will identify tests annotated with `@pytest.mark.snowflake_vcr`
and run those tests in record and replay mode.

```bash
$pytest test_method
```

With the first time running the test, a recording file containing http request/response with
the name being `<test_class_name>,<test_method_name>.yaml` will be
generated under the directory `<your_test_folder>/cassettes`.

Once the recording is generated, the following running of the test will run against the local recordings.

If any change is made upon the test itself on purpose which changes the body of the request/response, you could delete
the specific recording file under `<your_test_folder>/cassettes` so that the next running will regenerate the recording.


# pytest options to run tests in record and replay


### Specifying tests

A pytest option is provided to select the tests run in record and replay mode: `--snowflake-record-tests-selectio` and there are three modes `annotated`, `disable`, `all`:

- `annotated`: This is the default mode, pytest will only run the tests annotated with `@pytest.mark.snowflake_vcr` in record and replay mode.
- `disable`: This will disable record and replay for all tests.
- `all` This will all tests in record and replay regardless of whether the test is annotated with `@pytest.mark.snowflake_vcr`.

```bash
# run tests which are annotated with `@pytest.mark.snowflake_vcr` in record and replay, this is the default mode
$pytest <tests>
# run tests which are annotated with `@pytest.mark.snowflake_vcr` in record and replay, with explicitly setting the default mode
$pytest <tests> --snowflake-record-tests-selection annotated
# disable running record and replay mode for all the tests
$pytest <tests> --snowflake-record-tests-selection disable
# run all the tests in record and replay regardless of whether the tests are being annotated with `@pytest.mark.snowflake_vcr`
$pytest <tests> --snowflake-record-tests-selection all
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
