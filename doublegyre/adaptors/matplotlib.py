from simulation import SimulationData

from matplotlib import pyplot as plt
import numpy as np


def draw_matplotlib(simdata: SimulationData) -> None:
    """Draw with mathplotlib"""

    if simdata.iteration % 100 != 0:
        return

    # plot the 'vel_x' field iso-contour lines
    _, ax = plt.subplots()

    ax.set_aspect("equal", adjustable="box")
    CS = ax.contour(
        # note: z shape is (m,n); contours want n,m,z
        simdata.x,
        simdata.y,
        np.sqrt(simdata.vx**2 + simdata.vy**2).T,  # TODO transposed
        levels=10,
    )
    ax.clabel(CS, inline=True, fontsize=10)
    ax.set_title("Velocity magnitude iso-contours")
    plt.savefig(f"output/Velocitymagnitude.{simdata.iteration:03d}.png")

    # plot the velocity vectors sub-sampled
    _, ax1 = plt.subplots()
    ax1.set_xlim(simdata.x[0], simdata.x[-1])
    ax1.set_ylim(simdata.y[0], simdata.y[-1])
    ax1.set_aspect("equal", adjustable="box")

    x_coord, y_coord = np.meshgrid(simdata.x, simdata.y, indexing="xy")

    stride = 10
    ax1.quiver(
        x_coord[::stride, ::stride],
        y_coord[::stride, ::stride],
        simdata.vx.T[::stride, ::stride],  # TODO
        simdata.vy.T[::stride, ::stride],  # TODO
    )
    ax1.set_title("Velocity vectors")
    plt.savefig(f"output/Velocity-new.{simdata.iteration:03d}.png")
