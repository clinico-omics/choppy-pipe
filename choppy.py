#!/usr/bin/env python
"""
Choppy is a tool for submitting workflows via command-line to the cromwell execution engine servers.
"""

import sys
from choppy.choppy import main

if __name__ == "__main__":
    sys.exit(main())