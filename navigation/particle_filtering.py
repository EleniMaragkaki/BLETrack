import numpy as np
from scipy.stats import norm
import json
from shapely.geometry import Point, Polygon, LineString
from .models import Beacon

num_particles = 300
transmit_power = 8
# vathmos pou meiwnetai to signal strength me tin apostasi
path_loss_exponent = 2.0
# deviation logo perivallontos etc
measurement_noise = 0.1
# initial_particles = np.random.uniform(low=[0, 0], high=[9, 7], size=(num_particles, 2))
weights = np.ones(num_particles) / num_particles


def calculate_rss2(
    floor_plan,
    user_position,
):
    rss_values = []
    floor = user_position[2]
    beacons = Beacon.objects.filter(beacon_id__in=floor_plan[floor]["beacons"])
    for beacon in  beacons:
        if beacon.floor == floor:
            # euclidean distance of the user position and beacon
            distance = np.linalg.norm(user_position[:2] - np.array(beacon.coordinates))
            #rss = beacon.transmit_power - path_loss 
            rss = beacon.transmit_power - (
                10 * beacon.path_loss_exponent * np.log10(distance)
            )
            # rss += random noise
            rss += np.random.normal(scale=measurement_noise)
            rss_values.append(rss)
    return rss_values


def json_floor_plan(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)

    floor_plan = {}
    for floor_number, floor_data in data.items():
        floor_number = int(floor_number)
        rooms = [np.array(room) for room in floor_data.get("rooms", [])]
        corridors = [np.array(corridor) for corridor in floor_data.get("corridors", [])]
        entrance = np.array(floor_data.get("entrance", []))
        doors = {key: np.array(value) for key, value in floor_data.get("doors", {}).items()}
        beacon_data = floor_data.get("beacons", [])
        beacons = []
        for beacon in beacon_data:
            transmit_power = beacon["transmit_power"]
            coordinates = np.array(beacon["coordinates"]).tolist()
            beacon_exists = Beacon.objects.filter(coordinates=coordinates, floor=floor_number).first()

            if beacon_exists:
                beacons.append(beacon_exists.beacon_id)
            else:
                new_beacon = Beacon.add_beacon(transmit_power, coordinates, floor_number)
                beacons.append(new_beacon.beacon_id)
        stairs = [
            {
                "coordinates": np.array(stair["coordinates"]),
                "from_floor":int(stair["from_floor"]),
                "to_floor": int(stair["to_floor"]),
                "to_coordinates":np.array(stair["to_coordinates"])
            }
            for stair in floor_data.get("stairs", [])
        ]

        floor_plan[floor_number] = {
            "rooms": rooms,
            "corridors": corridors,
            "entrance": entrance,
            "doors": doors,
            "beacons": beacons,
            "stairs": stairs
        }

    return floor_plan



def is_valid_particle(x, y, z,prev_position, floor_plan):
    rooms = floor_plan[z].get("rooms", [])
    corridors = floor_plan[z].get("corridors", [])
    doors = floor_plan[z].get("doors", {})
    stairs = floor_plan[z].get("stairs", [])

    point = Point(x, y)
    prev_point = Point(prev_position[0], prev_position[1])
    movement_line = LineString([prev_point, point])
    for room in rooms:
        room_polygon = Polygon(room)
        if room_polygon.contains(point):
            # an kai to prev position einai mesa sto dwmatio ola ok
            if room_polygon.contains(prev_point):
                return True
    for corridor in corridors:
        corr_polygon = Polygon(corridor)
        if corr_polygon.contains(point):
            if corr_polygon.contains(prev_point):
                return True
    for corridor in corridors:
        corr_polygon = Polygon(corridor)
        if corr_polygon.contains(point):
            if corr_polygon.contains(prev_point):
                return True
    # else it must pass through a door
    for door in doors.values():
        door_line = LineString(door)
        if (
            movement_line.intersects(door_line)
            or door_line.contains(point)
            or door_line.contains(prev_point)
        ):
            return True

    for stair in stairs:
        stair_polygon = Polygon(stair["coordinates"])
        if stair_polygon.contains(point) :
            return True

    return False



def motion_model(num_particles, prev_position, floor_plan):
    # scale = apoklisi gauss
    # edw kanw add to wall constraint
    # array me ta walls , prin epistrepsw ta particles kalw synartisi pou
    # chekarei ama einai mesa sta constraint. an oxi weights[i] = 0
    # paragw kainouio rand
    # particles[:, 0] += np.random.normal(scale=0.01, size=num_particles)
    # particles[:, 1] += np.random.normal(scale=0.01, size=num_particles)
    # return particles
    new_particles = []
    for i in range(num_particles):
        valid_particle = False
        new_particle = np.array(
            [
                prev_position[0] + np.random.normal(scale=0.1),
                prev_position[1] + np.random.normal(scale=0.1),
                prev_position[2]
            ]
        )

        # valid_particle = is_valid_particle(
        #     new_particle[0], new_particle[1],new_particle[2], prev_position, floor_plan
        # )
        # if ( not valid_particle ) :
        #     weights[i]=0

        # #checking if i need to change floor
        # #prepei na to allaksw na allazw ama vriskw shma ston allo orofo
        # stairs = floor_plan[prev_position[2]].get("stairs", [])
        # for stair in stairs:
        #     stair_polygon = Polygon(stair["coordinates"])
        #     if stair_polygon.contains(Point(new_particle[0], new_particle[1])):
        #         new_particle[2] = stair["to_floor"]
        #         new_particle[0], new_particle[1]= stair["to_coordinates"]
        #         break

        new_particles.append(new_particle)
        valid_particle = True
    return np.array(new_particles)


def particle_filter(particles, weights, user_rss,floor_plan):
    # update
    for i in range(num_particles):
        particle_rss = calculate_rss2(floor_plan, particles[i])
        likelihood = 1
        for user_measurement, particle_measurement in zip(user_rss, particle_rss):
            # probability density function, loc = expected
            pdf = norm.pdf(
                particle_measurement, loc=user_measurement, scale=measurement_noise
            )
            likelihood *= pdf
        # updating the weight based on pdf
        weights[i] *= likelihood

    if np.sum(weights) == 0:
        weights = np.ones(num_particles) / num_particles
    else:
        # normalize weights
        weights /= np.sum(weights)

    # resample particles
    # ta particles me to megalytero varos einai pio pithano na epilextoun
    resample = np.random.choice(range(num_particles), size=num_particles, p=weights)
    particles = particles[resample]

    # ta varh ginontai isa gia epomeno iteration
    weights = np.ones(num_particles) / num_particles

    return particles, weights

