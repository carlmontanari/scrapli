import time

import pytest

from scrapli.decorators import operation_timeout


class SlowClass:
    def __init__(self):
        self.timeout_test = 0.5

    @operation_timeout("timeout_test")
    def slow_function(self):
        time.sleep(1)

    @operation_timeout("timeout_test")
    def fast_function(self):
        return "fast"

    @operation_timeout("non_existent_class_attr")
    def confused_function(self):
        return "fast"


def test_operation_timeout_timeout():
    slow = SlowClass()
    with pytest.raises(TimeoutError):
        slow.slow_function()


def test_operation_timeout_success():
    slow = SlowClass()
    result = slow.fast_function()
    assert result == "fast"


def test_operation_timeout_no_class_attr():
    slow = SlowClass()
    result = slow.confused_function()
    assert result == "fast"
