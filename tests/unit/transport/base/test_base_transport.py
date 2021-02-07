import logging

import pytest


def test_base_transport_arg_assignment(base_transport_no_abc, base_transport_args):
    """Assert base_transport_args get assigned to BaseTransport instance"""
    assert base_transport_no_abc._base_transport_args == base_transport_args


@pytest.mark.parametrize(
    "test_data",
    (
        (False, "opening transport connection to 'localhost' on port '22'"),
        (True, "closing transport connection to 'localhost' on port '22'"),
    ),
    ids=("opening", "closing"),
)
def test_pre_open_closing_log(caplog, base_transport_no_abc, test_data):
    """Assert pre_open log message content and log level"""
    caplog.set_level(logging.DEBUG, logger="scrapli.transport")

    closing, expected_log_message = test_data
    base_transport_no_abc._pre_open_closing_log(closing=closing)

    log_record = next(iter(caplog.records))
    assert expected_log_message == log_record.msg
    assert logging.DEBUG == log_record.levelno


@pytest.mark.parametrize(
    "test_data",
    (
        (False, "transport connection to 'localhost' on port '22' opened successfully"),
        (True, "transport connection to 'localhost' on port '22' closed successfully"),
    ),
    ids=("opening", "closing"),
)
def test_post_open_closing_log(caplog, base_transport_no_abc, test_data):
    """Assert post_open log message content and log level"""
    caplog.set_level(logging.DEBUG, logger="scrapli.transport")

    closing, expected_log_message = test_data
    base_transport_no_abc._post_open_closing_log(closing=closing)

    log_record = next(iter(caplog.records))
    assert expected_log_message == log_record.msg
    assert logging.DEBUG == log_record.levelno
