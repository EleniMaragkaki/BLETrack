import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import mplcursors
from shapely.geometry import  Polygon,  MultiPolygon, MultiPoint
from scipy.stats import gaussian_kde
from matplotlib.gridspec import GridSpec

def area_coverage(users, floor_plan):
    total_area = 0
    covered_area = 0
    # Multipolygon gia ta rooms kai corridors
    for floor_number, floor_data in floor_plan.items():
        floor_plan_polygons = MultiPolygon(
            [Polygon(room) for room in floor_data["rooms"]]
            + [Polygon(corridor) for corridor in floor_data["corridors"]]
        )
        # multipoint: exei ola ta visited shmeia apo users
        visited_points = MultiPoint(
            [point for user in users.values() for point in user['estimated_path'] if point[2] == floor_number]
        )

        # buffarw to kathe point
        visited_points = visited_points.buffer(0.2)

        # pairnw to intersection twn points me to floor plan gt meta to buffering
        # mporei na exw shmeia ektos
        visited_points = visited_points.intersection(floor_plan_polygons)

        covered_area += visited_points.area

        total_area += floor_plan_polygons.area

    return covered_area / total_area
def init_plot(floor_num):

    fig = plt.figure(figsize=(12, 8))

    gs = GridSpec(5, 2, width_ratios=[2, 1], hspace=0.3)

    ax_floors = []

    ax_floors.append(fig.add_subplot(gs[0:2, 0]))
    ax_floors.append(fig.add_subplot(gs[3:5, 0]))


    ax_traffic = fig.add_subplot(gs[0, 1])      # Traffic subplot
    ax_visitors = fig.add_subplot(gs[2, 1])     # Visitors subplot 
    ax_coverage = fig.add_subplot(gs[4, 1])     # Coverage subplot 

    if floor_num == 1:
        ax_floors = [ax_floors]

    return ax_floors, ax_coverage, ax_traffic, ax_visitors, fig


def traffic_volume(ax_traffic):

    # traffic volume
    traffic_volume = {
        "Monday": 10,
        "Tuesday": 22,
        "Wednesday": 18,
        "Thursday": 25,
        "Friday": 32,
        "Saturday": 29,
    }
    days = list(traffic_volume.keys())
    volumes = list(traffic_volume.values())
    ax_traffic.barh(days, volumes, color="#f8766d")
    # ax_traffic.set_xlabel("Traffic Volume", fontsize=12)
    ax_traffic.set_title("Traffic Volume", fontsize=14)


def visitors_num(users, ax_visitors):
    # number of visitors
    num_visitors = len(users)
    ax_visitors.text(
        0.5,
        0.5,
        f"{num_visitors}",
        ha="center",
        va="center",
        fontsize=12,
        transform=ax_visitors.transAxes,
        bbox=dict(facecolor="white", alpha=0.8),
    )
    ax_visitors.axis("off")
    ax_visitors.set_title("Visitors", fontsize=14)


def area_coverage_pie(users, floor_plan, ax_coverage):
    # area coverage
    area_covered = area_coverage(users, floor_plan)
    data = [1 - area_covered, area_covered]
    labels = ["Uncovered", "Covered"]
    colors = ["#00bfc4", "#f8766d"]
    ax_coverage.pie(
        data,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=140,
        radius=0.8,
    )

    ax_coverage.set_title("Area Coverage", fontsize=14)
    ax_coverage.axis("equal")


def time_heatmap(
    users, floor_plan, ax_floors, ax_traffic, ax_visitors, ax_coverage, cbar1,cbar2
):
    for ax in ax_floors:
        ax.clear()
    ax_traffic.clear()
    ax_visitors.clear()
    ax_coverage.clear()
    for floor_number, ax in enumerate(ax_floors):
            x_coords = []
            y_coords = []
            time_weights = []
            floor_data = floor_plan[floor_number]

            x_min = min([x for room in floor_data["rooms"] for x, y in room])
            x_max = max([x for room in floor_data["rooms"] for x, y in room])
            y_min = min([y for room in floor_data["rooms"] for x, y in room])
            y_max = max([y for room in floor_data["rooms"] for x, y in room])

            for user in users.values():
                time_spent = user.get_time_spent()
                for (x, y, z), time in time_spent.items():
                    if z == floor_number:
                        x_coords.append(x)
                        y_coords.append(y)
                        time_weights.append(time)

            if len(x_coords) > 2 and len(y_coords) > 1 and np.std(time_weights) > 0:
                grid_x, grid_y = np.mgrid[x_min:x_max:100j, y_min:y_max:100j]
                positions = np.vstack([grid_x.ravel(), grid_y.ravel()])
                values = np.vstack([x_coords, y_coords])
                kernel = gaussian_kde(values, weights=time_weights)
                density = np.reshape(kernel(positions).T, grid_x.shape)

                ax.imshow(np.rot90(density), cmap='rainbow', extent=[x_min, x_max, y_min, y_max], aspect='auto', interpolation='bilinear')

                norm = Normalize(vmin=np.min(density*10), vmax=np.max(density*10))
                sm = ScalarMappable(norm=norm, cmap="rainbow")
                sm.set_array([])
                if floor_number == 0:
                    if cbar1 is None:
                        cbar1 = plt.colorbar(sm, ax=ax, fraction=0.046)
                        cbar1.set_label("Time Spent - Floor 1")
                    else:
                        cbar1.update_normal(sm)
                elif floor_number == 1:
                        if cbar2 is None:
                            cbar2 = plt.colorbar(sm, ax=ax, fraction=0.046)
                            cbar2.set_label("Time Spent - Floor 2")
                        else:
                            cbar2.update_normal(sm)

            for rooms in floor_data["rooms"]:
                rooms = np.array(rooms)
                ax.plot(rooms[:, 0], rooms[:, 1], "k-")

            for entrance in floor_data.get("entrance", []):
                entrance = np.array(entrance)
                ax.plot(entrance[:, 0], entrance[:, 1], "white", linewidth=2)

            for door in floor_data["doors"].values():
                door = np.array(door)
                ax.plot(door[:, 0], door[:, 1], "white", linewidth=2)

            for beacon in floor_data.get("beacons", []):
                print(f"beacon coords = {beacon.coordinates}")
                ax.scatter(beacon.coordinates[0], beacon.coordinates[1], color="magenta", marker="o")
            for user in users.values():
                estimated_path = user.estimated_path
                for i in range(len(estimated_path) - 1):
                    if estimated_path[i][2] == floor_number:
                        ax.plot(
                            [estimated_path[i][0], estimated_path[i + 1][0]],
                            [estimated_path[i][1], estimated_path[i + 1][1]],
                            "white",
                            linewidth=1.5,
                        )

            ax.set_title(f"Heatmap - Floor {floor_number}", fontsize=16)
            ax.set_xlabel("X", fontsize=14)
            ax.set_ylabel("Y", fontsize=14)

            ax.set_xlim(x_min , x_max)
            ax.set_ylim(y_min , y_max)
            ax.set_aspect("equal", adjustable="box")
            ax.plot([], [], "r-", label="Estimated Path")
            ax.legend(loc="upper right", fontsize=12)
    # traffic volume
    traffic_volume(ax_traffic)

    # number of visitors
    visitors_num(users, ax_visitors)

    # area coverage
    area_coverage_pie(users, floor_plan, ax_coverage)

    plt.tight_layout()
    # plt.show()
    return cbar1,cbar2


def coverage_area(floor_plan, transmit_power, path_loss_exponent):

    fig, ax = plt.subplots(figsize=(8, 6))

    for rooms in floor_plan["rooms"]:
        rooms = np.array(rooms)
        ax.plot(rooms[:, 0], rooms[:, 1], "k-")

    for entrance in floor_plan["entrance"]:
        entrance = np.array(entrance)
        ax.plot(entrance[:, 0], entrance[:, 1], "b-", linewidth=2)

    for door in floor_plan["doors"].values():
        door = np.array(door)
        ax.plot(door[:, 0], door[:, 1], "b-", linewidth=2)

    access_points = floor_plan["access_points"]
    for ap in access_points:
        ap = np.array(ap)
        ax.scatter(ap[0], ap[1], color="magenta", marker="o")
        mplcursors.cursor(ax.scatter(ap[0], ap[1], color="magenta", marker="o"))

        coverage_radius = np.sqrt(
            10
            ** (
                (transmit_power - (-10 * path_loss_exponent * np.log10(1)))
                / (10 * path_loss_exponent)
            )
        )

        circle = plt.Circle((ap[0], ap[1]), coverage_radius, color="blue", alpha=0.2)
        ax.add_patch(circle)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Coverage Area")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True)
    plt.show()


