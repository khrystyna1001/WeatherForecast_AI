// Show forecast button
document.addEventListener('DOMContentLoaded', function() {
    const dateValue = document.getElementById('forecast_date');
    const buttonContainer = document.getElementById('button-container');

    dateValue.addEventListener('input', function() {
        console.log(this.value)
        if (this.value) {
            buttonContainer.style.display = 'block';
        } else {
            buttonContainer.style.display = 'none';
        }
    });
});

const dateValue = document.getElementById('forecast_date');
const forecastBtn = document.querySelector('.card-button');

forecastBtn.onclick = function() {
    const date = dateValue.value;
    if (date) {
        window.location.href = `forecast.html?date=${date}`;
    }
};

// Get current date
const d = new Date();
const year = d.getFullYear();
const month = String(d.getMonth() + 1).padStart(2, '0');
const day = String(d.getDate()).padStart(2, '0');

const dateString = `${year}-${month}-${day}`;
document.getElementById('forecast_date').min = dateString;