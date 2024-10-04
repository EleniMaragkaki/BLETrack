
from __future__ import absolute_import, unicode_literals
from celery import shared_task,Celery
import time
import os
from datetime import datetime
import numpy as np
from .particle_filtering import particle_filter, calculate_rss2, motion_model, json_floor_plan
import random

#app = Celery('indoorTrackingProject')

@shared_task
def initialize_user_tracking():
    from .models import User, Beacon  
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_file = os.path.join(base_dir, 'navigation', 'static', "json_data",'floor_plan.json')
        floor_plan = json_floor_plan(json_file)

        user_paths = {
        "MAC_ID1": [
             (2.0, 3.3716, 0.0),  (2.34375, 3.2808, 0.0),  (2.6875, 2.9915, 0.0),  (3.03125, 3.1692, 0.0),  (3.375, 3.2073, 0.0),  (3.61875, 3.0041, 0.0),  (4.0625, 3.1910, 0.0),  (4.40625, 3.3980, 0.0),  (4.75, 3.0158, 0.0),  (5.09375, 3.2852, 0.0),  (5.4375, 3.3864, 0.0),  (5.78125, 3.2323, 0.0),  (6.125, 3.2958, 0.0),  (6.46875, 3.1459, 0.0),  (6.8125, 3.0616, 0.0),  (7.15625, 3.1941, 0.0),  (7.5, 3.2107, 0.0)
            ],

        }
            

        for username, path in user_paths.items():
    
            user,created = User.objects.get_or_create(username=username)
            user.clear_active_data()
            print("after clear",user.path)
            user.random_path(path=path, step_size=0.4, floor_plan=floor_plan)
            print("after random path",user.path)

            user.set_active()
            user.save()
        
        weights = np.ones(300)/ 300
        while User.objects.filter(active=True).exists():
            
            user = User.objects.select_for_update().filter(active=True).order_by('?').first()
            user.refresh_from_db() 
            start_step = datetime.now()
            step_indx=user.get_step_pointer()
            if(step_indx<len(user.get_path())):
                real_pos=user.get_path()[step_indx]
                if(step_indx==0):
                    start_step = datetime.now()
                    user.first_step = datetime.now()
                    user.save()
                    prev_position = real_pos
                else:
                    prev_position = user.estimated_path[-1]
                initial_particles = motion_model(
                    num_particles=300, prev_position=prev_position, floor_plan=floor_plan
                )
                particles, weights = particle_filter(
                        initial_particles,
                        weights,
                        calculate_rss2(floor_plan, real_pos),
                        floor_plan,
                    )
                estimated_position = user.get_path()[step_indx]
                user.estimated_path.append(estimated_position)
                user.save()
                prev_position = estimated_position
                beacons = Beacon.objects.filter(beacon_id__in=floor_plan[estimated_position[2]]["beacons"])
                for beacon in beacons:
                    beacon.detect_user(user.username, estimated_position)
                    beacon.save()
                    time.sleep(np.random.uniform(0.3,0.6))
                end_step = datetime.now()
                time_spent = (end_step - start_step).total_seconds()
                user.update_time_spent(prev_position, time_spent)
                user.save() 
                start_step = end_step
                step_indx += 1
                user.set_step_pointer(step_indx)
                user.save() 
                user.refresh_from_db() 

            else:
                user.unset_active()  
                user.add_visit(user.first_step, datetime.now()) 
                user.clear_active_data()
                user.save()
        return None 
    except Exception as e:
        print(f"Error in initialize_user_tracking task: {e}")
        print("Telos users.")
        return None

"""
user step pointers : gia na exw access se poio user anaferomai kathe fora
while loop pou kalei tis aparaitites synartiseis gia na kanei particle filtering, 
se kathe loopa ginetai update to estimated path gia kapoion xristi
"""
"""
def setup_periodic_tasks(sender, **kwargs):
    sender.initialize_user_tracking.delay()

if __name__ == '__main__':
    app.start()

"""
