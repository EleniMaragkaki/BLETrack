
let selectedFloor = 0;
let view = 0;
let userPathsData = {};
let floorPlanData;
let svgContainer;
let mapContainer = document.getElementById('heatmap_svg_container');
let heatmapData = {};
let coveragePieChart;
let trafficVolumeWeekChart;
let trafficVolumeHourChart;
let pathInterval, heatmapInterval;
//thelei allagh
const colorMap = {
    "MAC_ID1": "red",
    "MAC_ID2": "blue",
    "MAC_ID3": "green",
    "MAC_ID3": "yellow",
};

function initialize() {
    fetchDataAndVisualize();
}

function loadMapView(selectedView) {
    view = selectedView
    
    clearInterval(pathInterval)
    clearInterval(heatmapInterval)
    //view : user paths
    if (view == 0) {
        clearHeatmap()
        drawUserPaths()
        pathInterval = setInterval(drawUserPaths, 1000)
    }
    //view : heatmap
    else if (view == 1) {
        clearUserPaths()
        drawHeatmapUser()
        heatmapInterval = setInterval(drawHeatmapUser, 1000)
    }
    //view : userpaths + heatmap
    else {
        clearUserPaths()
        clearHeatmap()
        drawUserPaths()
        drawHeatmapUser()
        heatmapInterval = setInterval(drawHeatmapUser, 1000)
        pathInterval = setInterval(drawUserPaths, 1000)

    }
}
function clearHeatmap() {
    heatmap.setData({
        min: 0,
        max: 0,
        data: []
    });
}
function clearUserPaths() {
    svgContainer.selectAll('.user-path-group').remove();
}
function fetchDataAndVisualize() {
    Promise.all([
        //fetch('/get_user_paths/').then(response => response.json()),
        fetch('/get_floor_plan/').then(response => response.json())

    ]).then(([userData, floorPlan]) => {
       // userPathsData = userData;
        floorPlanData = floorPlan;

        svgContainer = d3.select(document.getElementById("heatmap_container"))
            .append('svg')
            .attr('width', 900)
            .attr('height', 700);

        heatmap = h337.create({
            container: document.getElementById("heatmap_container"),
            radius: 20,
            maxOpacity: .5,
            minOpacity: 0,
            blur: .85
        });
        setInterval(fetchUserData, 1000)
        loadFloorPlan(selectedFloor);
        loadMapView(view)
        update_data()
        setInterval(update_data, 10000)
    }).catch(error => console.error('Error data:', error));
}

function fetchUserData() {
    fetch('/get_user_paths/')
        .then(response => response.json())
        .then(updatedUserPathsData => {
            userPathsData = updatedUserPathsData;
        })
        .catch(error => console.error('Error user paths:', error));
}


function loadFloorPlan(floor) {
    selectedFloor = floor;
    console.log("floor:", selectedFloor);

    svgContainer.selectAll("*").remove();
    const svgFile = `static/images/floor${selectedFloor}.svg`;
    d3.xml(svgFile)
        .then(data => {
            const importedNode = document.importNode(data.documentElement, true);
            svgContainer.node().appendChild(importedNode);
            loadMapView(view);
        })
        .catch(error => console.error('Error loading SVG:', error));
}
function checkBeaconCoverage(checked) {
    if (checked) {
        loadBeaconCoverage(floorPlanData[selectedFloor].beacons);
    } else {
        d3.select(document.getElementById("heatmap_container")).select('svg')
            .selectAll('.coverage-circle').remove();
    }
}
function loadBeaconCoverage(beacons){
    const svgContainer = d3.select(document.getElementById("heatmap_container")).select('svg');

    svgContainer.selectAll('.coverage-circle').remove(); 

    beacons.forEach(beacon => {
        const coordinates = beacon.coordinates;
        const transmitPower = beacon.transmit_power;
        const pathLossExponent = beacon.path_loss_exponent;
        
        const coverageRadius = Math.sqrt(
            Math.pow(10, (transmitPower - (-10 * pathLossExponent * Math.log10(1))) / (10 * pathLossExponent))
        );

        svgContainer.append('circle')
            .attr('class', 'coverage-circle')
            .attr('cx', coordinates[0] * 100)
            .attr('cy', (7 - coordinates[1]) * 100) 
            .attr('r', coverageRadius * 100) 
            .style('fill', 'blue')
            .style('opacity', 0.1)
            .style('stroke', 'blue');
    });
}

function drawUserPaths() {
    clearUserPaths();

    const userGroups = svgContainer.selectAll('.user-path-group')
        .data(Object.entries(userPathsData), d => d[0]);

    const userGroupsEnter = userGroups.enter()
        .append('g')
        .attr('class', 'user-path-group')
        .attr('id', d => `user-path-${d[0]}`);

    userGroupsEnter.each(function (d) {
        const userData = d[1];
        const pathsData = userData.estimated_path.filter(point => point[2] == selectedFloor);
        const color = colorMap[d[0]] || 'black';
        const pathGroup = d3.select(this).append('g').attr('class', 'path-group');

        for (let i = 0; i < pathsData.length - 1; i++) {
            const point = pathsData[i];
            const nextPoint = pathsData[i + 1];

            pathGroup.append('line')
                .attr('class', 'user-path')
                .attr('x1', scaleUserPath(point)[0])
                .attr('y1', scaleUserPath(point)[1])
                .attr('x2', scaleUserPath(nextPoint)[0])
                .attr('y2', scaleUserPath(nextPoint)[1])
                .style('stroke', color)
                .style('stroke-width', 2);
        }
    });

    userGroups.exit().remove();

}



function drawHeatmapUser() {
    let min = 0
    let max = 0
    let data = []
    let maxTime = 0
    Object.values(userPathsData).forEach(userData => {
        if (userData.time_spent) {
            Object.entries(userData.time_spent).forEach(([position, time]) => {
                try {
                    let [x, y, z] = JSON.parse(position);
                    if (Math.floor(z) == selectedFloor) {
                        scaledX = x * 100;
                        scaledY = (7 - y) * 100;
                        data.push({ x: Math.floor(scaledX), y: Math.floor(scaledY), value: time });
                        if (time > maxTime) {
                            maxTime = time
                            max = maxTime;
                        }
                    }
                } catch (error) {
                    console.error(`Error heatmap`, error);
                }
            });
        }
    });

    heatmap.setData({
        min: min,
        max: max,
        data: data
    });
    console.log(heatmap.getData())
}
function drawHeatmapBeacon() {

    fetch(`/get_heatmap_data/?floor=${selectedFloor}`)
        .then(response => response.json())
        .then(data => {
            heatmapData = data.data;
            let min = 0
            let max = Math.max(...heatmapData.map(item => item.value))

            heatmap.setData({
                min: min,
                max: max,
                data: heatmapData
            });
        })
        .catch(error => {
            console.error('Error fetching heatmap data:', error);
        });

}

function scaleUserPath(point) {
    const scale = 100;
    const scaledX = point[0] * scale;
    const scaledY = (7 - point[1]) * scale;
    return [scaledX, scaledY];
}

function removeUsers(isChecked) {
    if (isChecked) {
        console.log("removing user paths...")

        fetch('/removeUserPaths/')
        .then(response => response.json())
        .then(data => {
            console.log(data.message); 
        })
        .catch((error) => {
            console.error('Error:', error);
        });
        setTimeout(function() {
            document.getElementById("removeUserPathsCheckbox").checked = false;  
        }, 1000); 
    }
}