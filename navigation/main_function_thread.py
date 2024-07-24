
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
        print(f"paw na kanw run!")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_file = os.path.join(base_dir, 'navigation', 'static', "json_data",'floor_plan.json')
        floor_plan = json_floor_plan(json_file)

        user_paths = {
        "MAC_ID1": [
                (4.4, 6.9,0),
                (4.51, 6.1,0),
                (5.1, 6,0),
                (5.6, 5.8,0),
                (5.7, 5.2,0),
                (5.7, 4.9,0),
                (5.7, 4,0),
                (5.6, 3.5,0),
                (5.5, 3,0),
                (5.4, 2.5,0),
                (5.3, 2,0),
                (5.3, 1.5,0),
                (5.2, 1.1,0),
                (4.8, 1.6,0),
                (3, 1.5,0),
                (1, 2,0),
                (0.8, 2.8,0),
                (0.8, 3.8,0),
                (2.5, 3.6,0),
                (2.5, 4.6,0),
                (1, 5.5,0),
                (3.6, 5.1,0),
                (4.3, 5.1,0),
                (4.1, 6.9,0),
            ],
            "MAC_ID2": [
                (4.2, 6.85,0),
                (4.15, 6.1,0),
                (4.2, 5.5,0),
                (3.5, 5.2,0),
                (2.5, 4.3,0),
                (3.3, 5,0),
                (4.4, 5.5,0),
                (4.8, 6.7,0),
            ],
            "MAC_ID3": [(4.5, 6.8,0), (4.6, 6.2,0), (6.5, 5.9,0), (8.5, 4.2,0), (7.6, 1,0)],
            
            "MAC_ID4": [(4.6, 6.82,0), (4.5, 5,0), (4.5, 3.5,0),(4.5, 3,0),(4.5, 2.5,0),(4.3, 1.8,0), (3.8, 1.8,0),(3.2, 1.5,0), (2.5, 1.5, 0),(1.98, 0.9, 0),(2.06, 0.6, 1),(2.5, 1, 1),(2.9,1, 1),(3.2,1.5,1),(4.5,2,1)]
        }
            

        for username, path in user_paths.items():
    
            user,created = User.objects.get_or_create(username=username)
            user.clear_active_data()
            user.random_path(path=path, step_size=0.1, floor_plan=floor_plan)
            user.set_active()
            user.save()
            print(f"ekana user save!")
        
        enter_time={}
        weights = np.ones(300)/ 300
        while User.objects.filter(active=True).exists():
            
            print(f"eimai while!")
            user = User.objects.filter(active=True).order_by('?').first()
            start_step = datetime.now()
            step_indx=user.get_step_pointer()
            if(step_indx<len(user.get_path())):
                real_pos=user.get_path()[step_indx]
                if(step_indx==0):
                    start_step = datetime.now()
                    enter_time[user.username] = datetime.now()
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
                estimated_position = particles[np.argmax(weights)]
                user.estimated_path.append(estimated_position.tolist())
                user.save()
                prev_position = estimated_position
                beacons = Beacon.objects.filter(beacon_id__in=floor_plan[estimated_position[2]]["beacons"])
                for beacon in beacons:
                    beacon.detect_user(user.username, estimated_position)
                    beacon.save()
                    time.sleep(np.random.uniform(0.05,0.20))
                end_step = datetime.now()
                time_spent = (end_step - start_step).total_seconds()
                user.update_time_spent(prev_position.tolist(), time_spent)
                user.save() 
                start_step = end_step
                step_indx += 1
                user.set_step_pointer(step_indx)
                user.save() 
            else:
                print(f"antio user !")
                user.unset_active()  
                user.add_visit(start_step, datetime.now()) 
                user.clear_active_data()
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
