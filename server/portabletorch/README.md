# PortableTorch demos

These scripts demonstrate saving and loading neural networks. They create randomly
initialized models; they do not train them.

Run from the repository root:

```sh
uv run python server/portabletorch/simple_demo.py
uv run python server/portabletorch/testdir/read_demo.py simple

uv run python server/portabletorch/cnn_demo.py
uv run python server/portabletorch/testdir/read_demo.py cnn
```

Each demo saves a bundle containing `model.pt`, `info.json`, and the model's Python
source under `server/portabletorch/models/simple/` or
`server/portabletorch/models/cnn/`. These locations are relative to the scripts,
regardless of the working directory. The output folder is ignored by Git.
Rerunning a demo replaces its own saved bundle. The CNN demo creates a much larger
model than the simple demo.

The reader defaults to `simple` if no model name is provided. With Make installed,
you can also run `make simple_test` or `make cnn_test` from this directory;
`make clean` removes the generated model folder and Python caches.
