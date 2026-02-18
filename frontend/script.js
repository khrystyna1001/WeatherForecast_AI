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

resetLabel.addEventListener('click', function(e) {
    dateInput.value = '';
    document.querySelector('.current-date').innerText = '15.02.2027';
    console.log("Date reset to default view.");
});

const card = document.createElement('div');
card.className = 'weather-card';

async function showForecast(type) {
    document.querySelectorAll('.tab').forEach(btn => btn.classList.remove('active'));
    event.currentTarget.classList.add('active');

    const container = document.getElementById('forecast-display');
    container.innerHTML = '<p>Querying LSTM Model...</p>';

    try {
        const response = await fetch(`http://127.0.0.1:8000/predict?view_type=${type}`);
        const data = await response.json();
        console.log(data)

        container.innerHTML = '';
        
        data.forEach(item => {
            const card = document.createElement('div');
            card.className = 'weather-card';
            card.innerHTML = `
                <div class="card-header">
                    <p class="card-date">${item.time}</p>
                    <p class="card-status">${item.status}</p>
                </div>
                <div class="card-footer">
                    <div class="stats">
                        <span class="temp">${item.temp}</span>
                    </div>
                </div>
            `;
            container.appendChild(card);
            console.log(item.time)
        });
    } catch (err) {
        container.innerHTML = '<p>Error: AI Server is offline.</p>';
    }
}