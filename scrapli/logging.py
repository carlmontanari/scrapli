"""scrapli.logging"""
from ast import literal_eval
from logging import FileHandler, Formatter, LoggerAdapter, LogRecord, NullHandler, getLogger
from typing import Optional, Union, cast

from scrapli.exceptions import ScrapliException


class ScrapliLogRecord(LogRecord):
    message_id: int
    uid: str
    host: str
    port: str
    target: str


class ScrapliFormatter(Formatter):
    def __init__(self, log_header: bool = True, caller_info: bool = False) -> None:
        """
        Scrapli's opinionated custom log formatter class

        Only applied/used when explicitly requested by the user, otherwise we leave logging up to
        the user as any library should!

        Args:
            log_header: add the "header" row to logging output (or not)
            caller_info: add caller (module/package/line) info to log output

        Returns:
            None

        Raises:
            N/A

        """
        log_format = "{message_id:<5} | {asctime} | {levelname:<8} | {target: <25} | {message}"
        if caller_info:
            log_format = (
                "{message_id:<5} | {asctime} | {levelname:<8} | {target: <25} | "
                "{module:<20} | {funcName:<20} | {lineno:<5} | {message}"
            )

        super().__init__(fmt=log_format, style="{")

        self.log_header = log_header
        self.caller_info = caller_info
        self.message_id = 1

        self.header_record = ScrapliLogRecord(
            name="header",
            level=0,
            pathname="",
            lineno=0,
            msg="MESSAGE",
            args=(),
            exc_info=None,
        )
        self.header_record.message_id = 0
        self.header_record.asctime = "TIMESTAMP".ljust(23, " ")
        self.header_record.levelname = "LEVEL"
        self.header_record.uid = "(UID:)"
        self.header_record.host = "HOST"
        self.header_record.port = "PORT"
        self.header_record.module = "MODULE"
        self.header_record.funcName = "FUNCNAME"
        self.header_record.lineno = 0
        self.header_record.message = "MESSAGE"

    def formatMessage(self, record: LogRecord) -> str:
        """
        Override standard library logging Formatter.formatMessage

        Args:
            record: LogRecord to format

        Returns:
            str: log string to emit

        Raises:
            N/A

        """
        record = cast(ScrapliLogRecord, record)

        record.message_id = self.message_id

        if not hasattr(record, "host"):
            # if no host/port set, assign to the record so formatting does not fail
            record.host = ""
            record.port = ""
            _host_port = ""
        else:
            _host_port = f"{record.host}:{record.port}"

        if not hasattr(record, "uid"):
            # maybe this name changes... but a uid in the event you have multiple connections to a
            # single host... w/ this you can assign the uid so you know which is which
            _uid = ""
        else:
            # add colon to the uid so the log messages are pretty
            _uid = f"{record.uid}:"

        record.target = f"{_uid}{_host_port}"
        record.target = (
            record.target[:25] if len(record.target) <= 25 else f"{record.target[:22]}..."
        )

        if self.caller_info:
            record.module = (
                record.module[:20] if len(record.module) <= 20 else f"{record.module[:17]}..."
            )
            record.funcName = (
                record.funcName[:20] if len(record.funcName) <= 20 else f"{record.funcName[:17]}..."
            )

        message = self._style.format(record)

        if self.message_id == 1 and self.log_header:
            # ignoring type for these fields so we can put "pretty" data into the log "header" row
            self.header_record.message_id = "ID"  # type: ignore
            self.header_record.lineno = "LINE"  # type: ignore
            self.header_record.target = "(UID:)HOST:PORT".ljust(len(record.target))
            header_message = self._style.format(self.header_record)
            message = header_message + "\n" + message

        self.message_id += 1

        return message


class ScrapliFileHandler(FileHandler):
    def __init__(
        self,
        filename: str,
        mode: str = "a",
        encoding: Optional[str] = None,
        delay: bool = False,
    ) -> None:
        """
        Handle "buffering" log read messages for logging.FileHandler

        Args:
            filename: name of file to create
            mode: file mode
            encoding: encoding to use for file
            delay: actually not sure what this is for :)

        Returns:
            None

        Raises:
            N/A

        """
        super().__init__(
            filename=filename,
            mode=mode,
            encoding=encoding,
            delay=delay,
        )
        self._record_buf: Optional[LogRecord] = None
        self._record_msg_buf: bytes = b""
        self._read_msg_prefix = "read: "
        self._read_msg_prefix_len = len(self._read_msg_prefix)

    def emit_buffered(self) -> None:
        """
        Emit a buffered read message to the FileHandler

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliException: should never be raised!

        """
        if not self._record_buf:
            raise ScrapliException(
                "something unexpected happened in the ScrapliFileHandler log handler"
            )

        self._record_buf.msg = f"read : {repr(self._record_msg_buf)}"
        super().emit(record=self._record_buf)
        self._record_buf = None
        self._record_msg_buf = b""

    def emit(self, record: LogRecord) -> None:
        """
        Override standard library FileHandler.emit to "buffer" subsequent read messages

        Args:
            record: log record to check

        Returns:
            None

        Raises:
            N/A

        """
        if not record.msg.startswith(self._read_msg_prefix):
            # everytime we get a message *not* starting with "read: " we check to see if there is
            # any buffered message ready to send, if so send it. otherwise, treat the message
            # normally by super'ing to the "normal" handler
            if self._record_buf:
                self.emit_buffered()

            super().emit(record=record)
            return

        if self._record_buf is None:
            # no message in the buffer, set the current record to the _record_buf
            self._record_buf = record
            # get the payload of the message after "read: " and re-convert it to bytes
            self._record_msg_buf = literal_eval(record.msg[self._read_msg_prefix_len :])  # noqa
            return

        # if we get here we know we are getting subsequent read messages we want to buffer -- the
        # log record data will all be the same, its just the payload that will be new, so add that
        # current payload to the _record_msg_buf buffer
        self._record_msg_buf += literal_eval(record.msg[self._read_msg_prefix_len :])  # noqa


def get_instance_logger(
    instance_name: str, host: str = "", port: int = 0, uid: str = ""
) -> LoggerAdapter:
    """
    Get an adapted logger instance for a given instance (driver/channel/transport)

    Args:
        instance_name: logger/instance name, i.e. "scrapli.driver"
        host: host to add to logging extras if applicable
        port: port to add to logging extras if applicable
        uid: unique id for a logging instance

    Returns:
        LoggerAdapter: adapter logger for the instance

    Raises:
        N/A

    """
    extras = {}

    if host and port:
        extras["host"] = host
        extras["port"] = str(port)

    if uid:
        extras["uid"] = uid

    _logger = getLogger(instance_name)
    return LoggerAdapter(_logger, extra=extras)


def enable_basic_logging(
    file: Union[str, bool] = False,
    level: str = "info",
    caller_info: bool = False,
    buffer_log: bool = True,
    mode: str = "write",
) -> None:
    """
    Enable opinionated logging for scrapli

    Args:
        file: True to output to default log path ("scrapli.log"), otherwise string path to write log
            file to
        level: string name of logging level to use, i.e. "info", "debug", etc.
        caller_info: add info about module/function/line in the log entry
        buffer_log: buffer log read outputs
        mode: string of "write" or "append"

    Returns:
        None

    Raises:
        ScrapliException: if invalid mode is passed

    """
    logger.propagate = False
    logger.setLevel(level=level.upper())

    scrapli_formatter = ScrapliFormatter(caller_info=caller_info)

    if mode.lower() not in (
        "write",
        "append",
    ):
        raise ScrapliException("logging file 'mode' must be 'write' or 'append'!")
    file_mode = "a" if mode.lower() == "append" else "w"

    if file:
        if isinstance(file, bool):
            filename = "scrapli.log"
        else:
            filename = file

        if not buffer_log:
            fh = FileHandler(filename=filename, mode=file_mode)
        else:
            fh = ScrapliFileHandler(filename=filename, mode=file_mode)

        fh.setFormatter(scrapli_formatter)

        logger.addHandler(fh)


# get the root scrapli logger and apply NullHandler like a good library should, leave logging things
# up to the user!
logger = getLogger("scrapli")
logger.addHandler(NullHandler())
