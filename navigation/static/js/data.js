
function update_data() {
    loadTrafficVolumeWeek();
    loadTrafficVolumeHour();
    loadCoveragePieChart();
    loadVisitors()
}

function loadCoveragePieChart() {
    fetch('/get_area_coverage/')
        .then(response => response.json())
        .then(data => {
            const area_covered = data.area_covered;
            const area_uncovered = 1 - area_covered;

            const pieData = {
                datasets: [{
                    data: [area_covered * 100, area_uncovered * 100],
                    backgroundColor: [
                        '#0a2342',
                        '#19a979'
                    ],
                    borderWidth: 0
                }],
                labels: ['Covered Area', 'Uncovered Area'],
            };

            const pieOptions = {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            font: {
                                size: 16
                            }
                        }
                    },
                    datalabels: {
                        formatter: (value, context) => {
                            return value.toFixed(2) + '%';
                        },
                        color: '#fff',
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        anchor: 'end',
                        align: 'start',
                        textShadowColor: '#000',
                        textShadowBlur: 1
                    }
                }
            };

            const pie_container = document.getElementById('area_coverage_container').getContext('2d');
            if (coveragePieChart) {
                coveragePieChart.destroy();
            }

            coveragePieChart = new Chart(pie_container, {
                type: 'pie',
                data: pieData,
                options: pieOptions,
                plugins:[ChartDataLabels]
            });
        })
        .catch(error => console.error('Error coverage area:', error));
}


function loadVisitors() {
    fetch('/get_numVisitors/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            const active_users = data.active_users;
            document.getElementById('activeUsersText').innerText = `${active_users}`;
        })
        .catch(error => {
            console.error('Error active visitors:', error);
        });
}

function loadTrafficVolumeWeek() {
    fetch('/get_traffic_volume_week/')
        .then(response => response.json())
        .then(chartData => {
            const chart_container = document.getElementById('traffic_volume_day_container').getContext('2d');
            if (trafficVolumeWeekChart) {
                trafficVolumeWeekChart.destroy();
            }

            let today = new Date().getDay() - 1;
            trafficVolumeWeekChart = new Chart(chart_container, {
                type: 'bar',
                data: {
                    labels: chartData.labels,
                    datasets: [{
                        label: 'Visitors',
                        data: chartData.data,
                        backgroundColor: chartData.labels.map((label, index) => {
                            return index === today ? '#0a2342' : '#19a979';
                        }),
                        borderColor: '#73A9AD',
                        borderWidth: 1,
                        barThickness: 20,
                        categoryPercentage: 0.9,
                        barPercentage: 0.9,
                        color: '#fff'
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                font: {
                                    size: 14
                                }
                            }
                        },
                        x: {
                            ticks: {
                                font: {
                                    size: 14
                                }
                            }
                        }
                    },
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Traffic Volume Week',
                            font: {
                                size: 16
                            }
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error traffic volume:', error));
}


function loadTrafficVolumeHour() {
    fetch('/get_traffic_volume_hour/')
        .then(response => response.json())
        .then(chartData => {
            const chart_container = document.getElementById('traffic_volume_hour_container').getContext('2d');
            if (trafficVolumeHourChart) {
                trafficVolumeHourChart.destroy();
            }
            const curr_hour = new Date().getHours();
            console.log("curr hour", curr_hour)
            trafficVolumeHourChart = new Chart(chart_container, {
                type: 'bar',
                data: {
                    labels: chartData.labels.map(hour => `${hour}:00`),
                    datasets: [{
                        label: 'Visitors',
                        data: chartData.data,
                        backgroundColor: chartData.labels.map((label, index) => { return label == curr_hour ? '#0a2342' : '#19a979'; }),
                        borderColor: '#73A9AD',
                        borderWidth: 1,
                        barThickness: 20,
                        categoryPercentage: 0.9,
                        barPercentage: 0.9
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                font: {
                                    size: 14
                                }
                            }
                        },
                        x: {
                            ticks: {
                                font: {
                                    size: 14
                                }
                            }
                        }
                    },
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Traffic Volume 9 AM to 9 PM',
                            font: {
                                size: 16
                            }
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error traffic volume hour:', error));
}
