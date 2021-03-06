import click
import matplotlib.collections
import matplotlib.pyplot as plt

from vpype import global_processor, as_vector, VectorData, convert
from .cli import cli

COLORS = [
    (0, 0, 1),
    (0, 0.5, 0),
    (1, 0, 0),
    (0, 0.75, 0.75),
    (0, 1, 0),
    (0.75, 0, 0.75),
    (0.75, 0.75, 0),
    (0, 0, 0),
]


@cli.command(group="Output")
@click.option("-a", "--show-axes", is_flag=True, help="Display axes.")
@click.option("-g", "--show-grid", is_flag=True, help="Display grid (implies -a).")
@click.option("-p", "--show-pen-up", is_flag=True, help="Show pen-up trajectories.")
@click.option("-h", "--hide-legend", is_flag=True, help="Do not display the legend.")
@click.option(
    "-c", "--colorful", is_flag=True, help="Display each segment in a different color."
)
@click.option(
    "-u",
    "--unit",
    type=str,
    default="px",
    help="Units of the plot (when --show-grid is active)",
)
@global_processor
def show(
    vector_data: VectorData,
    show_axes: bool,
    show_grid: bool,
    show_pen_up: bool,
    hide_legend: bool,
    colorful: bool,
    unit: str,
):
    """
    Display the geometry using matplotlib.

    By default, only the geometries are displayed without the axis. All geometries are
    displayed with black. When using the `--colorful` flag, each segment will have a different
    color (default matplotlib behaviour). This can be useful for debugging purposes.
    """

    scale = 1 / convert(unit)

    fig = plt.figure()
    color_idx = 0
    collections = {}
    for layer_id, lc in vector_data.layers.items():
        if colorful:
            color = COLORS[color_idx:] + COLORS[:color_idx]
            color_idx += len(lc)
        else:
            color = COLORS[color_idx]
            color_idx += 1
        if color_idx >= len(COLORS):
            color_idx = color_idx % len(COLORS)

        collections[layer_id] = matplotlib.collections.LineCollection(
            (as_vector(line) * scale for line in lc),
            color=color,
            lw=1,
            alpha=0.5,
            label=str(layer_id),
        )
        plt.gca().add_collection(collections[layer_id])

        if show_pen_up:
            plt.gca().add_collection(
                matplotlib.collections.LineCollection(
                    (
                        (as_vector(lc[i])[-1] * scale, as_vector(lc[i + 1])[0] * scale)
                        for i in range(len(lc) - 1)
                    ),
                    color=(0, 0, 0),
                    lw=0.5,
                    alpha=0.5,
                )
            )

    plt.gca().invert_yaxis()
    plt.axis("equal")
    plt.margins(0, 0)

    if not hide_legend:
        lgd = plt.legend()
        # we will set up a dict mapping legend line to orig line, and enable
        # picking on the legend line
        line_dict = {}
        for lgd_line, lgd_text in zip(lgd.get_lines(), lgd.get_texts()):
            lgd_line.set_picker(5)  # 5 pts tolerance
            layer_id = int(lgd_text.get_text())
            if layer_id in collections:
                line_dict[lgd_line] = collections[layer_id]

        def on_pick(event):
            line = event.artist
            vis = not line_dict[line].get_visible()
            line_dict[line].set_visible(vis)

            if vis:
                line.set_alpha(1.0)
            else:
                line.set_alpha(0.2)
            fig.canvas.draw()

        fig.canvas.mpl_connect("pick_event", on_pick)

    if show_axes or show_grid:
        plt.axis("on")
        plt.xlabel(f"[{unit}]")
        plt.ylabel(f"[{unit}]")
    else:
        plt.axis("off")
    if show_grid:
        plt.grid("on")
    plt.show()

    return vector_data
