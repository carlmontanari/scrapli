from datetime import datetime

from nssh.result import Result


def test_result_init():
    result = Result("localhost", "ls -al")
    result_start_time = str(datetime.now())[:-7]
    assert result.host == "localhost"
    assert result.channel_input == "ls -al"
    assert str(result.start_time)[:-7] == result_start_time
    assert result.failed is True
    assert bool(result) is True
    assert repr(result) == "SSH2NetResponse <Success: False>"
    assert str(result) == "SSH2NetResponse <Success: False>"


def test_result_record_result():
    result = Result("localhost", "ls -al")
    result_end_time = str(datetime.now())[:-7]
    result_str = """
ls -al
total 264
drwxr-xr-x  34 carl  staff   1088 Jan 27 19:07 ./
drwxr-xr-x  21 carl  staff    672 Jan 25 15:56 ../
-rw-r--r--   1 carl  staff  53248 Jan 27 19:07 .coverage
drwxr-xr-x  12 carl  staff    384 Jan 27 19:13 .git/"""
    result.record_result(result_str)
    assert str(result.finish_time)[:-7] == result_end_time
    assert result.result == result_str
