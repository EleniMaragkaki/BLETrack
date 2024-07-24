import numpy as np
from shapely.geometry import Point, Polygon, LineString


class User:

    def __init__(self, id):
        self.id = id
        self.path = []
        self.estimated_path = []
        self.time_spent = {}

    def get_id(self):
        return self.id

    """
    given some points in the floor plan it connects them and creates a user path
    given a step size. it takes into account the wall constraints
    """

    def random_path(self, path, step_size, floor_plan):
        new_path = []
        floor = 0 #panta mpainoume apo ton 0 orofo
        for i in range(len(path) - 1):
            x1, y1,z1 = path[i]
            x2, y2,z2 = path[i + 1]
            distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            num_steps = int(distance / step_size)
            if num_steps == 0:
                new_path.append((x1, y1,z1))
            else:
                add_x = (x2 - x1) / num_steps
                add_y = (y2 - y1) / num_steps
                for j in range(num_steps):
                    new_x = x1 + j * add_x
                    new_y = y1 + j * add_y
                    new_z = z1
                    while not is_valid_step(new_x, new_y,new_z, path[i], floor_plan):
                        new_x = new_x + np.random.normal(scale=0.1)
                        new_y = new_y + np.random.normal(scale=0.1)
                    #an allaksei orofo
                    stairs= floor_plan[new_z].get("stairs", [])
                    for stair in stairs :
                        stair_polygon = Polygon(stair["coordinates"])
                        if stair_polygon.contains(Point(new_x, new_y)):
                            print(f"stair contains newx,newy in user rand path")
                            print(f"new x,y = {stair["to_coordinates"]}, new z={stair["to_floor"]} ")

                            current_floor = stair["to_floor"]
                            new_x, new_y = stair["to_coordinates"]
                            new_z = current_floor
                            break
                    new_path.append((new_x, new_y,new_z))
                    
        # new_path = new_path[:-1]

        self.path = new_path

    def get_path(self):
        return self.path

    def get_estimated_path(self):
        return self.estimated_path

    def get_time_spent(self):
        return self.time_spent

    def update_time_spent(self,position,time_spent):
        position_tuple = tuple(position)
        self.time_spent[position_tuple] =  time_spent
"""
function that checks if the current step is ok with the wall constraints
returns true if ok
false if not
"""


def is_valid_step(x, y,z, prev_position, floor_plan):
    rooms = floor_plan[z].get("rooms", [])
    corridors = floor_plan[z].get("corridors", [])
    doors = floor_plan[z].get("doors", [])
    stairs = floor_plan[z].get("stairs", [])


    point = Point(x, y)
    if prev_position is not None:
        prev_point = Point(prev_position[0], prev_position[1])
        movement_line = LineString([prev_point, point])
    else:
        prev_point = None
        movement_line = LineString([point])
    for room in rooms:
        room_polygon = Polygon(room)
        if room_polygon.contains(point):
            if room_polygon.contains(prev_point):
                return True
            """
    for corridor in corridors:
        corr_polygon = Polygon(corridor)
        if corr_polygon.contains(point):
            if corr_polygon.contains(prev_point):
                return True
            """
    for corridor in corridors:
        corr_polygon = Polygon(corridor)
        if corr_polygon.contains(point):
            return True
    for door in doors.values():
        door_line = LineString(door)
        if (
            movement_line.intersects(door_line)
            or door_line.contains(point)
            or door_line.contains(prev_point)
        ):
            return True
    for stair in stairs:
        #SOS tsekare to isws einai lathos
        stair_polygon = Polygon(stair["coordinates"])
        if stair_polygon.contains(point):
            return True
    return False
