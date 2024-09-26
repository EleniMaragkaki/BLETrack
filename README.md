# BLETrack

## Description
BLETrack is an indoor tracking and visualization system that utilizes BLE Beacons and a particle filtering algorithm, incorporating wall constraints, to accurately detect the user's location within a building. Integrated within a Django application, the system provides useful information such as user paths, heatmaps indicating time spent in different areas, daily and hourly traffic volumes, the extent of space coverage by users, and real-time active user counts.

## Prerequisites
- Redis
- Python and Django
- Celery

## Installation & Usage guide

1. Clone the repository

2. Run Redis server (wsl):
    ```bash
    redis-server
    ```

3. Start the worker for background processes:
    ```bash
    celery -A indoorTrackingProject worker --pool=solo -l info
    ```

4. Run the Django server:
    ```bash
    python manage.py runserver
    ```

5. View the website:
    ```plaintext
    http://127.0.0.1:8000/
    ```
~