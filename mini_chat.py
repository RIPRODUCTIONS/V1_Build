#!/usr/bin/env python3
"""
Mini-ChatGPT Interactive Chat Application
A simple interactive chat interface using GPT-2 with proper error handling.
"""

import logging
import sys
import signal
from typing import Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MiniChatGPT:
    """A simple chat interface using GPT-2."""
    
    def __init__(self):
        self.generator = None
        self.running = True
        
    def load_model(self) -> bool:
        """Load the GPT-2 model."""
        try:
            from transformers import pipeline
            logger.info("Loading GPT-2 model...")
            self.generator = pipeline(
                "text-generation", 
                model="gpt2",
                device_map="auto" if sys.platform != "darwin" else None
            )
            logger.info("Model loaded successfully")
            return True
        except ImportError as e:
            logger.error(f"Failed to import transformers: {e}")
            print("Please install with: pip install transformers torch")
            return False
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def generate_response(self, prompt: str) -> Optional[str]:
        """Generate a response for the given prompt."""
        try:
            if not prompt.strip():
                return "Please provide a valid prompt."
            
            # Limit prompt length to avoid memory issues
            if len(prompt) > 200:
                prompt = prompt[:200]
                logger.warning("Prompt truncated to 200 characters")
            
            result = self.generator(
                prompt,
                max_length=min(len(prompt.split()) + 50, 150),  # Dynamic max length
                num_return_sequences=1,
                temperature=0.8,
                do_sample=True,
                pad_token_id=self.generator.tokenizer.eos_token_id,
                truncation=True
            )
            
            if result and len(result) > 0:
                return result[0]['generated_text']
            else:
                return "Sorry, I couldn't generate a response."
                
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return "Sorry, an error occurred while generating the response."
    
    def handle_exit(self, signum, frame):
        """Handle graceful exit on signal."""
        print("\n\nGoodbye! 👋")
        self.running = False
        sys.exit(0)
    
    def run(self):
        """Run the interactive chat loop."""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        
        print("🚀 Mini-ChatGPT Ready!")
        print("Type 'quit', 'exit', or press Ctrl+C to exit")
        print("=" * 50)
        
        while self.running:
            try:
                prompt = input("\n🤔 You: ").strip()
                
                if not prompt:
                    continue
                    
                if prompt.lower() in ['quit', 'exit', 'bye']:
                    print("Goodbye! 👋")
                    break
                
                if prompt.lower() in ['help', '?']:
                    print("Commands:")
                    print("  help, ? - Show this help")
                    print("  quit, exit, bye - Exit the chat")
                    print("  Just type anything else to chat!")
                    continue
                
                print("🤖 AI: ", end="", flush=True)
                response = self.generate_response(prompt)
                print(response)
                
            except EOFError:
                print("\nGoodbye! 👋")
                break
            except KeyboardInterrupt:
                print("\nGoodbye! 👋")
                break
            except Exception as e:
                logger.error(f"Chat loop error: {e}")
                print("Sorry, an error occurred. Please try again.")

def main():
    """Main function."""
    try:
        chat = MiniChatGPT()
        
        if not chat.load_model():
            print("Failed to load the model. Please check your installation.")
            sys.exit(1)
        
        chat.run()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

