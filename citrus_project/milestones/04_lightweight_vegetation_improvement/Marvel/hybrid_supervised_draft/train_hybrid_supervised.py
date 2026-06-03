from __future__ import absolute_import, division, print_function

import sys
from pathlib import Path

DRAFT_DIR = Path(__file__).resolve().parent
REPO_ROOT = DRAFT_DIR.parents[4]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(1, str(REPO_ROOT))

from options import LiteMonoOptions
from trainer import Trainer

options = LiteMonoOptions()
opts = options.parse()


if __name__ == "__main__":
    trainer = Trainer(opts)
    trainer.train()