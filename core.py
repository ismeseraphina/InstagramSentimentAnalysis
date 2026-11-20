import csv
import json
import re
from pathlib import Path
_PATTERN = re.compile(r"[a-z0-9._]{1,30}\Z", re.ASCII)
