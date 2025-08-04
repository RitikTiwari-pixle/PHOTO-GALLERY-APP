// This file goes inside the 'static/js/' folder

function initializeScanner(eventId) {
    const video = document.getElementById('video');
    const snap = document.getElementById('take-selfie-btn');
    const resultsContainer = document.getElementById('results-container');
    const loadingContainer = document.getElementById('loading-container');
    const scannerUI = document.getElementById('scanner-ui');
    const canvas = document.createElement('canvas');

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function(stream) {
                video.srcObject = stream;
                video.play();
            })
            .catch(function(err) {
                console.error("Error accessing camera: ", err);
                scannerUI.innerHTML = `<div class="alert alert-danger">Could not access the camera. Please grant permission and try again.</div>`;
            });
    }

    snap.addEventListener("click", function() {
        loadingContainer.style.display = 'block';
        scannerUI.style.display = 'none';
        resultsContainer.innerHTML = '';

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        const imageDataURL = canvas.toDataURL('image/jpeg');

        fetch(`/api/find_my_photos/${eventId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ image: imageDataURL }),
        })
        .then(response => response.json())
        .then(data => {
            loadingContainer.style.display = 'none';
            if (data.error) {
                resultsContainer.innerHTML = `<div class="alert alert-warning">${data.error}</div>`;
                scannerUI.style.display = 'block';
            } else if (data.message) {
                 resultsContainer.innerHTML = `<div class="alert alert-info">${data.message}</div>`;
                 scannerUI.style.display = 'block';
            } else if (data.gallery_html) {
                resultsContainer.innerHTML = data.gallery_html;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            loadingContainer.style.display = 'none';
            resultsContainer.innerHTML = `<div class="alert alert-danger">An unexpected error occurred. Please try again.</div>`;
            scannerUI.style.display = 'block';
        });
    });
}
