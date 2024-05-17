// Fetch past conversations and display them when the page loads
async function fetchConversations() {
    const response = await fetch("http://127.0.0.1:5000/get-conversations");
    const data = await response.json();
    return data;
}

// Store each conversation when the user sends a new message
async function storeConversation(userMessage, aiResponse) {
    await fetch("http://127.0.0.1:5000/store", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            user_message: userMessage,
            ai_response: aiResponse
        })
    });
}

document.addEventListener("DOMContentLoaded", async function() {
    const conversations = await fetchConversations();
    const responseDiv = document.getElementById('response');
    
    conversations.forEach(convo => {
        const convoMessage = `
            <div><strong>Past Conversation - User:</strong> ${convo.user_message}</div>
            <div><strong>Past Conversation - AI:</strong> ${convo.ai_response}</div>`;
        responseDiv.innerHTML += convoMessage;
    });
});

document.getElementById('run').addEventListener('click', async function() {
    const runButton = document.getElementById('run');
    const message = document.getElementById('prompt').value;
    console.log("Sending message:", message);

    const userMessage = `<div><strong>USER:</strong> ${message}</div>`;
    document.getElementById('response').innerHTML += userMessage;

    runButton.innerText = 'AI is thinking...';
    runButton.disabled = true;

    try {
        const response = await fetch("http://42c0-34-124-141-80.ngrok.io/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });
        
        if (!response.ok) {
            throw new Error("Network response was not ok");
        }
        
        const data = await response.json();
        console.log("Received data:", data);

        let cleanedResponse = data.response.replace("<s>", "").replace("</s>", "").trim();
        cleanedResponse = cleanedResponse.split("ASSISTANT:")[1].trim();

        const assistantMessage = `<div><strong>ASSISTANT:</strong> ${cleanedResponse}</div>`;
        document.getElementById('response').innerHTML += assistantMessage;

        // Scroll to the bottom to see the latest message
        const responseContainer = document.getElementById('response');
        responseContainer.scrollTop = responseContainer.scrollHeight;

        // Store the conversation
        await storeConversation(message, cleanedResponse);
    } catch (error) {
        console.error("Error:", error);
    } finally {
        runButton.innerText = 'Run Prompt';
        runButton.disabled = false;
    }
});

document.getElementById('restart').addEventListener('click', function() {
    document.getElementById('response').innerHTML = "Response will appear here...";
});

document.getElementById('clean').addEventListener('click', function() {
    document.getElementById('response').innerHTML = "";
});

document.getElementById('stop').addEventListener('click', function() {
    document.getElementById('run').disabled = true;
});
