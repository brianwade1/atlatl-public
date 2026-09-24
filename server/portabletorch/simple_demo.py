from pathlib import Path

from portabletorch import PortableTorch
import model

# Create torch model
m = model.Model()
# Add extra data. Read model.py to get shape info.
demo_dir = Path(__file__).resolve().parent
dirname = str(demo_dir / "models" / "simple")
model_path = str(demo_dir / "model.py")
input_shape = (2)
output_shape = (1)
# Create portable torch model
p = PortableTorch(
    m,
    "Model",
    model_path,
    dependence_paths=[],
    args=[],
    kwargs={},
    input_shape=input_shape,
    output_shape=output_shape,
    comment="Simplest example. No extra files (dependencies) or arguments to the model constructor of either type (args nor kwargs)."
)
# Save to directory
p.save(dirname)
# Test
p.print()
p.test()
