function myFunction() {
  var x = document.getElementById("myTopnav");
  if (x.className === "topnav") {
    x.className += " responsive";

  } else {
    x.className = "topnav";
  }
}

const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const context = canvas.getContext("2d");
const captureButton = document.getElementById("capture");
const socket = io.connect("http://" + document.domain + ":" + location.port);
const notification = document.createElement("div");

// gaya notifikasi
notification.id = "notification";
notification.style.position = "fixed";
notification.style.bottom = "20px";
notification.style.right = "20px";
notification.style.padding = "10px";
notification.style.backgroundColor = "#4CAF50";
notification.style.color = "#fff";
notification.style.borderRadius = "5px";
notification.style.display = "none";
document.body.appendChild(notification);

// Access the camera
if (navigator.mediaDevices.getUserMedia) {
  navigator.mediaDevices
    .getUserMedia({ video: true })
    .then(function (stream) {
      video.srcObject = stream;
    })
    .catch(function (error) {
      console.log("Something went wrong!");
    });
}

// Akses kamera
video.addEventListener("play", () => {
  function sendFrame() {
    if (video.paused || video.ended) {
      return;
    }
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const data = canvas.toDataURL("image/jpeg");
    const buffer = data.split(",")[1];
    socket.emit(
      "video_frame",
      Uint8Array.from(atob(buffer), (c) => c.charCodeAt(0)).buffer
    );
    requestAnimationFrame(sendFrame);
  }
  sendFrame();
});

// 

captureButton.addEventListener("click", () => {
  context.drawImage(video, 0, 0, canvas.width, canvas.height);
  const imageData = canvas.toDataURL("image/jpeg");

  // Display captured image
  const capturedImage = document.getElementById("capturedImage");
  capturedImage.src = imageData;

  // Kirim URL data ke server menggunakan Fetch API
  fetch("/process_image", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ image_data: imageData }),
  })
    .then((response) => response.json())
    .then((data) => {
      // Menangani respon dari server Flask
      console.log("Prediction Result:", data);

      // Menampilkan gambar yang diprediksi
      document.getElementById("predictedImage").src =
        "data:image/jpeg;base64," + data.annotated_image;

      // Menampilkan kelas yang diprediksi
      document.getElementById("prediction").textContent =
        "Predicted Class: " + data.predicted_class;

      // Tampilkan pemberitahuan
      notification.textContent = "Gambar berhasil diproses!";
      notification.style.display = "block";

      // Sembunyikan notifikasi setelah beberapa detik
      setTimeout(() => {
        notification.style.display = "none";
       }, 3000); 
    })
    .catch((error) => {
      console.error("Error:", error);
      // Menampilkan pemberitahuan kesalahan jika diperlukan
      notification.textContent = "Terjadi kesalahan saat memproses gambar.";
      notification.style.backgroundColor = "#f44336"; 
      notification.style.display = "block";
      setTimeout(() => {
        notification.style.display = "none";
      }, 3000); 
    });
});