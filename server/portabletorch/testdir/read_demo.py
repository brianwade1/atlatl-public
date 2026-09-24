import argparse
from pathlib import Path
import sys

demo_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(demo_dir))
from portabletorch import PortableTorch

parser = argparse.ArgumentParser(description="Load a saved PortableTorch demo model.")
parser.add_argument("model", choices=("simple", "cnn"), nargs="?", default="simple")
args = parser.parse_args()
portable = PortableTorch.load(str(demo_dir / "models" / args.model))

portable.print()
portable.test()
