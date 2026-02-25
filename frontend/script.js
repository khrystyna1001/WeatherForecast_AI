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
if (resetLabel) {
    resetLabel.addEventListener('click', function(e) {
        dateInput.value = '';
        document.querySelector('.current-date').innerText = '15.02.2027';
        console.log("Date reset to default view.");
    });
}

const card = document.createElement('div');
card.className = 'weather-card';

// Arrows
// Track the currently selected date globally
let currentSelectedDate = new Date();

// Initialize the page
window.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const dateParam = urlParams.get('date');
    
    if (dateParam) {
        currentSelectedDate = new Date(dateParam);
    }
    
    updateDateDisplay();
    setupArrows();
});

function setupArrows() {
    const prevBtn = document.querySelector('.arrow-btn:first-child');
    const nextBtn = document.querySelector('.arrow-btn:last-child');

    prevBtn.addEventListener('click', () => {
        currentSelectedDate.setDate(currentSelectedDate.getDate() - 1);
        syncAndFetch();
    });

    nextBtn.addEventListener('click', () => {
        currentSelectedDate.setDate(currentSelectedDate.getDate() + 1);
        syncAndFetch();
    });
}

function syncAndFetch() {
    // Convert to YYYY-MM-DD format for API and Input
    const year = currentSelectedDate.getFullYear();
    const month = String(currentSelectedDate.getMonth() + 1).padStart(2, '0');
    const day = String(currentSelectedDate.getDate()).padStart(2, '0');
    const formattedDate = `${year}-${month}-${day}`;

    // Update the Date Input field
    document.getElementById('forecast_date').value = formattedDate;

    // Update URL without reloading
    const newUrl = `${window.location.pathname}?date=${formattedDate}`;
    window.history.pushState({ path: newUrl }, '', newUrl);

    updateDateDisplay();
    
    // Determine current view type from active tab
    const isActiveWeek = document.querySelector('.tab:last-child').classList.contains('active');
    showForecast(isActiveWeek ? 'week' : 'today');
}

function updateDateDisplay() {
    const displaySpan = document.querySelector('.current-date');
    if (displaySpan) {
        const day = String(currentSelectedDate.getDate()).padStart(2, '0');
        const month = String(currentSelectedDate.getMonth() + 1).padStart(2, '0');
        const year = currentSelectedDate.getFullYear();
        displaySpan.innerText = `${day}.${month}.${year}`;
    }
}

// Update handleNewDate to use the global date object
function handleNewDate() {
    const dateInput = document.getElementById('forecast_date');
    if (dateInput.value) {
        currentSelectedDate = new Date(dateInput.value);
        syncAndFetch();
    }
}

// Chart data for weather forecast

function updateChart(data, viewType) {
    const weatherChart = Chart.getChart("weatherChart");
    if (!weatherChart) {
        console.error("Chart instance not found!");
        return;
    }
    
    weatherChart.data.labels = data.map(item => viewType === "weekly" ? item.date.split("-").slice(1).reverse().join(".") : item.time);
    weatherChart.data.datasets[0].data = data.map(item => parseFloat(item.temp.replace('°', '')));
    
    weatherChart.update();
}

// Show weather forecast
async function showForecast(type) {
    const viewType = (type === 'week' || type === 'weekly') ? 'weekly' : 'today';
    const container = document.getElementById('forecast-display');
    const dateInput = document.getElementById('forecast_date');
    const selectedDate = dateInput.value || new URLSearchParams(window.location.search).get('date');

    if (!selectedDate) return;

    // UI Feedback
    container.innerHTML = `<div class="loading-spinner">LSTM is processing atmospheric patterns...</div>`;
    
    try {
        const response = await fetch(`http://127.0.0.1:8000/predict/${selectedDate}?view_type=${viewType}`);
        if (!response.ok) throw new Error("AI Server Error");
        
        const data = await response.json();
        container.innerHTML = '';

        // Update Chart
        updateChart(data, viewType);

        // Generate Cards
        data.forEach(item => {
            const card = document.createElement('div');
            card.className = 'weather-card';
            card.innerHTML = `
                <p class="card-date">${item.display_time}</p>
                <span class="temp">${item.temp}</span>
                <p class="card-status">${item.status}</p>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        container.innerHTML = `<div class="loading-spinner" style="color: #ef4444;">AI Model Offline. Please check your Python server.</div>`;
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