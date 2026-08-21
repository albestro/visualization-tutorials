from __future__ import annotations

from typing import Self

import catalyst
import catalyst_conduit as conduit

from simulation import SimulationData


class CatalystAdaptor:
    def __init__(
        self,
        script: str,
        channel: str = "grid",
        coordtype: str = "uniform",
    ):
        self._script = script
        self._channel = channel
        self._coordtype = coordtype

        self._initialized = False

    def __enter__(self) -> Self:
        node = conduit.Node()

        # TODO it is decided at runtime
        # node["catalyst_load/implementation"] = "paraview"

        if not self._script is None:
            node["catalyst/scripts/script0/filename"] = self._script

        # TODO keep note of this somewhere
        # node["catalyst/pipelines/dump/type"] = "io"
        # node["catalyst/pipelines/dump/filename"] = "datasets/dump_{timestep:04d}.vtpd"
        # node["catalyst/pipelines/dump/channel"] = self._channel

        try:
            catalyst.initialize(node)
        except catalyst.CatalystError as e:
            raise RuntimeError(f"Catalyst initialize failed: {e}")
        self._initialized = True
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._initialized:
            catalyst.finalize(conduit.Node())
        self._initialized = False

    def callback(self, simdata: SimulationData) -> None:
        nx, ny = simdata.shape

        node = conduit.Node()
        node["catalyst/state/timestep"] = simdata.iteration
        node["catalyst/state/time"] = simdata.time

        channel_path = f"catalyst/channels/{self._channel}"
        node[f"{channel_path}/type"] = "mesh"
        mesh = node[channel_path + "/data"]

        match self._coordtype:
            case "rectilinear":
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
            case "uniform":
                mesh["coordsets/coords/type"] = "uniform"
                mesh["coordsets/coords/dims/i"] = nx
                mesh["coordsets/coords/dims/j"] = ny
                mesh["coordsets/coords/origin/x"] = 0.0
                mesh["coordsets/coords/origin/y"] = 0.0
                mesh["coordsets/coords/spacing/dx"] = simdata.spacing[0]
                mesh["coordsets/coords/spacing/dy"] = simdata.spacing[1]

                mesh["topologies/mesh/type"] = "uniform"
                mesh["topologies/mesh/coordset"] = "coords"

                fields = mesh["fields"]

                fields["Velocity/association"] = "vertex"
                fields["Velocity/topology"] = "mesh"
                fields["Velocity/values/x"].set(simdata.vx.ravel(order="F"))
                fields["Velocity/values/y"].set(simdata.vy.ravel(order="F"))
            case "explicit":
                import numpy as np

                xs, ys = np.meshgrid(simdata.x, simdata.y, indexing="ij")
                mesh["coordsets/coords/type"] = "explicit"
                mesh["coordsets/coords/values/x"].set_external(xs.ravel())
                mesh["coordsets/coords/values/y"].set_external(ys.ravel())

                mesh["topologies/mesh/coordset"] = "coords"
                mesh["topologies/mesh/type"] = "structured"
                # note: topology is number of elements, not number of points
                # TODO order is important to get the right mesh
                mesh["topologies/mesh/elements/dims/i"] = ny - 1
                mesh["topologies/mesh/elements/dims/j"] = nx - 1

                fields = mesh["fields"]

                fields["Velocity/association"] = "vertex"
                fields["Velocity/topology"] = "mesh"
                fields["Velocity/values/x"].set_external(simdata.vx.ravel())
                fields["Velocity/values/y"].set_external(simdata.vy.ravel())
            case _:
                raise NotImplementedError(
                    f"Logic for '{self._coordtype}' mesh type not implemented."
                )

        catalyst.execute(node)
