---
layout: section
---

# Part 1 | Warm-up

---

# Simulation Harness

Code in `simulation.py` manages a simple `Simulation` with a very basic interface.

We don't need to know the internals of the simulation in `engine.py`.

It is enough to know that running the `Simulation` means

```python
for step in range(args.timesteps):
    sim.compute_next_step()
    simdata = sim.data()
```

i.e. having a simple for loop with:
- `compute_next_step()`, a call for stepping the simulation ahead
- `data()` which returns `SimulationData`, i.e. it retrieves the data at current step

---

# SimulationData

This is what `Simulation` exposes for each step

```python
@dataclass
class SimulationData:
    iteration: int                          # step index
    dt: float                               # time interval between steps
    shape: tuple[int, int]                  # shape of the 2D mesh
    spacing: tuple[float, float]            # spacing (regular mesh)
    x: npt.NDArray[np.float64]              # x coordinates
    y: npt.NDArray[np.float64]              # y coordinates
    vx: npt.NDArray[np.float64]             # velocity x-component
    vy: npt.NDArray[np.float64]             # velocity y-component

    @property
    def time(self) -> float:                # helper function that returns timestep
        return self.iteration * self.dt
```

This is the data we are going to use for producing the visualization.  
*It is just an example, your code might have different needs.*

---

<div class="flex flex-col h-full">

# A look at the data

<div class="flex-1 min-h-0 flex items-center justify-center">
<img src="/input-data.png" class="max-h-full max-w-full object-contain" alt="ParaView GUI"/>
</div>

</div>

---

# Workspace setup

Requirements:

* `ParaView 6.1` binary release from https://www.paraview.org/download/

Then...

|Platform|PATH|
|-|-|
|<cib-apple/>|`export PATH=/Applications/ParaView-6.1.0.app/Contents/bin:$PATH`|
|<cib-linux/>|`export PATH=<syspath>/ParaView-6.1.0-MPI-Linux-Python3.12-x86_64/bin:$PATH`|
|<cib-windows/> (cmd)|`set PATH=C:\Program Files\ParaView 6.1.0\bin;%PATH%`|

---

# Quick start

Now we can run our Python simulation!

```bash
pvpython simulation.py
```

If we see a progress bar, that's a good sign!

```bash
$ pvpython simulation.py -t 10
[==================================================] 010/010 [100%]
```

Simulation ran successfully, but it didn't produce anything!
