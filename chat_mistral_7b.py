# Use a pipeline as a high-level helper
from transformers import pipeline


messages = [
    {"role": "user", "content": "Who are you?"},
]
pipe = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.2")
pipe(messages)

while True:
    messages.append({"role": "user", "content": input("You: ")})
    response = pipe(messages)
    print("Bot:", response[0]["generated_text"])
    messages.append({"role": "bot", "content": response[0]["generated_text"]})