---
layout: section
---

## Part 2
### Introducing Catalyst

---

# Catalyst API

Basically, we have to add 3 things in our application code

```python
catalyst_initialize(node_config)    # at application startup
catalyst_execute(node_data)         # at each timestep that generates data
catalyst_finalize(node_info)        # at the teardown of the application
```

Hence, the application flow should somehow follow this structure

```python
simulation_init(...)
# configuration
node_config = ...
catalyst_initialize(node_config)

# simulation loop
for step in range(args.timesteps):
    sim.compute_next_step()
    simdata = sim.data()
    # map simdata to node_data
    catalyst_execute(node_data)

catalyst_finalize(node_info)
```

---

# Catalyst API `catalyst_initialize`

Here we decided that user should provide a **YAML** file with the node for `catalyst_initialize`.

```python
node_config = conduit.Node()

if args.config:
    with open(args.config, "r") as config_yaml:
        node_config.parse(config_yaml.read(), "yaml")

catalyst.initialize(node_config)
```

The configuration can also be hard-coded

```python
node_config = conduit.Node()
node_config["catalyst/scripts/myscript/filename"] = "./paraview_catalyst.py"
catalyst.initialize(node_config)
```

It is up to the developer to decide what to pass to initialize.

---

# Catalyst API `catalyst_execute`

At each step, that we execute exactly as before, we have to map `SimulationData` to a **Conduit Mesh Blueprint** and pass it to `catalyst_execute` so that visualization is triggered.

```python
for step in range(args.timesteps):
    sim.compute_next_step()
    print_progress(step + 1, args.timesteps)

    simdata = sim.data()
    node = conduit.Node()
    node["catalyst/state/timestep"] = simdata.iteration
    node["catalyst/state/time"] = simdata.time
    ...
    mesh["coordsets/coords/values/x"].set_external(xs.ravel())
    mesh["coordsets/coords/values/y"].set_external(ys.ravel())
    ...
    fields["Velocity/values/x"].set_external(simdata.vx.ravel())
    fields["Velocity/values/y"].set_external(simdata.vy.ravel())

    catalyst.execute(node)
```

This is a stripped down mapping just to give an idea, here you find more details about [Conduit Mesh Blueprint](https://llnl-conduit.readthedocs.io/en/latest/blueprint_mesh.html#mesh-blueprint).

---

# Catalyst API `catalyst_finalize`

Nothing special, just call `catalyst_finalize` at the very end of the simulation.

```python
node = conduit.Node()
catalyst.finalize(node)
```

---

# Running with Catalyst

We instrumented our `Simulation` with these calls, so now it's time to run it using Catalyst.

```bash
pvpython simulation.py in-situ
```

**What happens?** The simulation runs, but nothing is produced.

**Why?** Let's debug and see what happens under the hood!

Let's use environment variable `CATALYST_DEBUG=1` to enable Catalyst debug logs

```bash
$ CATALYST_DEBUG=1 pvpython ./simulation.py -t 10 in-situ
catalyst debug: preferring environment variables? no
catalyst debug: implementation name from `CATALYST_IMPLEMENTATION_NAME`: (none)
catalyst debug: no implementation named; using the `stub` implementation: 0x10a6f1188
[==================================================] 010/010 [100%]
```

Note: use `set CATALYST_DEBUG=1` on Windows <cib-windows/>


💡 aha! it's the stub implementation!

---

# Let's switch Catalyst implementation

Let's use `CATALYST_IMPLEMENTATION_NAME` to tell Catalyst the name of the implementation we want to use.

It could be any implementation, `stub` one as we've already seen, or `Ascent`, or `AdiosCatalyst`, or a custom one...
but for the sake of simplicity, we'll use the one shipped with ParaView: **ParaView Catalyst**.

<cib-linux/> <cib-apple/>

```bash
$ CATALYST_DEBUG=1 CATALYST_IMPLEMENTATION_NAME=paraview pvpython ./simulation.py -t 10 in-situ
```

<cib-windows/> (cmd)

```bash
set CATALYST_IMPLEMENTATION_PATHS=C:\Program Files\ParaView 6.2.0\bin
set CATALYST_DEBUG=1
set CATALYST_IMPLEMENTATION_NAME=paraview
pvpython ./simulation.py -t 10 in-situ
```

and...

---

# Let's switch Catalyst implementation

We actually switched Catalyst implementation and we're using ParaView Catalyst!

```bash
catalyst debug: preferring environment variables? no
catalyst debug: implementation name from `CATALYST_IMPLEMENTATION_NAME`: paraview
catalyst debug: search path from default list: `/Applications/ParaView-6.1.0.app/Contents/Libraries/catalyst`
catalyst debug: loaded implementation: 0x1366684e8
[==================================================] 010/010 [100%]
```

It works but **still no output!**

---
layout: statement
---

Were we expecting anything? 🤓 we haven't yet said what ParaView should do with data 😅

---
layout: statement
---

*It does not produce output, but it maps data and calls the catalyst implementation...*

**...it is just that ParaView Catalyst does not know yet what to do with the data.**
