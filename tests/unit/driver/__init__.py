import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="no asyncssh on windows")
