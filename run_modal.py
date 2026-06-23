import sys
import collections
import platform

# Mock uname to prevent platform module hangs on Windows
UnameResult = collections.namedtuple('UnameResult', ['system', 'node', 'release', 'version', 'machine', 'processor'])
mock_uname = UnameResult(
    system="Windows",
    node="hostname",
    release="10",
    version="10.0.19045",
    machine="AMD64",
    processor="Intel64 Family 6 Model 158 Stepping 10, GenuineIntel"
)

platform.uname = lambda: mock_uname
platform.system = lambda: "Windows"
platform.release = lambda: "10"
platform.version = lambda: "10.0.19045"
platform.machine = lambda: "AMD64"
platform.processor = lambda: "Intel64 Family 6 Model 158 Stepping 10, GenuineIntel"

import modal.__main__

if __name__ == "__main__":
    modal.__main__.main()
