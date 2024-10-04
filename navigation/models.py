from django.db import models
import numpy as np
from shapely.geometry import Point, Polygon, LineString
from datetime import datetime

class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255)
    path = models.JSONField(default=list)
    estimated_path = models.JSONField(default=list)
    time_spent = models.JSONField(default=dict) 
    active = models.BooleanField(default=False) 
    past_visits = models.JSONField(default=list)  
    step_pointer = models.IntegerField(default=0)
    first_step=models.DateTimeField(default=datetime.now)

    def set_step_pointer(self, pointer):
        self.step_pointer = pointer
        self.save()

    def get_step_pointer(self):
        return self.step_pointer
    def __str__(self):
        return self.username
    
    def set_active(self):
        self.active = True
        self.save()

    def unset_active(self):
        self.active = False
        self.save()

    def add_visit(self, enter_time, exit_time):
        self.past_visits.append({
            'enter_time': enter_time.isoformat(),
            'exit_time': exit_time.isoformat()
        })
        self.save()

    def clear_active_data(self):
        self.path = []
        self.step_pointer=0
        self.estimated_path = []
        self.time_spent = {}
        self.save()
        
    def is_valid_step(self,x, y,z, prev_position, floor_plan):
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
      
        for corridor in corridors:
            corr_polygon = Polygon(corridor)
            if corr_polygon.contains(point):
                if corr_polygon.contains(prev_point):
                    return True
      
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
            stair_polygon = Polygon(stair["coordinates"])
            if stair_polygon.contains(point):
                return True
        return False

    def random_path(self, path, step_size, floor_plan):
        new_path = []
        floor = 0 
        for i in range(len(path) - 1):
            x1, y1, z1 = path[i]
            x2, y2, z2 = path[i + 1]
            distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            num_steps = int(distance / step_size)
            if num_steps == 0:
                new_path.append((x1, y1, z1))
            else:
                add_x = (x2 - x1) / num_steps
                add_y = (y2 - y1) / num_steps
                for j in range(num_steps):
                    new_x = x1 + j * add_x
                    new_y = y1 + j * add_y
                    new_z = z1
                    while not self.is_valid_step(new_x, new_y, new_z, path[i], floor_plan):
                        new_x += np.random.normal(scale=0.1)
                        new_y += np.random.normal(scale=0.1)
                    stairs = floor_plan[new_z].get("stairs", [])
                    for stair in stairs:
                        stair_polygon = Polygon(stair["coordinates"])
                        if stair_polygon.contains(Point(new_x, new_y)):
                            new_x, new_y = stair["to_coordinates"]
                            new_z = stair["to_floor"]
                            z1= new_z
                            break
                    new_path.append((new_x, new_y, new_z))
        self.path = new_path
    
    def get_path(self):
        return self.path

    def get_estimated_path(self):
        return self.estimated_path

    def get_time_spent(self):
        return self.time_spent

    def update_time_spent(self, position, time_spent):
        position_key  = str(position)
        self.time_spent[position_key] = self.time_spent.get(position_key, 0) + time_spent
    def get_id(self):
        return self.id
    
class Beacon(models.Model):
    beacon_id = models.AutoField(primary_key=True)
    transmit_power = models.FloatField()
    coordinates = models.JSONField()
    floor = models.IntegerField()
    time_spent = models.JSONField(default=dict)
    enter_time = models.JSONField(default=dict)
    exit_time = models.JSONField(default=dict)
    user_time = models.JSONField(default=dict)
    path_loss_exponent = 2.0

    def __str__(self):
        return f'Beacon {self.beacon_id} on floor {self.floor}'
    def add_beacon(beacon):
        pass
    @classmethod
    def add_beacon(cls, transmit_power, coordinates, floor_number):
        beacon = cls(transmit_power=transmit_power, coordinates=coordinates, floor=floor_number)
        beacon.save()
        return beacon

    def enter(self, user_id):
        self.enter_time[user_id] = datetime.now().isoformat()

    def exit(self, user_id):
        self.exit_time[user_id] = datetime.now().isoformat()
        enter_time = datetime.fromisoformat(self.enter_time[user_id])
        time_spent = (datetime.now() - enter_time).total_seconds()
        self.time_spent[user_id] = self.time_spent.get(user_id, 0) + time_spent

    def get_time_spent(self):
        for user_id in list(self.enter_time.keys()):
            enter_time = datetime.fromisoformat(self.enter_time[user_id])
            time_spent = (datetime.now() - enter_time).total_seconds()
            self.time_spent[user_id] = self.time_spent.get(user_id, 0) + time_spent
            self.enter_time[user_id] = datetime.now().isoformat()
        return self.time_spent



    def in_beacon(self, x, y):
        radius = np.sqrt(
            10
            ** (
                (self.transmit_power - (-10 * self.path_loss_exponent * np.log10(1)))
                / (10 * self.path_loss_exponent)
            )
        )
        distance = np.linalg.norm(self.coordinates - np.array([x, y]))
        return (distance <= radius)

    """
    If the user is in the radius of the beacon: 
        If the user was not already in the beacon (in his previous step), 
            his enter time is updated based on the current time
    Else, if the user is in the time spent dictionary (but has left the beacon radius),
        his time spent in the beacon is being updated by the 
        addition of his prev time spent in the beacon plus the time he spent this time
        (of his enter_time - exit_time (current time)) 
        the user is then deleted from the dict enter_time.
    """
    def detect_user(self, user_id, user_position):
        if self.in_beacon(user_position[0], user_position[1]):
            if user_id not in self.enter_time:
                self.enter_time[user_id] = datetime.now().isoformat()
        else:
            if user_id in self.enter_time:
                enter_time = datetime.fromisoformat(self.enter_time[user_id])
                time_spent = (datetime.now() - enter_time).total_seconds()
                self.time_spent[user_id] = self.time_spent.get(user_id, 0) + time_spent
                del self.enter_time[user_id]

    
    def to_dict(self):
        return {
            'beacon_id': self.beacon_id,
            'transmit_power': self.transmit_power,
            'coordinates': self.coordinates,
            'floor': self.floor,
            'time_spent': self.time_spent,
            'enter_time': self.enter_time,
            'exit_time': self.exit_time,
            'user_time': self.user_time
        }