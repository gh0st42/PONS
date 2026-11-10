"""Make the repository importable (e.g. `import pons`) without installing it.

The simulator is used directly from the working tree, so the test suite
must not require a pip install either.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
