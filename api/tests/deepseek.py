import requests

# Enter your API Key
API_KEY = "sk-9b2f1bc7d7464468bfe1a97496ecd471"  

url = "https://api.deepseek.com/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

data = {
    "model": "deepseek-chat",  # Use 'deepseek-reasoner' for R1 model or 'deepseek-chat' for V3 model
    "messages": [
        {"role": "system", "content": "You are a professional assistant"},
        {"role": "user", "content": "Who are you?"}
    ],
    "stream": False  # Disable streaming
}

data["stream"] = True

response = requests.post(url, headers=headers, json=data, stream=True)

for line in response.iter_lines():
    if line:
        decoded_line = line.decode('utf-8')
        print(decoded_line)