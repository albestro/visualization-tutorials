---
layout: section
---

# Extra

---

# ParaView Catalyst | ParaView `pipelines/io`

If we don't (or don't want to) have post-hoc for dumping data, in ParaView Catalyst `initialize` protocol we have the `pipelines` protocol

```yaml
# dump-steps.yml
catalyst:
    pipelines:
        type:       io
        channel:    grid
        filename:   steps-data/output_{timestep:03d}.vtpd
```

```bash
$ pvpython simulation.py -t 5 in-situ --config dump-steps.yml
```

that by adding such a pipeline to the initialization node, it dumps data step by step in `steps-data` folder, which can be easily opened in ParaView.

```bash
$ ls steps-data
output_001      output_002      output_003      output_004      output_005
output_001.vtpd output_002.vtpd output_003.vtpd output_004.vtpd output_005.vtpd
```
