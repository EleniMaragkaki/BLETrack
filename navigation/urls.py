from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    #path('initialize_user_tracking/', views.initialize_user_tracking, name='initialize_user_tracking'),
    #path('update_user_step/', views.update_user_step, name='update_user_step'), 
    path('get_floor_plan/', views.get_floor_plan, name='get_floor_plan'),
    path('get_user_paths/', views.get_user_paths, name='get_user_paths'),
    path('get_area_coverage/', views.get_area_coverage, name='get_area_coverage'),
    path('get_numVisitors/', views.get_numVisitors, name='get_numVisitors'),
    path('get_traffic_volume_week/', views.get_traffic_volume_week, name='get_traffic_volume_week'),
    path('get_traffic_volume_hour/', views.get_traffic_volume_hour, name='get_traffic_volume_hour'),
    path('get_heatmap_data/', views.get_heatmap_data, name='get_heatmap_data'),
    path('add_user_step/', views.add_user_step, name='add_user_step'),
    path('add_user/', views.add_user, name='add_user'),
    path('removeUserPaths/', views.removeUserPaths, name='removeUserPaths'),

]