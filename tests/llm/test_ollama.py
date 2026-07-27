import ollama

response = ollama.chat(
    model="deepseek-r1:1.5b",
    messages=[
        {
            "role": "user",
            "content": "Return only JSON: {\"test\":\"hello\"}"
        }
    ]
)

print(response)
print("CONTENT:")
print(response["message"]["content"])