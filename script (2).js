document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const recordButton = document.getElementById('recordButton');
    const stopButton = document.getElementById('stopButton');
    const audioPlayer = document.getElementById('audioPlayer');
    const recordingsList = document.getElementById("recordingsList");

    let gumStream = null;
    let rec = null;
    let input = null;
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    const audioContext = new AudioContext();
    let isRecording = false;
    let chunks = []; 

    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const username = event.target.elements.username.value;  // Changed from email
            const password = event.target.elements.password.value;
            const response = await loginUser(username, password);
            if (response.status === "success") {
                window.location.href = 'main.html'; // redirect to main page
            } else {
                alert(response.message);
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const username = event.target.elements.username.value;  // Changed from email
            const password = event.target.elements.password.value;
            const response = await createUser(username, password);
            if (response.status === "success") {
                window.location.href = 'index.html'; // redirect to login page
            } else {
                alert(response.message);
            }
        });
    }

    async function loginUser(username, password) {
        try {
            const response = await fetch('https://gbtart.com/login', {
                method: 'POST',
                mode: 'cors',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            return await response.json();
        } catch (error) {
            return { status: "error", message: 'Error logging in.' };
        }
    }

    async function createUser(username, password) {
        try {
            const response = await fetch('https://gbtart.com/register', {
                method: 'POST',
                mode: 'cors',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            return await response.json();
        } catch (error) {
            return { status: "error", message: 'Error creating account.' };
        }
    }

    // Check browser compatibility
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Your browser does not support audio recording features. Please update or switch to a modern browser.');
    } else {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                gumStream = stream;
            })
            .catch(error => {
                console.error('Error accessing microphone:', error);
                alert('Error accessing microphone. Please check your microphone settings.');
            });
    }

    recordButton.addEventListener('click', startRecording);
    stopButton.addEventListener('click', stopRecording);

    function startRecording() {
        isRecording = true;
        recordButton.textContent = 'Firechat is Listening';
        recordChunk();
    }

    function recordChunk() {
        if (!isRecording) return;

        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                gumStream = stream;
                input = audioContext.createMediaStreamSource(stream);
                rec = new Recorder(input, { numChannels: 1 });
                rec.record();

                setTimeout(() => {
                    rec.stop();

                    rec.exportWAV(function(blob) {
                        if (containsSpeech(blob)) {
                            sendAudioToServer(blob);
                        }
                    });

                    gumStream.getAudioTracks().forEach(track => track.stop());
                    gumStream = null;

                    recordChunk();
                }, 15000); // 15 seconds
            })
            .catch(error => {
                console.error('Error accessing microphone:', error);
                alert('Error accessing microphone. Please check your microphone settings.');
            });
    }

    function containsSpeech(chunk) {
        // Placeholder function: Analyze the chunk's volume or waveform
        // Use libraries/services to make this efficient and accurate
        // For this placeholder, we'll send every chunk
        return true;
    }

    function stopRecording() {
        isRecording = false;
        recordButton.textContent = 'Talk to your AI';
    }

    async function sendAudioToServer(audioBlob) {
        document.getElementById('loadingSpinner').style.display = 'block';
        const formData = new FormData();
        formData.append('file', audioBlob, 'recorded_audio.wav');

        try {
            const response = await fetch('https://gbtart.com/process_audio', {
                method: 'POST',
                mode: 'cors',
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();

                if (data.chat_response) {
                    const userMessage = `<div><strong>You:</strong> ${data.user_text}</div>`;
                    const assistantMessage = `<div><strong>AI:</strong> ${data.chat_response}</div>`;
                    document.getElementById('response').innerHTML = userMessage + assistantMessage;
            
                    const fullPath = "https://gbtart.com/" + data.audio_path;
            
                    audioPlayer.src = fullPath;
                    audioPlayer.style.display = 'block';
                    audioPlayer.play();
            
                    const downloadLink = document.createElement('a');
                    downloadLink.href = fullPath;
                    downloadLink.download = 'response.mp3';
                    downloadLink.innerHTML = 'Download Audio Response';
                    document.getElementById('response').appendChild(downloadLink);
                } else {
                    console.info("User's message was too short. No response generated.");
                }

            } else {
                console.error("Server responded with status:", response.status);
                const text = await response.text();
                console.error("Server response text:", text);
            }
        } catch (error) {
            console.error("Error with the fetch request:", error.message);
        }
        document.getElementById('loadingSpinner').style.display = 'none';
    }
});
