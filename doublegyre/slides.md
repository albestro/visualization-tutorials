---
title: Catalyst in-situ Hands-on
sub_title: A guided walkthrough with a python example
author: Alberto Invernizzi (ETH Zurich | CSCS) @ ParaView Users' Day 2026
theme:
  name: catppuccin-latte
---

Agenda
===

1. **Warm-up**: An overview of the example code
    * Example Code Overview
    * Setup the working space
2. **Introducing Catalyst**: Catalyst API
    * API
    * Running the example with catalyst
3. **ParaView Catalyst**: The ParaView Catalyst implementation
    * How to pass information and data to the implementation
    * How to create a ParaView Catalyst python script
    * Run the visualization

<!-- end_slide -->

Part 1 - Warm-up | Overview
===

# What is the simulation harness?

`simulation.py` manages a simple `Simulation` with a very basic interface.

We don't need to know the internals of the simulation in `engine.py`.

```python
for step in range(args.timesteps):
    sim.compute_next_step()
    simdata = sim.data()
```

It is enough knowing that running the simulation means having a simple for loop with:

- a call for stepping the simulation ahead, i.e. `compute_next_step()`
- and one for retrieving the data of the step, i.e. `data()` which returns `SimulationData`

```python
@dataclass
class SimulationData:
    iteration: int
    dt: float
    shape: tuple[int, int]
    spacing: [float, float]
    x: np.array
    y: np.array
    vx: np.ndarray
    vy: np.ndarray

    @property
    def time(self) -> float:
        return self.iteration * self.dt
```

<!-- end_slide -->

Part 1 - Warm Up | Workspace setup
===

# Requirements

- `ParaView 6`

```bash
export PATH=/Applications/ParaView-6.1.0.app/Contents/bin:$PATH
```

TODO windows

# Quick start

```bash
pvpython simulation.py
```

The simulation runs without producing anything, but we should see a progress bar.
```bash
$ pvpython simulation.py -t 10
[==================================================] 010/010 [100%]
```

<!-- end_slide -->

<!-- jump_to_middle -->
Part 2 - Introducing Catalyst
===
<!-- end_slide -->

Part 2 - Introducing Catalyst | API
===

# Basically, we have to add 3 things in our application code

- `catalyst_initialize(node_config)` at the startup of the application
- `catalyst_execute(node_data)` at each timestep that generates data
- `catalyst_finalize(node_info)` at the teardown of the application

Hence, the application flow should somehow follow this structure

```python
simulation_init(...)

catalyst_initialize(node_config)

while True:
    data = simulation_step(...)
    catalyst_execute(node_data)

catalyst_finalize(node_info)
```

<!-- end_slide -->

Part 2 - Introducing Catalyst | API : `catalyst_initialize`
===

Here we decided that user should provide a **YAML** file with the node for `catalyst_initialize`.

```python
node_config = conduit.Node()

if args.config:
    with open(args.config, "r") as config_yaml:
        node_config.parse(config_yaml.read(), "yaml")

catalyst.initialize(node_config)
```

<!-- end_slide -->

Part 2 - Introducing Catalyst | API : `catalyst_execute`
===


At each step, that we execute exactly as before, we have to map `SimulationData` to a **Conduit Mesh Blueprint**.

```python
for step in range(args.timesteps):
    sim.compute_next_step()
    print_progress(step + 1, args.timesteps)

    simdata = sim.data()
    nx, ny = simdata.shape

    node = conduit.Node()
    node["catalyst/state/timestep"] = simdata.iteration
    node["catalyst/state/time"] = simdata.time

    channel_path = "catalyst/channels/grid"
    channel = node[channel_path]
    channel["type"] = "mesh"
    mesh = channel["data"]

    xs, ys = np.meshgrid(simdata.x, simdata.y, indexing="ij")
    mesh["coordsets/coords/type"] = "explicit"
    mesh["coordsets/coords/values/x"].set_external(xs.ravel())
    mesh["coordsets/coords/values/y"].set_external(ys.ravel())

    mesh["topologies/mesh/coordset"] = "coords"
    mesh["topologies/mesh/type"] = "structured"
    mesh["topologies/mesh/elements/dims/i"] = ny - 1
    mesh["topologies/mesh/elements/dims/j"] = nx - 1

    fields = mesh["fields"]
    fields["Velocity/association"] = "vertex"
    fields["Velocity/topology"] = "mesh"
    fields["Velocity/values/x"].set_external(simdata.vx.ravel())
    fields["Velocity/values/y"].set_external(simdata.vy.ravel())

    catalyst.execute(node)
```

Here you find more details about [Conduit Mesh Blueprint](https://llnl-conduit.readthedocs.io/en/latest/blueprint_mesh.html#mesh-blueprint)

<!-- end_slide -->

Part 2 - Introducing Catalyst | API : `catalyst_finalize`
===

Nothing special, just call it

```python
node = conduit.Node()
catalyst.finalize(node)
```

<!-- end_slide -->

Part 2 - Introducing Catalyst | Running with Catalyst
===

```bash
pvpython simulation.py in-situ
```

# What happens?

The simulation runs, but nothing is produced.

# Why?

Let's debug and see what happens under the hood: let's use env var `CATALYST_DEBUG=1` to enable Catalyst debug logs.

TODO in windows check how to export environment variables on the fly

```bash
$ CATALYST_DEBUG=1 pvpython ./simulation.py -t 10 in-situ
catalyst debug: preferring environment variables? no
catalyst debug: implementation name from `CATALYST_IMPLEMENTATION_NAME`: (none)
catalyst debug: no implementation named; using the `stub` implementation: 0x10a6f1188
[==================================================] 010/010 [100%]
```

💡 aha! it's the stub implementation!

<!-- end_slide -->

Part 2 - Introducing Catalyst | Let's switch Catalyst implementation
===

Let's use `CATALYST_IMPLEMENTATION_NAME` to tell Catalyst the name of the implementation we want to use.

It could be any implementation, `stub` one as we've already seen, or `Ascent`, or `AdiosCatalyst`, or a custom one...

...but for the sake of simplicity, we'll use the one shipped with ParaView, i.e. `ParaView Catalyst`.

```bash
$ CATALYST_DEBUG=1 CATALYST_IMPLEMENTATION_NAME=paraview pvpython ./simulation.py -t 10 in-situ
catalyst debug: preferring environment variables? no
catalyst debug: implementation name from `CATALYST_IMPLEMENTATION_NAME`: paraview
catalyst debug: search path from default list: `/Applications/ParaView-6.1.0.app/Contents/Libraries/catalyst`
catalyst debug: loaded implementation: 0x1366684e8
[==================================================] 010/010 [100%]
```

It works but **still no output!** ...were we expecting anything? 🤓 we haven't yet said what ParaView should do with data 😅

*It does not produce output, but it packs data in the conduit node and calls the catalyst implementation...*

*...it is just that ParaView does not know what to do with the data.*

<!-- end_slide -->

<!-- jump_to_middle -->
Part 3 - ParaView Catalyst
===

<!-- end_slide -->

Part 3 - ParaView Catalyst | ParaView Catalyst Blueprint
===

Each implementation has its own way of being configured.

[ParaView Catalyst Blueprint](https://docs.paraview.org/en/latest/Catalyst/blueprints.html#paraview-catalyst-blueprint)

<!-- column_layout: [1,1] -->

<!-- column: 0 -->

# initialize protocol (for `catalyst_initialize`)

```yaml
catalyst:
    scripts:
        filename: <python-catalyst-script>
```

For more [details](https://docs.paraview.org/en/latest/Catalyst/blueprints.html#protocol-initialize)

# execute protocol (for `catalyst_execute`)

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

<!-- column: 1 -->

Since we implemented the initialization phase to parse a YAML file and pass it as config node for `catalyst_initialize`.

```python
node = conduit.Node()
if args.config:
    with open(args.config, "r") as config_yaml:
        node.parse(config_yaml.read(), "yaml")
catalyst.initialize(node)
```

We can prepare a YAML file and pass it via CLI! 🚀

```yaml
catalyst:
    scripts:
        filename: <script-filepath>
```

**Wait...but what script are we talking about? 🤔**

<!-- reset_layout -->

<!-- end_slide -->

Part 3 - ParaView Catalyst | Need a pipeline script
===

We need to create a Catalyst ParaView python script to describe what visualization we want to produce...

<!-- column_layout: [2,1] -->

<!-- column: 0 -->

## Either manually...

```python
import paraview
from paraview.simple import *

renderView1 = CreateView('RenderView')
...
grid = TrivialProducer(registrationName='grid')

add_z_component = Calculator(registrationName='add_z_component', Input=grid)
add_z_component.Set(
    ResultArrayName='velocity',
    Function='Velocity_X * iHat + Velocity_Y * jHat + 0 * kHat',
)

vector_field = Glyph(registrationName='vector_field', Input=add_z_component, GlyphType='Arrow')
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

Part 3 - ParaView Catalyst | Dump
===

One common option is that our simulation already implements **post-hoc** visualization paradigm, with a format compatible with any of the reader available in ParaView.

The most basic one is **binary format**, simply implemented in the example thanks to **numpy**

```python
simdata = sim.data()
data = np.stack([simdata.vx.T, simdata.vy.T], axis=-1).astype(np.float64)
data.tofile(f"velocity-field-{step:03d}.raw")
```

which can be easily run with

```bash
$ pvpython ./simulation.py -t 10 post-hoc
[==================================================] 010/010 [100%]
$ ls dump-binary
velocity-field-000.raw velocity-field-002.raw velocity-field-004.raw velocity-field-006.raw velocity-field-008.raw
velocity-field-001.raw velocity-field-003.raw velocity-field-005.raw velocity-field-007.raw velocity-field-009.raw
```

and this can be read with `ImageReader` by specifying

- shape
- endianness
- xy vs ij
- number of components
- data type

<!-- end_slide -->

Part 3 - ParaView Catalyst | Create a ParaView Catalyst Script
===

<!-- jump_to_middle -->

Now we have data! Let's open ParaView and create a catalyst script! 🚀
===

TODO image of ParaView GUI

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
pvpython simulation.py in-situ --config config_catalyst/run_script.yaml
```

And produce visualization output of our simulation!

```bash
$ ls datasets
vector_field-000010.png vector_field-000060.png vector_field-000110.png vector_field-000160.png vector_field-000210.png
vector_field-000020.png vector_field-000070.png vector_field-000120.png vector_field-000170.png vector_field-000220.png
vector_field-000030.png vector_field-000080.png vector_field-000130.png vector_field-000180.png vector_field-000230.png
vector_field-000040.png vector_field-000090.png vector_field-000140.png vector_field-000190.png vector_field-000240.png
vector_field-000050.png vector_field-000100.png vector_field-000150.png vector_field-000200.png vector_field-000250.png
```

<!-- end_slide -->

Part 3 - ParaView Catalyst | Visualization
===

<!-- jump_to_middle -->
TODO image result

<!-- end_slide -->

<!-- jump_to_middle -->
Conclusion
===

<!-- end_slide -->

Conclusion | References & Cheatsheet
===

# Useful references
- [Catalyst documentation](https://catalyst-in-situ.readthedocs.io)
- [Catalyst replay](https://catalyst-in-situ.readthedocs.io/en/latest/catalyst_replay.html)
- [Catalyst repository](https://gitlab.kitware.com/paraview/catalyst)

# Cheatsheet

<!-- column_layout: [1,1] -->

<!-- column: 0 -->

## Configuration

Environment variables
- `CATALYST_IMPLEMENTATION_NAME`
- `CATALYST_IMPLEMENTATION_PATHS`

## Debugging

- `CATALYST_DEBUG=1`
- `PARAVIEW_LOG_CATALYST_VERBOSITY=INFO`

<!-- column: 1 -->

## ParaView Visualization Pipeline

```yaml
catalyst:
    scripts:
        filename: myparaview-catalyst-script.py
```

<!-- end_slide -->
<!-- jump_to_middle -->
Extra
===

<!-- end_slide -->
Extra 1 - ParaView Catalyst | ParaView pipelines/io
===

In ParaView Catalyst Blueprint doc, in the definition of `initialize` protocol we see it mentions `pipelines` protocol

```yaml
catalyst:
    pipelines:
        type:       io
        channel:    grid
        filename:   steps-data/output_{timestep:03d}.vtpd
```

So, by adding such a pipeline to the initialization node we get `steps-data` folder with data step by step.

Let's see it in action

```bash
$ pvpython simulation.py -t 5 in-situ --config dump-steps.yaml
```

And the output is there

```bash
$ ls steps-data
output_001      output_002      output_003      output_004      output_005
output_001.vtpd output_002.vtpd output_003.vtpd output_004.vtpd output_005.vtpd
```

And it can be easily opened in ParaView.
