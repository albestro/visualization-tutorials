---
layout: section
---

## Part 3
### ParaView Catalyst

---

# ParaView Catalyst Blueprint

Each implementation has its own way of being configured (see [ParaView Catalyst Blueprint](https://docs.paraview.org/en/latest/Catalyst/blueprints.html#paraview-catalyst-blueprint))

[initialize](https://docs.paraview.org/en/latest/Catalyst/blueprints.html#protocol-initialize) protocol (for `catalyst_initialize`)

```yaml
catalyst:
    scripts:
        filename: <python-catalyst-script>
```

[execute](https://docs.paraview.org/en/latest/Catalyst/blueprints.html#protocol-execute) protocol (for `catalyst_execute`)

```yaml
catalyst:
    state:
        timestep: <value>
    channels:
        type: mesh
        data:
            <conduit mesh blueprint>
```

---

# Initialize ParaView Catalyst

Since we implemented the initialization phase so that i parse a YAML file and use it as config node for `catalyst_initialize`.

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

---

# ParaView Catalyst Pipeline Script

We need to create a ParaView Catalsyt python script to describe what visualization we want to produce.

```python
from paraview.simple import *

renderView1 = CreateView('RenderView')
grid = TrivialProducer(registrationName='grid')
...
vector_field = Glyph(registrationName='vector_field', Input=add_z_component, GlyphType='Arrow')
vector_field.Set(
    OrientationArray=['POINTS', 'velocity'],
    ScaleArray=['POINTS', 'velocity'],
    MaximumNumberOfSamplePoints=2500,
)
...
pNG1 = CreateExtractor('PNG', renderView1, registrationName='PNG1')
pNG1.Writer.Set(
    FileName='vector_field-{timestep:06d}.png',
    Format='PNG',
)
```

Either manually like this, or...

---

# ParaView Catalyst Pipeline Script

... or with ParaView GUI, which is definitely **RECOMMENDED**.

In order to play with data in the GUI, we need data from the simulation first...but to get the data from the simulation we need to instruct catalyst to dump data from the simulation (with a script?!).

<div class="flex justify-center">
🐓 or 🐣
</div>

---

# ParaView Catalyst | Dump

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

---

# ParaView - Load Binary Data

And this can be read with `ImageReader` source filter in ParaView by specifying

<div class="text-sm flex justify-center [&_table]:w-90">

|Property|Value|
|:-|-|
|Data Scalar Type|double|
|Data Byte Order|LittleEndian|
|Data Spacing **\***|0.008 0.008|
|Number Of Scalar Components|2|
|File Lower Left|Unchecked|
|Scalar Array Name **\***|Velocity|
|File Dimensionality|2|
|Dimensions|256 128 0|

</div>

**\*** It should match with what catalyst produces.

<style>
th, td {
  padding-top: 0.2rem !important;
  padding-bottom: 0.2rem !important;
}
</style>

---

<div class="flex flex-col h-full">

# Create a ParaView Catalyst Script

<div>

Now we have loaded data in ParaView GUI! Let's create a catalyst script! 🚀

</div>

<div class="flex-1 min-h-0 flex items-center justify-center">

<img src="/paraview-gui.png" class="max-h-full max-w-full object-contain" alt="ParaView GUI"/>

</div>

<div>

**Remember to add at least an Extractor filter!** Otherwise you're still not producing anything, right?

</div>

</div>

---

# Last step before running...

With the ParaView GUI, you created a pipeline starting from a representative source, i.e. in our case the binary data loaded with `ImageReader` filter.

**Saving Catalyst State** actually saves this exact pipeline, *almost* ready to be used with ParaView Catalyst implementation.
*Almost*, because you have to manually replace the fictitious source, with the source that Catalyst can actually use: **TrivialProducer**.

```diff {class:'text-xs'}
 # create a new 'Image Reader'
-velocityfield000raw = ImageReader(registrationName='velocity-field-000.raw', FileNames=[...])
-velocityfield000raw.Set(
-    ...
-    ScalarArrayName='Velocity',
-    FileDimensionality='2',
-    Dimensions=[250, 125, 0],
-)
+velocityfield000raw = TrivialProducer(registrationName='grid')
```

The name `registrationName` must match the name of the channel sent to Catalyst.

---

# Running with ParaView Catalyst Script

At this point we have the script, and we know how to specify it to Catalyst implementation via the node given to `catalyst_initialize`.

```yaml
# config_catalyst/run_script.yaml
catalyst:
  scripts:
    filename: ./custom.py
```

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

---

<div class="flex flex-col h-full">

# Visualization Results

<div class="flex-1 min-h-0 flex items-center justify-center">

<video src="/doublegyre.mp4" autoplay loop muted playsinline class="max-h-full max-w-full w-auto h-auto object-contain rounded-lg" />

</div>
</div>
