---
title: Catalyst in-situ Hands-on
sub_title: A guided walkthrough with a python example
author: Alberto Invernizzi (Eth Zurich | CSCS) @ ParaView Users' Day 2026
theme:
  name: catppuccin-latte
---

Agenda
===

1. **Warm-up**: An overview of the example code
    * Example Code Overview
    * Setup the working space
    * Adaptors
    * Run the simulation with different adaptors
2. **Introducing Catalyst**: `libcatalyst` and Catalyst API
    * Download, Build and Install
    * Overview of the Catalyst adaptor for this example
    * Select implementation
3. **ParaView Catalyst**: The ParaView Catalyst implementation
    * How to pass information and data to the implementation
    * How to create a ParaView Catalyst python script
    * Run the visualization
4. **Extra**: stub implementation and replay
    * The dump feature
    * catalyst_replay tool
    * catalyst implementations and custom ones

<!-- end_slide -->

Part 1 - Warm-up | Overview
===

### What is the simulation harness?

`simulation.py` manages a simple `Simulation` with:
- `_compute_step()`: generates data at each timestep
- `data()`: returns `SimulationData`
- `run(callback)` executes simulation by calling **callback** at each timestep

```python
def run(self, callback):
    while self._step < self._nsteps:
        self._compute_step()

        if callback:
            callback(self.data())
```

The harness separates **what** the simulation does from **what** we do with the data. **Visualization is handed to **adaptors** via callback**

```bash
$ uv run simulation.py --help
usage: simulation.py [-h] [-t TIMESTEPS] {matplotlib,insitu} ...

Doubly Gyre Simulation

positional arguments:
  {matplotlib,insitu}

options:
  -h, --help            show this help message and exit
  -t, --timesteps TIMESTEPS
                        number of timesteps to run the miniapp
```

<!-- end_slide -->

Part 1 - Warm Up | Workspace setup
===

# Requirements

- `uv`
- `c++` compiler

# Create the environment

```bash
uv venv
uv pip install -r requirements.txt
```

# Quick start: no adaptor

```bash
uv run simulation.py
```

The simulation runs, but with no adaptor it does not produce anything.

```bash
$ uv run simulation.py
100%|█████████████████████████████████████████████████| 250/250 [00:08<00:00, 27.96it/s]
```

<!-- end_slide -->

Part 1 - Warm-up | Adaptors available
===

The adaptor is chosen via subcommand `simulation.py [<adaptor>]`

The adaptor *callback* receives `SimulationData` at each timestep, and it is up to the adaptor implementer to decide what to do with it.

| Adaptor | Description |
|-|-|
|-| if nothing is passed, the callback won't be called at all|
| **matplotlib** | genreate png plots using matplotlib |
| **catalyst** | the `Catalyst` adaptor (more details later) |

<!-- end_slide -->


Part 1 - Warm Up | A basic adaptor with `matplotlib`
===

The first adaptor we're going to use is the `matplotlib`-based one.

It simply create figures and axes where it plots `SimulationData` and then save it to `output` folder in working directory.

```python
def draw_matplotlib(simdata: SimulationData) -> None:
    if simdata.iteration % 25 != 0:
        return

    outdir = Path("./output")
    if not outdir.is_dir():
        outdir.mkdir()

    _, ax = plt.subplots()

    ax.set_aspect("equal", adjustable="box")
    CS = ax.contour(
        # note: z shape is (m,n); contours want n,m,z
        simdata.x,
        simdata.y,
        np.sqrt(simdata.vx**2 + simdata.vy**2).T,
        levels=10,
    )
    ax.clabel(CS, inline=True, fontsize=10)
    ax.set_title("Velocity magnitude iso-contours")
    plt.savefig(outdir / f"Velocitymagnitude.{simdata.iteration:03d}.png")

    ...
```

And running it is just a matter of specifying the adaptor at command line

```bash
uv run simulation.py matplotlib
```
<!-- end_slide -->

<!-- jump_to_middle -->
Part 2 - Introducing Catalyst
===
<!-- end_slide -->

Part 2 - Introducing Catalyst | Getting libcatalyst
===

Catalyst is an API specification developed for simulations (and other scientific data producers) to analyze and visualize data in situ.

It also includes a light-weight implementation of the Catalyst API. This implementation is called `stub`.

## Download, Build and Install

```bash
# see 01-dep-libcatalyst.sh

git clone --depth 1 \
  https://gitlab.kitware.com/paraview/catalyst.git
cd catalyst
cmake -S . -B build \
  --install-prefix install-here \
  -DCATALYST_WRAP_PYTHON=on \
  -DCATALYST_BUILD_STUB_IMPLEMENTATION=on \
  -DCATALYST_BUILD_TOOLS=on
cmake --build build
cmake --install build

# install wrappers inside the venv
echo /path-to/catalyst/install-here/lib/python3.14/site-packages \
  > .venv/lib/python-3.14/site-packages/catalyst.pth
```

## Test setup is working

Let's see if we can import the just built and installed python wrappers

```bash
uv run python -c "import catalyst_conduit; catalyst_conduit.Node()"
```

No news, good news. 🍾

<!-- end_slide -->

Part 2 - Introducing Catalyst | The adaptor
===

Mainly we should add 3 things in our application code

<!-- column_layout: [2, 3] -->

<!-- column: 0 -->

# `catalyst_initialize` at the startup of the application

Here the adaptor implementer decided that user should provide a yaml file with node to give to `catalyst_initialize`.


```python
def __enter__(self) -> Self:
    node = conduit.Node()

    node = conduit.Node()
    node.parse(open(self._config_filepath, "r").read(), "yaml")

    try:
        catalyst.initialize(node)
        self._initialized = True
        return self
    except catalyst.CatalystError as e:
        raise RuntimeError(f"Catalyst initialize failed: {e}")
```

# `catalyst_finalize` at the teardown of the application

```python
def __exit__(self, exc_type, exc, tb) -> None:
    if self._initialized:
        catalyst.finalize(conduit.Node())
    self._initialized = False
```

<!-- column: 1 -->

# `catalyst_execute` at each timestep that generates data

The adaptor implementer has to map `SimulationData` to a **Conduit Mesh Blueprint**

```python
def callback(self, simdata: SimulationData) -> None:
    nx, ny = simdata.shape

    node = conduit.Node()
    node["catalyst/state/timestep"] = simdata.iteration
    node["catalyst/state/time"] = simdata.time

    channel_path = f"catalyst/channels/{self._channel}"
    node[f"{channel_path}/type"] = "mesh"
    mesh = node[channel_path + "/data"]

    mesh["coordsets/coords/type"] = "rectilinear"
    mesh["coordsets/coords/values/x"].set_external(simdata.x)
    mesh["coordsets/coords/values/y"].set_external(simdata.y)

    mesh["topologies/mesh/type"] = "rectilinear"
    mesh["topologies/mesh/coordset"] = "coords"

    fields = mesh["fields"]

    fields["Velocity/association"] = "vertex"
    fields["Velocity/topology"] = "mesh"
    fields["Velocity/values/x"].set(simdata.vx.ravel(order="F"))
    fields["Velocity/values/y"].set(simdata.vy.ravel(order="F"))

    catalyst.execute(node)
```

<!-- reset_layout -->

Here you find more details about [Conduit Mesh Blueprint](https://llnl-conduit.readthedocs.io/en/latest/blueprint_mesh.html#mesh-blueprint)

<!-- end_slide -->

Part 2 - Introducing Catalyst | Running with Catalyst adaptor
===

```bash
uv run simulation.py insitu
```

# What happens?

The simulation runs, but nothing is produced.

# Why?

Let's debug and see what happens under the hood: let's use env var `CATALYST_DEBUG=1` to enable Catalyst debug logs.

```bash
$ CATALYST_DEBUG=1 uv run simulation.py insitu
catalyst debug: preferring environment variables? no
catalyst debug: implementation name from `CATALYST_IMPLEMENTATION_NAME`: (none)
catalyst debug: no implementation named; using the `stub` implementation: 0x10a270240
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████| 250/250 [00:09<00:00, 27.50it/s]
```

💡 aha! it's the stub implementation!

<!-- end_slide -->

Part 2 - Introducing Catalyst | Let's switch Catalyst implementation
===

Let's use `CATALYST_IMPLEMENTATION_NAME` to tell Catalyst the name of the implementation we want to use

```bash
CATLAYST_DEBUG=1 CATALYST_IMPLEMENTATION_NAME=paraview uv run simulation.py insitu
```

but...

```bash

failed to open library: dlopen(/Users/ialberto/workspace/repos/paraview-usersday-2026/doublegyre/libcatalyst.git/install-here/lib/catalyst/libcatalyst-paraview.so, 0x0005): tried:
...
...
...
Traceback (most recent call last):
  File "/Users/ialberto/workspace/repos/paraview-usersday-2026/doublegyre/adaptors/catalyst.py", line 33, in __enter__
    catalyst.initialize(node)
    ~~~~~~~~~~~~~~~~~~~^^^^^^
catalyst.NotFoundError: The implementation library was not found.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/ialberto/workspace/repos/paraview-usersday-2026/doublegyre/simulation.py", line 163, in <module>
    with adaptor:
         ^^^^^^^
  File "/Users/ialberto/workspace/repos/paraview-usersday-2026/doublegyre/adaptors/catalyst.py", line 37, in __enter__
    raise RuntimeError(f"Catalyst initialize failed: {e}")
RuntimeError: Catalyst initialize failed: The implementation library was not found.
```

There is a good news and (clearly) a bad news:

- ✅ Good news is that it now looks for `libcatalyst-paraview`, so it is using the information we're giving it
- ❌ It seems it does not know where to look for the selected implementation 🔍

<!-- end_slide -->

Part 2 - Introducing Catalyst | Where to look for the wanted Catalyst implementation
===

Let's use `CATALYST_IMPLEMENTATION_PATHS`, which allows to specify a list of paths where to look for catalyst implementations shared libraries (`libcatalyst-<name>.so` on UNIX/Linux/macOS)

## Unix/Linux

TODO

`CATALYST_IMPLEMENTATION_PATHS=/usr/local/lib/catalyst`

## macOS

`CATALYST_IMPLEMENTATION_PATHS=/Applications/ParaView-6.1.0.app/Contents/Libraries/catalyst`

# Run

Now it pick the right Catalyst implementation, in the right path, so...

```bash
$ export CATALYST_DEBUG=1
$ export CATALYST_IMPLEMENTATION_NAME=paraview
$ export CATALYST_IMPLEMENTATION_PATHS=/Applications/ParaView-6.1.0.app/Contents/Libraries/catalyst
$ uv run simulation.py -t 1 insitu
catalyst debug: preferring environment variables? no
catalyst debug: implementation name from `CATALYST_IMPLEMENTATION_NAME`: paraview
catalyst debug: search paths from `CATALYST_IMPLEMENTATION_PATHS`
catalyst debug: trying to load `/Applications/ParaView-6.1.0.app/Contents/Libraries/catalyst/libcatalyst-paraview.so`: valid ((no error))
catalyst debug: loaded implementation: 0x1054504e8
100%|███████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 25.59it/s]
```

It works but **still no output!** But were we expecting anything? 🤓 we haven't yet said what ParaView visualization we want.

<!-- end_slide -->

<!-- jump_to_middle -->
Part 3 - ParaView Catalyst
===

<!-- end_slide -->

Part 3 - ParaView Catalyst | ParaView Catalyst Blueprint
===

Each implementation has its own way of being configured. [ParaView Catalyst Blueprint](https://docs.paraview.org/en/latest/Catalyst/blueprints.html#paraview-catalyst-blueprint)

<!-- column_layout: [1,1] -->

<!-- column: 0 -->

# initialize protocol

For more [details](https://catalyst-in-situ.readthedocs.io/en/latest/for_simulation_developers.html#catalyst-initialize)

```yaml
catalyst_load:

    # alternative to CATALYST_IMPLEMENTATION_NAME
    implementation: <impl_name>

    # alternative to CATALYST_IMPLEMENTATION_PATHS
    search_paths:   
    - <path1>
    - <path2>
    - ...
```

For more [details](https://docs.paraview.org/en/latest/Catalyst/blueprints.html#protocol-initialize)

```yaml
catalyst:
    # either
    scripts: filename
    # or
    scripts:
        myscript1:
            filename:
        myscript2:
            filename:
```

<!-- column: 1 -->

# execute protocol

```yaml
catalyst:
    state:
        timestep: <value>
    channels:
        type: mesh
        data:
            <conduit mesh blueprint>
```

For mode [details](https://docs.paraview.org/en/latest/Catalyst/blueprints.html#protocol-execute)

<!-- reset_layout -->

Since the adaptor we implemented parse a yaml file as a node for `catalyst_initialize`, we can prepare one and pass it via CLI! 🚀

<!-- end_slide -->

Part 3 - ParaView Catalyst | Running with ParaView implementation
===

```yaml
catalyst_load:
  implementation: paraview
  search_paths:
    - /Applications/ParaView-6.1.0.app/Contents/Libraries/catalyst
catalyst:
    scripts: ...
```

Wait...but what script are we talking about? 🤔
===

<!-- end_slide -->

Part 3 - ParaView Catalyst | Need a pipeline script
===

We need to create a Catalyst ParaView python script to describe what visualization we want to produce...

<!-- column_layout: [1,1] -->

<!-- column: 0 -->

## Either manually...

```python
import paraview
from paraview.simple import *

renderView1 = CreateView('RenderView')
renderView1.Set(
    ViewSize=[1164, 625],
    OrientationAxesVisibility=0,
    CenterOfRotation=[0.9959283447824419, 0.49609315814450383, 0.0],
    CameraPosition=[0.9959283447824419, 0.49609315814450383, 4.331848123013008],
    CameraFocalPoint=[0.9959283447824419, 0.49609315814450383, 0.0],
    CameraViewAngle=15.463917525773196,
)

# init the 'Grid Axes 3D Actor' selected for 'AxesGrid'
renderView1.AxesGrid.Visibility = 1

# create a new 'XML Image Data Reader'
grid = TrivialProducer(registrationName='grid')
grid.PointArrayStatus = ['Velocity']

# create a new 'Calculator'
add_z_component = Calculator(registrationName='add_z_component', Input=grid)
add_z_component.Set(
    ResultArrayName='velocity',
    Function='Velocity_X * iHat + Velocity_Y * jHat + 0 * kHat',
)

# create a new 'Glyph'
vector_field = Glyph(registrationName='vector_field', Input=add_z_component,
    GlyphType='Arrow')
vector_field.Set(
    OrientationArray=['POINTS', 'velocity'],
    ScaleArray=['POINTS', 'velocity'],
    ScaleFactor=0.2,
    GlyphMode='Uniform Spatial Distribution (Surface Sampling)',
    MaximumNumberOfSamplePoints=2500,
    Seed=1326,
)

vector_fieldDisplay = Show(vector_field, renderView1, 'GeometryRepresentation')

...

pNG1 = CreateExtractor('PNG', renderView1, registrationName='PNG1')
pNG1.Trigger.Frequency = 10

pNG1.Writer.Set(
    FileName='vector_field-{timestep:06d}.png',
    ImageResolution=[1164, 625],
    Format='PNG',
)
```

<!-- column: 1 -->

## ... or with ParaView GUI (RECOMMENDED)

In order to play with data in the GUI, we need data from the simulation first...

...but to get the data from the simulation we need to instruct catalyst to dump data from the simulation (with a script?!).

🐓 or 🐣
===

<!-- end_slide -->

Part 3 - ParaView Catalyst | ParaView pipelines/io
===

In ParaView Catalyst Blueprint doc, in the definition of `initialize` protocol we see it mentions `pipelines`

```yaml
catalyst_load:
    pipelines:
        type:       io
        channel:    grid                        # mesh channel name used in catalyst_execute node
        filename:   steps-data/output_{timestep:03d}.vtpd
```

So, by adding such a pipeline to the initialization node we get `steps-data` folder with data step by step.

Let's see it in action

```bash
uv run simulation.py -t 25 insitu --config dump-steps.yaml
```

And the output is there

```bash
$ ls steps-data
output_001      output_004.vtpd output_008      output_011.vtpd output_015      output_018.vtpd output_022      output_025.vtpd
output_001.vtpd output_005      output_008.vtpd output_012      output_015.vtpd output_019      output_022.vtpd
output_002      output_005.vtpd output_009      output_012.vtpd output_016      output_019.vtpd output_023
output_002.vtpd output_006      output_009.vtpd output_013      output_016.vtpd output_020      output_023.vtpd
output_003      output_006.vtpd output_010      output_013.vtpd output_017      output_020.vtpd output_024
output_003.vtpd output_007      output_010.vtpd output_014      output_017.vtpd output_021      output_024.vtpd
output_004      output_007.vtpd output_011      output_014.vtpd output_018      output_021.vtpd output_025
```

<!-- end_slide -->

Part 3 - ParaView Catalyst | Create a ParaView Catalyst Script
===

TODO image of ParaView GUI

<!-- jump_to_middle -->

Now we have data! Let's open ParaView and create a catalyst script! 🚀
===

<!-- end_slide -->

Part 3 - ParaView Catalyst | Running a ParaView Catalyst Script
===

At this point we have the script, and we know how to specify it to Catalyst implementation via the node given to `catalyst_initialize`.

```yaml
# config_catalyst/run_script.yaml

catalyst:
  scripts:
    filename: ./custom.py
```

So, we can run it...

```bash
uv run simulation.py insitu --config config_catalyst/run_script.yaml
```

And produce visualiation output of our simulation!

```bash
$ ls datasets
vector_field-000010.png vector_field-000060.png vector_field-000110.png vector_field-000160.png vector_field-000210.png
vector_field-000020.png vector_field-000070.png vector_field-000120.png vector_field-000170.png vector_field-000220.png
vector_field-000030.png vector_field-000080.png vector_field-000130.png vector_field-000180.png vector_field-000230.png
vector_field-000040.png vector_field-000090.png vector_field-000140.png vector_field-000190.png vector_field-000240.png
vector_field-000050.png vector_field-000100.png vector_field-000150.png vector_field-000200.png vector_field-000250.png
```

<!-- end_slide -->

Part 4 - Extra | Catalyst stub implementation
===

The `stub` implementation can dump conduit nodes for later replay.

```bash
CATALYST_DATA_DUMP_DIRECTORY=dump \
CATALYST_IMPLEMENTATION_NAME=stub \
CATALYST_IMPLEMENTATION_PATHS=/path-to/catalyst/install-here/lib/catalyst \
uv run simulation.py insitu
```

Creates a dump that can be replayed.

TODO

<!-- end_slide -->

Part 4 - Extra | Catalyst replay
===

```bash
CATALYST_IMPLEMENTATION_NAME=paraview \
CATALYST_IMPLEMENTATION_PATHS=/Applications/ParaView-6.1.0.app/Contents/Libraries/catalyst \
PYTHONPATH=/Applications/ParaView-6.1.0.app/Contents/Python:$PYTHONPATH \
/path-to/catalyst/install-here/bin/catalyst_replay dump
```

Replay as if the simulation was running, without actually running it.

# Why use stub implementation?

IMHO it is more for catalyst implementation developers.

- **Debugging**: Inspect conduit nodes at each step
- **Reproducers**: Create minimal test cases
- **Development**: Iterate quickly without simulation running

<!-- end_slide -->

Part 4 - Extra | Catalyst implementations
===

Yes, you can create your one, basically by implementing full Catalyst API in a custom library.

[all details here](https://catalyst-in-situ.readthedocs.io/en/latest/for_implementation_developers.html)

TODO

Or you one of the existing ones

- Adios Catalyst
- Ascent Catalyst
- ParaView Catalyst

<!-- end_slide -->

Conclusion | Useful references
===

- [Catalyst documentation](https://catalyst-in-situ.readthedocs.io)
- [Catalyst replay](https://catalyst-in-situ.readthedocs.io/en/latest/catalyst_replay.html)
- [Catalyst repository](https://gitlab.kitware.com/paraview/catalyst)
