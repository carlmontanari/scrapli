from datetime import datetime

from scrapli.response import Response


def test_response_init():
    response = Response("localhost", "ls -al")
    response_start_time = str(datetime.now())[:-7]
    assert response.host == "localhost"
    assert response.channel_input == "ls -al"
    assert str(response.start_time)[:-7] == response_start_time
    assert response.failed is True
    assert bool(response) is True
    assert repr(response) == "Scrape <Success: False>"
    assert str(response) == "Scrape <Success: False>"


def test_response_record_result():
    response = Response("localhost", "ls -al")
    response_end_time = str(datetime.now())[:-7]
    response_str = """
ls -al
total 264
drwxr-xr-x  34 carl  staff   1088 Jan 27 19:07 ./
drwxr-xr-x  21 carl  staff    672 Jan 25 15:56 ../
-rw-r--r--   1 carl  staff  53248 Jan 27 19:07 .coverage
drwxr-xr-x  12 carl  staff    384 Jan 27 19:13 .git/"""
    response.record_response(response_str)
    assert str(response.finish_time)[:-7] == response_end_time
    assert response.result == response_str
