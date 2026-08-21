# Double Gyre (python)

## Overview

`simulation.py` is a trivial application that manages a very simple `Simulation` with following methods: 
- `_compute_step` contains the math code for generating data at each timestep
- `data` returns a view over simulation data at the current timestep
- `run` is what actually executes the simulation for the requested number of timesteps. it can be given a callback that will be executed after `_compute_step` at each timestep and it will be passed `data` as argument

This simple harness allow to separate what the simulation does from what we want to do with simulation data, i.e. visualization.
In particular, visualization is handed to `adaptors`, that implements a compatible callback function for the simulation (see `run` method).

There are two adaptors:
- `matplotlib`: a very simple adaptor, consisting of a simple callback function without context, that just plots data using `matplotlib` library
- `catalyst`: this is an adaptor with a context, and the callback function is responsible of packing simulation data into a conduit mesh blueprint and call `catalyst_execute`

The adaptor can be chosen using application subcommands (i.e. first positional argument):

- `python simulation.py` without any argument use an empty adaptor (no operation after each timestep computed)
- `python simulation.py matplotlib` use the matplotlib adaptor (it requires you to create a `output` directory in the working directory)
- `python simulation.py insitu` use the `catalyst` adaptor

## How to run the simulation in 3 steps with Catalyst (in-situ)

1. Get libcatalyst
2. Run the simulation
3. Run the simulation with ParaView Catalyst

# 1. Libcatalyst

Create a python venv and install numpy (the only dependency)

```
uv venv
uv pip install numpy
source .venv/bin/activate
```

Get `libcatalyst`, build, and install it

```
git clone --depth 1 https://gitlab.kitware.com/paraview/catalyst.git
cd catalyst
cmake -S . -B build --install-prefix install-here -DCATALYST_WRAP_PYTHON=on-DCATALYST_BUILD_STUB_IMPLEMENTATION=on -DCATALYST_BUILD_TOOLS=on
cmake --build build
cmake --install build
```

Now let venv know about `libcatalyst` just built

```
echo /path-to/catalyst/install-here/lib/python3.14/site-packages > .venv/lib/python-3.14/site-packages/catalyst.pth
```

Test it

```
uv run python -c "import catalyst; import catalyst_conduit; catalyst_conduit.Node()"
```

# 2. Simulation

Simulation can be launched within the venv just setup

```
source /path-to/.venv/source/bin/activate
uv pip install tqdm matplotlib      # required for matplotlib adaptor

# run simulation without adaptor
python simulation.py                # it just runs the simulation without any adaptor

# run simulation with matplotlib adaptor
python simulation.py matplotlib     # run with the matplotlib adaptor
```

# 3. Built once, run many times

Re-run the simulation, now using the "insitu" code branch, which is catalyst-based

```
python simulation.py insitu
```

It runs but nothing happens. We haven't chose any catalyst implementation

```
CATALYST_IMPLEMENTATION_NAME=paraview \
CATALYST_IMPLEMENTATION_PATHS=/Applications/ParaView-6.1.0.app/Contents/Libraries/catalyst \
python simulation.py insitu
```

Still nothing, it runs but it does not produce anything. We chose Paraview as Catalyst implementation, but we haven't specified any visualization script

```
CATALYST_IMPLEMENTATION_NAME=paraview \
CATALYST_IMPLEMENTATION_PATHS=/Applications/ParaView-6.1.0.app/Contents/Libraries/catalyst \
python simulation.py insitu --pipeline catalyst_pipeline.py
```

# EXTRA

We could have chosen a different implementation

https://catalyst-in-situ.readthedocs.io/en/latest/catalyst_replay.html

```
CATALYST_DATA_DUMP_DIRECTORY=dump \
CATALYST_IMPLEMENTATION_NAME=stub \
CATALYST_IMPLEMENTATION_PATHS=/path-to/catalyst/install-here/lib/catalyst \
python simulation.py insitu
```

and this creates a dump that can be replied with catalyst replay

```
CATALYST_IMPLEMENTATION_NAME=paraview \
CATALYST_IMPLEMENTATION_PATHS=/Applications/ParaView-6.1.0.app/Contents/Libraries/catalyst \
PYTHONPATH=/Applications/ParaView-6.1.0.app/Contents/Python:$PYTHONPATH \
/path-to/catalyst/install-here/bin/catalyst_replay dump
```
