import numpy as np
from datetime import datetime


class Beacon:
    # edw ftiaxe list of beacons!!
    def __init__(self, transmit_power, coordinates,floor):
        self.transmit_power = transmit_power
        self.coordinates = np.array(coordinates)
        self.floor = floor
        self.time_spent = {}
        self.enter_time = {}
        self.exit_time = {}
        self.user_time ={}
        self.path_loss_exponent = 2.0
        # for beacon in beacons :
        # add_beacon(beacon)

    def add_beacon(beacon):
        pass

    def enter(self, user_id):
        self.enter_time[user_id] = datetime.now()

    def exit(self, user_id):
        self.exit_time[user_id] = datetime.now()
        time_spent = (
            self.exit_time[user_id] - self.enter_time[user_id]
        ).total_seconds()
        self.time_spent[user_id] = self.time_spent.get(user_id, 0) + time_spent

    def get_time_spent(self):
        for user_id in list(self.enter_time.keys()):
            time_spent = (datetime.now() - self.enter_time[user_id]).total_seconds()
            self.time_spent[user_id] = self.time_spent.get(user_id, 0) + time_spent
            self.enter_time[user_id] = datetime.now()  # Update last update time

        return self.time_spent

    def find_beacon():
        """
         coverage_radius = np.sqrt(
            10
            ** (
                (transmit_power - (-10 * path_loss_exponent * np.log10(1)))
                / (10 * path_loss_exponent)
            )
        )
        """
        pass

    def in_beacon(self, x, y):
        radius = np.sqrt(
            10
            ** (
                (self.transmit_power - (-10 * self.path_loss_exponent * np.log10(1)))
                / (10 * self.path_loss_exponent)
            )
        )
        distance = np.linalg.norm(self.coordinates - np.array([x, y]))
        return distance <= radius
    """
        def detect_user(self, user_id, user_position):
            if self.in_beacon(user_position[0], user_position[1]):
                if user_id not in self.enter_time:
                    self.enter(user_id)
            else:
                if user_id in self.enter_time:
                    self.exit(user_id)
                    del self.enter_time[user_id]


    """
    def detect_user(self, user_id, user_position):
        if self.in_beacon(user_position[0], user_position[1]):
            if user_id not in self.enter_time:
                self.enter_time[user_id] = datetime.now()
        else:
            if user_id in self.enter_time:
                time_spent = (datetime.now() - self.enter_time[user_id]).total_seconds()
                self.time_spent[user_id] = self.time_spent.get(user_id, 0) + time_spent
                del self.enter_time[user_id]
