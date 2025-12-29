document.addEventListener('DOMContentLoaded', () => {
  // Menu Toggle
  const menuToggle = document.querySelector('.menu-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (menuToggle) {
    menuToggle.addEventListener('click', () => {
      navLinks.classList.toggle('active');
    });
  }

  // Detection Logic
  const video = document.getElementById("video");
  const canvas = document.getElementById("canvas");
  const captureButton = document.getElementById("capture");

  // Only execute if we serve detection page elements
  if (video && canvas && captureButton) {
    const context = canvas.getContext("2d");

    // Access the camera
    if (navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices
        .getUserMedia({ video: true })
        .then(function (stream) {
          video.srcObject = stream;
        })
        .catch(function (error) {
          console.log("Something went wrong with camera access!", error);
          alert("Cannot access camera. Please allow camera permissions.");
        });
    }

    // Capture Button Logic
    captureButton.addEventListener("click", () => {
      // Draw current frame to canvas
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      const imageData = canvas.toDataURL("image/jpeg");

      // Display captured image immediately
      const capturedImage = document.getElementById("capturedImage");
      if (capturedImage) capturedImage.src = imageData;

      const predictionText = document.getElementById("prediction");
      if (predictionText) predictionText.innerText = "Processing...";

      // Send to server
      fetch("/process_image", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ image_data: imageData }),
      })
        .then((response) => {
          if (response.status === 401) {
            window.location.href = '/login';
            return;
          }
          return response.json();
        })
        .then((data) => {
          if (!data) return;

          console.log("Prediction Result:", data);

          // Update UI
          const predictedImg = document.getElementById("predictedImage");
          if (predictedImg) predictedImg.src = "data:image/jpeg;base64," + data.annotated_image;

          if (predictionText) predictionText.textContent = data.predicted_class;
        })
        .catch((error) => {
          console.error("Error:", error);
          if (predictionText) predictionText.innerText = "Error";
        });
    });
  }
});