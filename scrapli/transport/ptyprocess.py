"""
Ptyprocess is under the ISC license, as code derived from Pexpect.
    http://opensource.org/licenses/ISC

Copyright (c) 2013-2014, Pexpect development team
Copyright (c) 2012, Noah Spurrier <noah@noah.org>

PERMISSION TO USE, COPY, MODIFY, AND/OR DISTRIBUTE THIS SOFTWARE FOR ANY PURPOSE
WITH OR WITHOUT FEE IS HEREBY GRANTED, PROVIDED THAT THE ABOVE COPYRIGHT NOTICE
AND THIS PERMISSION NOTICE APPEAR IN ALL COPIES. THE SOFTWARE IS PROVIDED
"AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE
INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT
SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING
OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

Thank you to the folks who create and maintain pexpect, vendoring this here
has been ridiculously helpful! -CM
"""

import builtins
import errno
import io
import os
import signal
import struct
import sys
import time
from shutil import which
from typing import List, Optional, Type, TypeVar

from scrapli.exceptions import SSHNotFound


class PtyProcessError(Exception):
    """Generic error class for this package."""


PtyProcessType = TypeVar("PtyProcessType", bound="PtyProcess")


_EOF, _INTR = None, None


def _make_eof_intr() -> None:
    """
    Set constants _EOF and _INTR.

    This avoids doing potentially costly operations on module load.

    Args:
        N/A

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A

    """
    import termios

    global _EOF, _INTR
    if (_EOF is not None) and (_INTR is not None):
        return

    # inherit EOF and INTR definitions from controlling process.
    try:
        from termios import VEOF, VINTR

        fd = None
        for name in "stdin", "stdout":
            stream = getattr(sys, "__%s__" % name, None)
            if stream is None or not hasattr(stream, "fileno"):
                continue
            try:
                fd = stream.fileno()
            except ValueError:
                continue
        if fd is None:
            # no fd, raise ValueError to fallback on CEOF, CINTR
            raise ValueError("No stream has a fileno")
        intr = ord(termios.tcgetattr(fd)[6][VINTR])
        eof = ord(termios.tcgetattr(fd)[6][VEOF])
    except (ImportError, OSError, IOError, ValueError, termios.error):
        # unless the controlling process is also not a terminal,
        # such as cron(1), or when stdin and stdout are both closed.
        # Fall-back to using CEOF and CINTR. There
        try:
            from termios import CEOF, CINTR

            (intr, eof) = (CINTR, CEOF)
        except ImportError:
            (intr, eof) = (3, 4)

    _INTR = bytes([intr])
    _EOF = bytes([eof])


def _setwinsize(fd: int, rows: int, cols: int) -> None:
    """
    Set window size.

    Some very old platforms have a bug that causes the value for termios.TIOCSWINSZ to be truncated.
    There was a hack here to work around this, but it caused problems with newer platforms so has
    been removed. For details see https://github.com/pexpect/pexpect/issues/39

    Args:
        fd: file descriptor
        rows: int number of rows for terminal
        cols: int number of cols for terminal

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A

    """
    import fcntl
    import termios

    TIOCSWINSZ = getattr(termios, "TIOCSWINSZ", -2146929561)
    # Note, assume ws_xpixel and ws_ypixel are zero.
    s = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(fd, TIOCSWINSZ, s)


class PtyProcess:
    def __init__(self, pid: int, fd: int) -> None:
        """
        This class represents a process running in a pseudoterminal.

        The main constructor is the `spawn` method.

        Args:
            pid: integer value of pid
            fd: integer value of fd

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        _make_eof_intr()  # Ensure _EOF and _INTR are calculated
        self.pid = pid
        self.fd = fd
        readf = io.open(fd, "rb", buffering=0)
        writef = io.open(fd, "wb", buffering=0, closefd=False)
        self.fileobj = io.BufferedRWPair(readf, writef)  # type: ignore

        self.terminated = False
        self.closed = False
        self.exitstatus: Optional[int] = None
        self.signalstatus: Optional[int] = None
        # status returned by os.waitpid
        self.status: Optional[int] = None
        self.flag_eof = False
        # Used by close() to give kernel time to update process status.
        # Time in seconds.
        self.delayafterclose = 0.1
        # Used by terminate() to give kernel time to update process status.
        # Time in seconds.
        self.delayafterterminate = 0.1

    @classmethod
    def spawn(cls: Type[PtyProcessType], spawn_command: List[str]) -> PtyProcessType:
        """Start the given command in a child process in a pseudo terminal.

        This does all the fork/exec type of stuff for a pty, and returns an
        instance of PtyProcess.
        """
        # Note that it is difficult for this method to fail.
        # You cannot detect if the child process cannot start.
        # So the only way you can tell if the child process started
        # or not is to try to read from the file descriptor. If you get
        # EOF immediately then it means that the child is already dead.
        # That may not necessarily be bad because you may have spawned a child
        # that performs some task; creates no stdout output; and then dies.

        import fcntl
        import pty
        import resource
        from pty import CHILD, STDIN_FILENO

        spawn_executable = which(spawn_command[0])
        if spawn_executable is None:
            raise SSHNotFound("ssh executable not found!")
        spawn_command[0] = spawn_executable

        # [issue #119] To prevent the case where exec fails and the user is
        # stuck interacting with a python child process instead of whatever
        # was expected, we implement the solution from
        # http://stackoverflow.com/a/3703179 to pass the exception to the
        # parent process
        # [issue #119] 1. Before forking, open a pipe in the parent process.
        exec_err_pipe_read, exec_err_pipe_write = os.pipe()

        pid, fd = pty.fork()

        # Some platforms must call setwinsize() and setecho() from the
        # child process, and others from the master process. We do both,
        # allowing IOError for either.
        if pid == CHILD:
            try:
                _setwinsize(fd=STDIN_FILENO, rows=24, cols=80)
            except IOError as err:
                if err.args[0] not in (errno.EINVAL, errno.ENOTTY):
                    raise

            # [issue #119] 3. The child closes the reading end and sets the
            # close-on-exec flag for the writing end.
            os.close(exec_err_pipe_read)
            fcntl.fcntl(exec_err_pipe_write, fcntl.F_SETFD, fcntl.FD_CLOEXEC)

            # Do not allow child to inherit open file descriptors from parent,
            # with the exception of the exec_err_pipe_write of the pipe.
            # Impose ceiling on max_fd: AIX bugfix for users with unlimited
            # nofiles where resource.RLIMIT_NOFILE is 2^63-1 and os.closerange()
            # occasionally raises out of range error
            max_fd = min(1048576, resource.getrlimit(resource.RLIMIT_NOFILE)[0])
            pass_fds = sorted({exec_err_pipe_write})
            for pair in zip([2] + pass_fds, pass_fds + [max_fd]):
                os.closerange(pair[0] + 1, pair[1])

            try:
                os.execv(spawn_executable, spawn_command)
            except OSError as err:
                # [issue #119] 5. If exec fails, the child writes the error
                # code back to the parent using the pipe, then exits.
                tosend = f"OSError:{err.errno}:{str(err)}".encode()
                os.write(exec_err_pipe_write, tosend)
                os.close(exec_err_pipe_write)
                os._exit(os.EX_OSERR)

        # Parent
        inst = cls(pid, fd)

        # [issue #119] 2. After forking, the parent closes the writing end
        # of the pipe and reads from the reading end.
        os.close(exec_err_pipe_write)
        exec_err_data = os.read(exec_err_pipe_read, 4096)
        os.close(exec_err_pipe_read)

        # [issue #119] 6. The parent reads eof (a zero-length read) if the
        # child successfully performed exec, since close-on-exec made
        # successful exec close the writing end of the pipe. Or, if exec
        # failed, the parent reads the error code and can proceed
        # accordingly. Either way, the parent blocks until the child calls
        # exec.
        if len(exec_err_data) != 0:
            try:
                errclass, errno_s, errmsg = exec_err_data.split(b":", 2)
                exctype = getattr(builtins, errclass.decode("ascii"), Exception)

                exception = exctype(errmsg.decode("utf-8", "replace"))
                if exctype is OSError:
                    exception.errno = int(errno_s)
            except Exception:
                raise Exception("Subprocess failed, got bad error data: %r" % exec_err_data)
            else:
                raise exception

        try:
            inst.setwinsize(rows=24, cols=80)
        except IOError as err:
            if err.args[0] not in (errno.EINVAL, errno.ENOTTY, errno.ENXIO):
                raise

        return inst

    def __repr__(self) -> str:
        """
        Magic repr method for PtyProcess

        Args:
            N/A

        Returns:
            str: str repr of object

        Raises:
            N/A

        """
        return f"{type(self).__name__}(pid={self.pid}, fd={self.fd})"

    def __del__(self) -> None:
        """
        Magic delete method for PtyProcess

        This makes sure that no system resources are left open. Python only
        garbage collects Python objects. OS file descriptors are not Python
        objects, so they must be handled explicitly. If the child file
        descriptor was opened outside of this class (passed to the constructor)
        then this does not close it.

        Args:
            N/A

        Returns:
            N/A

        Raises:
            N/A

        """
        if not self.closed:
            # It is possible for __del__ methods to execute during the
            # teardown of the Python VM itself. Thus self.close() may
            # trigger an exception because os.close may be None.
            try:
                self.close()
            # which exception, shouldn't we catch explicitly .. ?
            except Exception:
                pass

    def close(self, force: bool = True) -> None:
        """This closes the connection with the child application. Note that
        calling close() more than once is valid. This emulates standard Python
        behavior with files. Set force to True if you want to make sure that
        the child is terminated (SIGKILL is sent if the child ignores SIGHUP
        and SIGINT)."""
        if not self.closed:
            self.flush()

            # in the original ptyprocess vendor'd code the file object is "gracefully" closed,
            # however in some situations it seemed to hang forever on the close call... given that
            # as soon as this connection is closed it will need to be re-opened, and that will of
            # course re-create the fileobject this seems like an ok workaround because for reasons
            # unknown to me... this does not hang (even though in theory delete method just closes
            # things...?)
            del self.fileobj
            # Give kernel time to update process status.
            time.sleep(self.delayafterclose)
            if self.isalive():
                if not self.terminate(force):
                    raise PtyProcessError("Could not terminate the child.")
            self.fd = -1
            self.closed = True
            # self.pid = None

    def flush(self) -> None:
        """
        This does nothing.

        It is here to support the interface for a File-like object.

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """

    def read(self, size: int = 1024) -> bytes:
        """Read and return at most ``size`` bytes from the pty.

        Can block if there is nothing to read. Raises :exc:`EOFError` if the
        terminal was closed.

        Unlike Pexpect's ``read_nonblocking`` method, this doesn't try to deal
        with the vagaries of EOF on platforms that do strange things, like IRIX
        or older Solaris systems. It handles the errno=EIO pattern used on
        Linux, and the empty-string return used on BSD platforms and (seemingly)
        on recent Solaris.
        """
        try:
            s = self.fileobj.read1(size)
        except (OSError, IOError) as err:
            if err.args[0] == errno.EIO:
                # Linux-style EOF
                self.flag_eof = True
                raise EOFError("End Of File (EOF). Exception style platform.")
            raise
        if s == b"":
            # BSD-style EOF (also appears to work on recent Solaris (OpenIndiana))
            self.flag_eof = True
            raise EOFError("End Of File (EOF). Empty string style platform.")

        return s

    def write(self, bytes_to_write: bytes, flush: bool = True) -> int:
        """Write bytes to the pseudoterminal.

        Returns the number of bytes written.
        """
        n = self.fileobj.write(bytes_to_write)
        if flush:
            self.fileobj.flush()
        return n

    def eof(self) -> bool:
        """This returns True if the EOF exception was ever raised."""

        return self.flag_eof

    def terminate(self, force: bool = False) -> bool:
        """
        This forces a child process to terminate.

        It starts nicely with SIGHUP and SIGINT. If "force" is True then moves onto SIGKILL. This
        returns True if the child was terminated. This returns False if the child could not be
        terminated.

        Args:
            force: bool; force termination

        Returns:
            bool: terminate succeeded or failed

        Raises:
            N/A

        """
        if not self.isalive():
            return True
        try:
            self.kill(signal.SIGHUP)
            time.sleep(self.delayafterterminate)
            if not self.isalive():
                return True
            self.kill(signal.SIGCONT)
            time.sleep(self.delayafterterminate)
            if not self.isalive():
                return True
            self.kill(signal.SIGINT)
            time.sleep(self.delayafterterminate)
            if not self.isalive():
                return True
            if force:
                self.kill(signal.SIGKILL)
                time.sleep(self.delayafterterminate)
                if not self.isalive():
                    return True
        except OSError:
            # I think there are kernel timing issues that sometimes cause
            # this to happen. I think isalive() reports True, but the
            # process is dead to the kernel.
            # Make one last attempt to see if the kernel is up to date.
            time.sleep(self.delayafterterminate)
            if not self.isalive():
                return True
        return False

    def isalive(self) -> bool:
        """This tests if the child process is running or not. This is
        non-blocking. If the child was terminated then this will read the
        exitstatus or signalstatus of the child. This returns True if the child
        process appears to be running or False if not. It can take literally
        SECONDS for Solaris to return the right status."""

        if self.terminated:
            return False

        if self.flag_eof:
            # This is for Linux, which requires the blocking form
            # of waitpid to get the status of a defunct process.
            # This is super-lame. The flag_eof would have been set
            # in read_nonblocking(), so this should be safe.
            waitpid_options = 0
        else:
            waitpid_options = os.WNOHANG

        try:
            pid, status = os.waitpid(self.pid, waitpid_options)
        except OSError as e:
            # No child processes
            if e.errno == errno.ECHILD:
                raise PtyProcessError(
                    "isalive() encountered condition "
                    + 'where "terminated" is 0, but there was no child '
                    + "process. Did someone else call waitpid() "
                    + "on our process?"
                )
            raise

        # I have to do this twice for Solaris.
        # I can't even believe that I figured this out...
        # If waitpid() returns 0 it means that no child process
        # wishes to report, and the value of status is undefined.
        if pid == 0:
            try:
                ### os.WNOHANG) # Solaris!
                pid, status = os.waitpid(self.pid, waitpid_options)
            except OSError as e:  # pragma: no cover
                # This should never happen...
                if e.errno == errno.ECHILD:
                    raise PtyProcessError(
                        "isalive() encountered condition "
                        + "that should never happen. There was no child "
                        + "process. Did someone else call waitpid() "
                        + "on our process?"
                    )
                raise

            # If pid is still 0 after two calls to waitpid() then the process
            # really is alive. This seems to work on all platforms, except for
            # Irix which seems to require a blocking call on waitpid or select,
            # so I let read_nonblocking take care of this situation
            # (unfortunately, this requires waiting through the timeout).
            if pid == 0:
                return True

        if pid == 0:
            return True

        if os.WIFEXITED(status):
            self.status = status
            self.exitstatus = os.WEXITSTATUS(status)
            self.signalstatus = None
            self.terminated = True
        elif os.WIFSIGNALED(status):
            self.status = status
            self.exitstatus = None
            self.signalstatus = os.WTERMSIG(status)
            self.terminated = True
        elif os.WIFSTOPPED(status):
            raise PtyProcessError(
                "isalive() encountered condition "
                + "where child process is stopped. This is not "
                + "supported. Is some other process attempting "
                + "job control with our child pid?"
            )
        return False

    def kill(self, sig: int) -> None:
        """Send the given signal to the child application.

        In keeping with UNIX tradition it has a misleading name. It does not
        necessarily kill the child unless you send the right signal. See the
        :mod:`signal` module for constants representing signal numbers.
        """

        # Same as os.kill, but the pid is given for you.
        if self.isalive():
            os.kill(self.pid, sig)

    def setwinsize(self, rows: int = 24, cols: int = 80) -> None:
        """
        Set window size.

        This will cause a SIGWINCH signal to be sent to the child. This does not change the physical
        window size. It changes the size reported to TTY-aware applications like vi or curses --
        applications that respond to the SIGWINCH signal.

        Args:
            rows: int number of rows for terminal
            cols: int number of cols for terminal

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        return _setwinsize(self.fd, rows, cols)
