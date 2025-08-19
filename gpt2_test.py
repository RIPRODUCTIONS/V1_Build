#!/usr/bin/env python3
"""
GPT-2 Text Generation Test Script
Demonstrates basic text generation with proper error handling and logging.
"""

import logging
import sys
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_model() -> Optional[Any]:
    """Load GPT-2 text generation model with error handling."""
    try:
        from transformers import pipeline
        logger.info("Loading GPT-2 model...")
        generator = pipeline(
            "text-generation", 
            model="gpt2",
            device_map="auto" if sys.platform != "darwin" else None  # Handle Mac compatibility
        )
        logger.info("Model loaded successfully")
        return generator
    except ImportError as e:
        logger.error(f"Failed to import transformers: {e}")
        logger.error("Please install with: pip install transformers torch")
        return None
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None

def generate_text(generator: Any, prompt: str, max_length: int = 50) -> Optional[str]:
    """Generate text with the given prompt and parameters."""
    try:
        if not prompt.strip():
            logger.warning("Empty prompt provided")
            return None
            
        logger.info(f"Generating text for prompt: '{prompt[:50]}...'")
        result = generator(
            prompt, 
            max_length=max_length, 
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True,
            pad_token_id=generator.tokenizer.eos_token_id
        )
        
        if result and len(result) > 0:
            generated_text = result[0]['generated_text']
            logger.info("Text generation completed successfully")
            return generated_text
        else:
            logger.warning("No text was generated")
            return None
            
    except Exception as e:
        logger.error(f"Text generation failed: {e}")
        return None

def main():
    """Main function to run the GPT-2 test."""
    try:
        # Load model
        generator = load_model()
        if generator is None:
            logger.error("Failed to load model. Exiting.")
            sys.exit(1)
        
        # Test prompt
        prompt = "Once upon a time in the future,"
        
        # Generate text
        generated_text = generate_text(generator, prompt, max_length=50)
        
        if generated_text:
            print("\n" + "="*50)
            print("GENERATED TEXT:")
            print("="*50)
            print(generated_text)
            print("="*50)
        else:
            logger.error("Failed to generate text")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
