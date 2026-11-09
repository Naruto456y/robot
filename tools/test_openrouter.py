#!/usr/bin/env python3
import requests
import json
import sys

sys.path.append('/home/pi/project_demo/09.AI_Big_Model/')
from API_KEY import openAI_KEY

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {openAI_KEY}",
    "Content-Type": "application/json"
}
data = {
    "model": "openai/gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Привет! Ты работаешь?"}]
}

response = requests.post(url, headers=headers, json=data)
if response.status_code == 200:
    print("✅ OpenRouter работает!")
    print(response.json()['choices'][0]['message']['content'])
else:
    print(f"❌ Ошибка: {response.status_code}")
    print(response.text)