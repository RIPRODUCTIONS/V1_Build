#!/usr/bin/env python3
"""
Simple GPT-2 text generation test script.
This script attempts to load GPT-2 model, with fallback for offline environments.
"""

try:
    from transformers import pipeline
    
    print("🚀 Loading GPT-2 model...")
    # Try to load the model with offline fallback
    try:
        generator = pipeline("text-generation", model="gpt2")
        
        # Generate text
        result = generator("Once upon a time in the future,", max_length=50, num_return_sequences=1)
        
        print("✅ GPT-2 model loaded successfully!")
        print("\n📝 Generated text:")
        print(result[0]['generated_text'])
        
    except Exception as model_error:
        print(f"⚠️  Could not load GPT-2 model: {model_error}")
        print("💡 This might be due to no internet connection or missing model files.")
        print("📋 The transformers library is installed correctly.")
        
except ImportError as import_error:
    print(f"❌ Missing dependency: {import_error}")
    print("💡 Please run: pip3 install -r requirements.txt")
