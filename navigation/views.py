# views.py
import os
from django.shortcuts import render
from .particle_filtering import json_floor_plan
from .models import User , Beacon
from datetime import datetime
import numpy as np
import time
import matplotlib.pyplot as plt
from .plots import area_coverage
from django.http import JsonResponse
import json
from django.shortcuts import render
import threading
from collections import Counter, defaultdict
from .main_function_thread import initialize_user_tracking
from django.db import transaction
user_lock = threading.Lock()
beacon_lock = threading.Lock()

def home(request):
    initialize_user_tracking.delay()
    return render(request, 'navigation/index.html')


"""epistrefei ta user paths apo db
"""
def get_user_paths(request):
    
    with user_lock:
        users = User.objects.all()
        user_data = {}
        for user in users:
            user_data[user.username] = {
                'user_id': user.username,
                'path': user.get_path(),
                'estimated_path': user.get_estimated_path(),
                'time_spent': user.get_time_spent()
            }
    return JsonResponse(user_data)
def get_heatmap_data(request):
    floor = request.GET.get('floor')
    floor = int(floor)
    with beacon_lock:
        beacons = Beacon.objects.filter(floor=floor)
        heatmap_data = []

        for beacon in beacons:
            x, y = beacon.coordinates[0], beacon.coordinates[1]
            total_beacon_time_spent = sum(beacon.time_spent.values())
            heatmap_data.append({
                'x': x*100,
                'y': (7-y)*100,
                'value': total_beacon_time_spent
            })

        return JsonResponse({'data': heatmap_data})
def get_floor_plan(request):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_file = os.path.join(base_dir, 'navigation', 'static',"json_data", 'floor_plan.json')
    
    with open(json_file, 'r') as f:
        floor_plan = json.load(f)
    
    beacons = Beacon.objects.all()
    beacon_data = []
    for beacon in beacons:
        beacon_data.append({
            'beacon_id': beacon.beacon_id,
            'transmit_power': beacon.transmit_power,
            'coordinates': beacon.coordinates,
            'path_loss_exponent':beacon.path_loss_exponent,
            'floor': beacon.floor,
            'time_spent': beacon.time_spent,
            'enter_time': beacon.enter_time,
            'exit_time': beacon.exit_time,
            'user_time': beacon.user_time
        })
    
    for floor_number, floor_data in floor_plan.items():
        floor_data['beacons'] = [b for b in beacon_data if b['floor'] == int(floor_number)]
    
    return JsonResponse(floor_plan, safe=False)

def get_area_coverage(request):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_file = os.path.join(base_dir, 'navigation', 'static', "json_data",'floor_plan.json')
    floor_plan = json_floor_plan(json_file)

    
    with user_lock:
        users = User.objects.all()
        user_data = {}
        for user in users:
            user_data[user.username] = {
                'estimated_path': user.get_estimated_path(),
            }
    
    area_covered = area_coverage(users, floor_plan)
    return JsonResponse({
        'area_covered': float(area_covered) 
    })

def get_numVisitors(request):
    
    with user_lock:
        active_users = User.objects.filter(active=True).count()
    print(f"num active users",active_users)
    return JsonResponse({'active_users': active_users})

def get_traffic_volume_week(request):
    
    users = User.objects.all()
    
    def get_weekday(date_string):
        date = datetime.fromisoformat(date_string)
        return date.strftime('%A')
    
    weekdays = []
    
    with user_lock:
        for user in users:
            for visit in user.past_visits:
                enter_time = visit.get('enter_time')
                if enter_time:
                    weekday = get_weekday(enter_time)
                    weekdays.append(weekday)
        
    counter = Counter(weekdays)
    
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        if day not in counter:
            counter[day] = 0
    
    ordered_weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    sorted_counter = {day: counter[day] for day in ordered_weekdays}
    
    chart_data = {
        "labels": list(sorted_counter.keys()),
        "data": list(sorted_counter.values())
    }
    
    return JsonResponse(chart_data)

def get_traffic_volume_hour(request):
    
    users = User.objects.all()
    
    def get_hour(date_string):
        date = datetime.fromisoformat(date_string)
        return date.hour 
    
    hourly_traffic = defaultdict(int)  
    
    with user_lock:
        for user in users:
            for visit in user.past_visits:
                enter_time = visit.get('enter_time')
                if enter_time:
                    hour = get_hour(enter_time)
                    if 9 <= hour <= 21:  
                        hourly_traffic[hour] += 1
    
    labels = list(range(9, 22))
    data = [hourly_traffic[hour] for hour in labels]
    
    chart_data = {
        "labels": labels,
        "data": data
    }
    
    return JsonResponse(chart_data)

def removeUserPaths(request):
    with transaction.atomic():
        active_users = User.objects.filter(active=True)
        for user in active_users:
            #user.unset_active
            user.add_visit(user.first_step,datetime.now())
            user.clear_active_data()
            user.save()
            User.objects.filter(active=True).update(active=False)
        return JsonResponse({"message":"User paths removed!"})