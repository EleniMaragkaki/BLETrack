from celery import shared_task
from .addDataToBase import removeInactiveUsers

@shared_task
def check_inactive():
    removeInactiveUsers()