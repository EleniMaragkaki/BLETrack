document.addEventListener("DOMContentLoaded", function() {
    fetchDataAndVisualize();
});

function fetchDataAndVisualize() {
    Promise.all([
        fetch('/get_user_paths/').then(response => response.json()),
        fetch('/get_floor_plan/').then(response => response.json())
    ]).then(([userPathsData, floorPlanData]) => {
        console.log(userPathsData);  // Log user paths data
        console.log(floorPlanData);  // Log floor plan data
        
        visualizeFloorPlan(floorPlanData[0], 0); // Visualize floor plan for the first floor
        visualizeFloorPlan(floorPlanData[1], 1); // Visualize floor plan for the second floor
        visualizeUserPaths(userPathsData);
        visualizeHeatmap(userPathsData);  // Assuming heatmap is based on user paths data
    }).catch(error => console.error('Error fetching data:', error));
}

function visualizeFloorPlan(data, floorIndex) {
    const layout = {
        title: `Floor Plan ${floorIndex + 1}`,
        xaxis: { title: 'X' },
        yaxis: { title: 'Y' },
        aspectratio: { x: 1, y: 1 },
        showlegend: true
    };

    const plotData = [];

    // Draw rooms
    if (data.rooms) {
        data.rooms.forEach(room => {
            const roomShape = {
                type: 'scatter',
                mode: 'lines',
                x: room.map(point => point[0]),
                y: room.map(point => point[1]),
                fill: 'toself',
                fillcolor: 'rgba(0, 0, 255, 0.1)',
                line: { color: 'blue' },
                name: 'Room'
            };
            plotData.push(roomShape);
        });
    } else {
        console.warn(`Rooms data is missing for floor ${floorIndex}`);
    }

    // Draw entrances
    if (data.entrance) {
        data.entrance.forEach(entrance => {
            const entranceShape = {
                type: 'scatter',
                mode: 'lines',
                x: entrance.map(point => point[0]),
                y: entrance.map(point => point[1]),
                line: { color: 'black', width: 2 },
                name: 'Entrance'
            };
            plotData.push(entranceShape);
        });
    } else {
        console.warn(`Entrance data is missing for floor ${floorIndex}`);
    }

    // Draw doors
    if (data.doors) {
        Object.values(data.doors).forEach(door => {
            const doorShape = {
                type: 'scatter',
                mode: 'lines',
                x: door.map(point => point[0]),
                y: door.map(point => point[1]),
                line: { color: 'black', width: 2 },
                name: 'Door'
            };
            plotData.push(doorShape);
        });
    } else {
        console.warn(`Doors data is missing for floor ${floorIndex}`);
    }

    // Draw beacons
    if (data.beacons) {
        data.beacons.forEach(beacon => {
            const beaconMarker = {
                type: 'scatter',
                mode: 'markers',
                x: [beacon.x],
                y: [beacon.y],
                marker: { color: 'magenta', size: 10 },
                name: 'Beacon'
            };
            plotData.push(beaconMarker);
        });
    } else {
        console.warn(`Beacons data is missing for floor ${floorIndex}`);
    }

    // Draw stairs
    if (data.stairs) {
        data.stairs.forEach(stair => {
            const stairMarker = {
                type: 'scatter',
                mode: 'markers',
                x: [stair.x],
                y: [stair.y],
                marker: { color: 'green', size: 10 },
                name: 'Stair'
            };
            plotData.push(stairMarker);
        });
    } else {
        console.warn(`Stairs data is missing for floor ${floorIndex}`);
    }

    Plotly.newPlot(`floor-plan-${floorIndex}`, plotData, layout);
}

function visualizeUserPaths(data) {
    const traces = [];

    Object.entries(data).forEach(([username, userData]) => {
        const path = userData.estimated_path;
        const xCoords = path.map(point => point[0]);
        const yCoords = path.map(point => point[1]);

        const trace = {
            x: xCoords,
            y: yCoords,
            mode: 'lines+markers',
            name: username
        };

        traces.push(trace);
    });

    Plotly.addTraces('floor-plan', traces);
}

function visualizeHeatmap(data) {
    const timeSpent = {};

    // Aggregate time spent at each position across users
    Object.values(data).forEach(userData => {
        Object.entries(userData.time_spent).forEach(([position, time]) => {
            if (timeSpent[position]) {
                timeSpent[position] += time;
            } else {
                timeSpent[position] = time;
            }
        });
    });

    // Convert aggregated data into heatmap format
    const heatmapData = Object.keys(timeSpent).map(position => {
        const [x, y] = position.split(',').map(Number);
        return { x, y, value: timeSpent[position] };
    });

    const trace = {
        x: heatmapData.map(d => d.x),
        y: heatmapData.map(d => d.y),
        z: heatmapData.map(d => d.value),
        type: 'heatmap'
    };

    const layout = {
        title: 'Heatmap Based on Time Spent',
        xaxis: { title: 'X' },
        yaxis: { title: 'Y' }
    };

    Plotly.newPlot('heatmap', [trace], layout);
}
