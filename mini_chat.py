#!/usr/bin/env python3
"""
Mini ChatGPT-like interface using GPT-2 model.
This script provides a simple chat interface with fallback for offline environments.
"""

try:
    from transformers import pipeline
    
    print("🚀 Mini-ChatGPT Starting...")
    
    # Try to load GPT-2 model
    try:
        generator = pipeline("text-generation", model="gpt2")
        print("✅ GPT-2 model loaded successfully!")
        print("💬 Type your messages (or 'quit' to exit)")
        
        while True:
            prompt = input("\n🎯 You: ")
            if prompt.lower() in ['quit', 'exit', 'q']:
                break
            
            try:
                output = generator(prompt, max_length=80, num_return_sequences=1)
                print("🤖 AI:", output[0]['generated_text'])
            except Exception as gen_error:
                print(f"⚠️  Generation error: {gen_error}")
                
    except Exception as model_error:
        print(f"⚠️  Could not load GPT-2 model: {model_error}")
        print("💡 This might be due to no internet connection.")
        print("🔄 Falling back to simple echo mode...")
        
        while True:
            prompt = input("\n🎯 You: ")
            if prompt.lower() in ['quit', 'exit', 'q']:
                break
            print(f"🤖 Echo: You said '{prompt}' (GPT-2 model unavailable)")
                
except ImportError as import_error:
    print(f"❌ Missing dependency: {import_error}")
    print("💡 Please run: pip3 install -r requirements.txt")

print("\n👋 Goodbye!")

