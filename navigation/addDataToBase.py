from .models import User, Beacon  
import os
from datetime import datetime
import numpy as np
import time
from .particle_filtering import json_floor_plan

#TODO start kai end time? apo request h edw?
def addDataToBase(user,currStep):
    start_step = datetime.now()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_file = os.path.join(base_dir, 'navigation', 'static', "json_data",'floor_plan.json')
    floor_plan = json_floor_plan(json_file)
    beacons = Beacon.objects.filter(beacon_id__in=floor_plan[currStep[2]]["beacons"])
    for beacon in beacons:
        beacon.detect_user(user.username, currStep)
        beacon.save()
        time.sleep(np.random.uniform(0.05,0.20))
    end_step = datetime.now()
    time_spent = (end_step - start_step).total_seconds()
    user.update_time_spent(currStep.tolist(), time_spent)
    user.save() 
    start_step = end_step
    #gia na dw se poio vima einai ama thelw na termatisw thn kinhsh--de xreiazetai
    step_indx += 1
    user.set_step_pointer(step_indx)
    user.save() 
"""
    else:
    user.unset_active()  
    user.add_visit(start_step, datetime.now()) 
    user.clear_active_data()
"""
