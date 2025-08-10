from transformers import pipeline

# Load GPT-2 model
generator = pipeline("text-generation", model="gpt2")

print("🚀 Mini-ChatGPT Ready!")
while True:
    prompt = input("\nEnter your prompt (or 'quit' to exit): ")
    if prompt.lower() == 'quit':
        break
    output = generator(prompt, max_length=80, num_return_sequences=1)
    print("\nAI:", output[0]['generated_text'])

