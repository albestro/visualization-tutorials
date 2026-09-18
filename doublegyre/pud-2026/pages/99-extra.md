---
layout: section
---

## Extra

---

# ParaView Catalyst -- ParaView `pipelines/io`

In `initialize` protocol we have `pipelines` protocol

```yaml
catalyst:
    pipelines:
        type:       io
        channel:    grid
        filename:   steps-data/output_{timestep:03d}.vtpd
```

By adding such a pipeline to the initialization node we get `steps-data` folder with data step by step.

Let's see it in action

```bash
$ pvpython simulation.py -t 5 in-situ --config dump-steps.yaml
```


And the output is there, and it can be easily opened in ParaView.

```bash
$ ls steps-data
output_001      output_002      output_003      output_004      output_005
output_001.vtpd output_002.vtpd output_003.vtpd output_004.vtpd output_005.vtpd
```
