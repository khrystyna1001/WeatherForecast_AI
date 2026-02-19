const ctx = document.getElementById('weatherChart').getContext('2d');
new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['15.02', '16.02', '17.02', '18.02', '19.02', '20.02'],
        datasets: [{
            data: [-12, -8, -2, 4, -10, 5],
            borderColor: '#000',
            borderWidth: 2,
            tension: 0.1,
            fill: false
        }]
    },
    options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
            y: { min: -25, max: 40 }
        }
    }
});

const dateInput = document.getElementById('dateInput');
const resetLabel = document.getElementById('resetDate');

// Reset when clicking "Select new Date"
resetLabel.addEventListener('click', function(e) {
    dateInput.value = '';
    document.querySelector('.current-date').innerText = '15.02.2027';
    console.log("Date reset to default view.");
});

const card = document.createElement('div');
card.className = 'weather-card';

// Chart data for weather forecast

function updateChart(data) {
    const weatherChart = Chart.getChart("weatherChart");
    if (!weatherChart) {
        console.error("Chart instance not found!");
        return;
    }
    
    // Extract times and temperatures from the API data
    weatherChart.data.labels = data.map(item => item.time);
    weatherChart.data.datasets[0].data = data.map(item => parseFloat(item.temp));
    
    weatherChart.update();
}

// Show weather forecast
async function showForecast(type) {
    const viewType = (type === 'week' || type === 'weekly') ? 'weekly' : 'today';
    
    const urlParams = new URLSearchParams(window.location.search);
    const selectedDate = urlParams.get('date');

    if (!selectedDate) {
        console.error("No date found in URL parameters.");
        return;
    }

    document.querySelectorAll('.tab').forEach(btn => btn.classList.remove('active'));
    
    if (window.event && window.event.currentTarget) {
        window.event.currentTarget.classList.add('active');
    } else {
        const tabs = document.querySelectorAll('.tab');
        tabs.forEach(tab => {
            if (tab.innerText.toLowerCase().includes(type.toLowerCase())) {
                tab.classList.add('active');
            }
        });
    }
    const container = document.getElementById('forecast-display');
    container.innerHTML = '<p>Querying LSTM Model...</p>';

    try {
        const url = `http://127.0.0.1:8000/predict/${selectedDate}?view_type=${viewType}`;
        console.log("Fetching from:", url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            const errorBody = await response.text();
            console.error("Server responded with:", errorBody);
            throw new Error("Server error");
        }
        
        const data = await response.json();
        container.innerHTML = '';
        
        if (Chart.getChart("weatherChart")) {
            updateChart(data);
        }
        
        data.forEach(item => {
            const card = document.createElement('div');
            card.className = 'weather-card';
            card.innerHTML = `
                <div class="card-header">
                    <p class="card-date">${item.display_time}</p>
                    <p class="card-status">${item.status}</p>
                </div>
                <div class="card-footer">
                    <div class="stats">
                        <span class="temp">${item.temp}C</span>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error(err);
        container.innerHTML = `<p>Error: AI Server responded with 404. Check FastAPI route.</p>`;
    }
}
const urlParams = new URLSearchParams(window.location.search);
const dateFromUrl = urlParams.get('date');
if (dateFromUrl) {
    const [year, month, day] = dateFromUrl.split('-');
    const formattedDate = `${day}.${month}.${year}`;

    const displaySpan = document.querySelector('.current-date');
    if (displaySpan) {
        displaySpan.innerText = formattedDate;
    }

    const footerDateInput = document.getElementById('dateInput');
    if (footerDateInput) {
        footerDateInput.value = dateFromUrl;
    }
}