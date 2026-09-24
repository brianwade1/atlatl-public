from pathlib import Path

from portabletorch import PortableTorch
import cnn

# Create torch model
m = cnn.CNN(15)
# Add extra data. Read cnn.py to get shape info.
demo_dir = Path(__file__).resolve().parent
dirname = str(demo_dir / "models" / "cnn")
model_path = str(demo_dir / "cnn.py")
#input_shape = (2)
input_shape = (1,15,5,5)
output_shape = (1)
# Create portable torch model
p = PortableTorch(
    m,
    #"Model",
    "CNN",
    model_path,
    dependence_paths=[],
    #args=[],
    args=[15],
    kwargs={},
    input_shape=input_shape,
    output_shape=output_shape,
    #comment="Simplest example. No extra files (dependencies) or arguments to the model constructor of either type (args nor kwargs).")
    comment="Convolutional example with one positional argument in constructor")
# Save to directory
p.save(dirname)
# Test
p.print()
p.test()
