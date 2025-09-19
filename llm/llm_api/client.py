import os
import multiprocessing
from typing import Dict, List, Optional
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv
import torch

load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"
try:
    multiprocessing.set_start_method("spawn", force=True)
except RuntimeError:

    pass


class LLMClient:
    def __init__(self, model_name: str = "LiquidAI/LFM2-1.2B", device: Optional[str] = None):
        self.model_name = model_name  
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.setup_model()
    
    def setup_model(self):
        """Initialize the Hugging Face model and tokenizer"""
        try:
            if self.device == "cpu":
                self.model_name = "LiquidAI/LFM2-1.2B"
            
            print(f"Loading model: {self.model_name} on {self.device}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                padding_side="left"
            )

            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.generator = pipeline(
                "text-generation",
                model=self.model_name,
                tokenizer=self.tokenizer,  
                device=-1 if self.device == "cpu" else 0,
                dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            print(f"✅ Model loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.generator = None
            self.tokenizer = None
    
    def generate_completion(self, prompt: str, **kwargs) -> str:
        """Generate text completion using Hugging Face model"""
        if self.generator is None or self.tokenizer is None:
            return "Model not available. Please check the model setup."
        
        try:
            response = self.generator(
                prompt,
                max_new_tokens=kwargs.get("max_new_tokens", 2048),
                num_return_sequences=1,
                temperature=kwargs.get("temperature", 0.3),
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                return_full_text=False,
                min_p=0.15,
                repetition_penalty=1.05
            )
            
            # Extract the generated text
            generated_text = response[0]['generated_text']
            
            return generated_text
            
        except Exception as e:
            print(f"Error generating completion: {e}")
            return ""
