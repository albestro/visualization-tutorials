import argparse

from pathlib import Path

from engine import Simulation


def print_progress(step, steps):
    """
    Helper for printing a progress bar
    """
    from os import linesep

    WIDTH = 50
    CHAR = "="
    progress = WIDTH * step // steps
    print("[", end="")
    print(f"{CHAR * progress:{WIDTH}s}", end="")
    print("]", end="")

    print(f" {step:03d}/{steps:03d}", end="")
    print(f" [{100.0 * step / steps:3.0f}%]", end="")
    print(end="\r" if step < steps else linesep)


def main_noviz(sim: Simulation, args):
    for step in range(args.timesteps):
        sim.compute_next_step()
        print_progress(step + 1, args.timesteps)


def main_posthoc(sim: Simulation, args):
    import numpy as np

    args.dump_dir.mkdir(exist_ok=True)

    for step in range(args.timesteps):
        sim.compute_next_step()
        print_progress(step + 1, args.timesteps)

        simdata = sim.data()

        data = np.stack([simdata.vx, simdata.vy], axis=-1).astype("<d")
        data.tofile(args.dump_dir / f"velocity-field-{step:03d}.raw")

    print(data.dtype)
    print(simdata.spacing)
    print(simdata.shape)


def main_insitu(sim: Simulation, args):
    import catalyst
    import catalyst_conduit as conduit
    import numpy as np

    # ===== INITIALIZE
    node = conduit.Node()
    if args.config:
        with open(args.config, "r") as config_yaml:
            node.parse(config_yaml.read(), "yaml")
    catalyst.initialize(node)

    # ===== RUN
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

        xs, ys = np.meshgrid(simdata.x, simdata.y, indexing="xy")
        mesh["coordsets/coords/type"] = "explicit"
        mesh["coordsets/coords/values/x"].set_external(xs.ravel())
        mesh["coordsets/coords/values/y"].set_external(ys.ravel())

        mesh["topologies/mesh/coordset"] = "coords"
        mesh["topologies/mesh/type"] = "structured"
        # note: topology is number of elements, not number of points
        mesh["topologies/mesh/elements/dims/i"] = nx - 1
        mesh["topologies/mesh/elements/dims/j"] = ny - 1

        fields = mesh["fields"]

        fields["Velocity/association"] = "vertex"
        fields["Velocity/topology"] = "mesh"
        fields["Velocity/values/x"].set_external(simdata.vx.ravel())
        fields["Velocity/values/y"].set_external(simdata.vy.ravel())

        catalyst.execute(node)

    # ===== FINALIZE
    node = conduit.Node()
    catalyst.finalize(node)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Doubly Gyre Simulation")
    parser.add_argument(
        "-t",
        "--timesteps",
        type=int,
        help="number of timesteps to run the miniapp",
        default=200,
    )

    parser_sub = parser.add_subparsers(dest="command")

    cmd_posthoc = parser_sub.add_parser("post-hoc")
    cmd_posthoc.add_argument("--dump-dir", type=Path, default="./dump-binary")

    cmd_insitu = parser_sub.add_parser("in-situ")
    cmd_insitu.add_argument("--config", type=str, default=None)

    args = parser.parse_args()

    sim = Simulation()

    match args.command:
        case "post-hoc":
            main_posthoc(sim, args)
        case "in-situ":
            main_insitu(sim, args)
        case None:
            main_noviz(sim, args)
        case _:
            raise ValueError(f"Unkown implementation {args.command}")
