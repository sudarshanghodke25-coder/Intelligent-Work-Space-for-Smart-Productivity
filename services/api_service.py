import os
import openai

class AurexAPIClient:
    def __init__(self):
        self.provider = "Unknown"
        self.model = "Unknown"
        self.base_url = None
        self.api_key = None
        self.client = None
        self._init_client()

    def _init_client(self):
        import sys
        from pathlib import Path
        from dotenv import load_dotenv

        keys_to_check = ["AUREX_API_KEY", "NVIDIA_API_KEY", "GROQ_API_KEY", "OPENAI_API_KEY", "GITHUB_TOKEN", "HF_TOKEN"]
        token = None
        for key in keys_to_check:
            token = os.environ.get(key)
            if token:
                break
        
        if not token:
            # Attempt to reload .env from possible installation roots
            candidates = [
                Path(sys.executable).parent / ".env",
                Path(__file__).resolve().parent.parent / ".env",
                Path.cwd() / ".env"
            ]
            for c in candidates:
                if c.exists():
                    load_dotenv(dotenv_path=c, override=True)
                    break
            for key in keys_to_check:
                token = os.environ.get(key)
                if token:
                    break

        if not token:
            return

        self.api_key = token

        if token.startswith("sk-"):
            self.provider = "OpenAI"
            self.model = "gpt-4o-mini"
            self.base_url = "https://api.openai.com/v1"
            self.client = openai.OpenAI(api_key=self.api_key)
            
        elif token.startswith("gsk_"):
            self.provider = "Groq"
            self.model = "llama-3.1-8b-instant"
            self.base_url = "https://api.groq.com/openai/v1"
            self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            
        elif token.startswith("github_pat_") or token.startswith("ghp_"):
            self.provider = "GitHub Models"
            self.model = "gpt-4o-mini"
            self.base_url = "https://models.inference.ai.azure.com"
            self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            
        elif token.startswith("hf_"):
            self.provider = "Hugging Face"
            self.model = "meta-llama/Meta-Llama-3-8B-Instruct"
            self.base_url = "https://api-inference.huggingface.co/v1/"
            self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            
        elif token.startswith("nvapi-"):
            self.provider = "Nvidia API"
            self.model = "nvidia/nemotron-3.5-bolt-e4b"
            self.fallback_model = "nvidia/nemotron-3.5-lightning-30b-a3b"
            self.base_url = "https://integrate.api.nvidia.com/v1"
            self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            
        else:
            self.provider = "Unsupported"

    def get_diagnostics(self) -> dict:
        if not self.api_key:
            return {
                "status": "FAIL",
                "message": "No API Key found in environment variables."
            }
        
        if self.provider == "Unsupported":
            return {
                "status": "FAIL",
                "message": f"Token format unrecognized (starts with '{self.api_key[:5]}...'). Supported: sk-, gsk_, github_pat_, hf_, nvapi-"
            }
            
        return {
            "status": "PASS",
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url
        }

    def print_diagnostics(self):
        print("\n--- AUREX SYSTEM DIAGNOSTICS ---")
        diag = self.get_diagnostics()
        if diag["status"] == "FAIL":
            print(f"X SYSTEM ERROR: {diag['message']}")
        else:
            print(f"Provider Detected: {diag['provider']}")
            print(f"Model Loaded: {diag['model']}")
            print(f"Endpoint URL: {diag['base_url']}")
            print(f"Token Validation Result: {diag['status']}")
            
            raw_key = self.api_key
            print(f"KEY DETECTED! Total Length: {len(raw_key)} characters")
            print(f"KEY STARTS WITH: '{raw_key[:5]}'")
            print(f"KEY ENDS WITH: '{raw_key[-5:] if len(raw_key) > 5 else ''}'")
        print("----------------------------------------\n")

    def _normalize_response(self, response):
        """Extract content or reasoning_content so choices[0].message.content is never empty."""
        if not response or not hasattr(response, "choices"):
            return response
        for choice in response.choices:
            if hasattr(choice, "message"):
                msg = choice.message
                if getattr(msg, "content", None) is None:
                    reasoning = getattr(msg, "reasoning_content", None)
                    if reasoning:
                        msg.content = reasoning
        return response

    def chat_completions_create(self, messages, model=None, response_format=None, temperature=0.7, max_tokens=1024):
        if not self.client:
            raise ValueError("AI Client not initialized properly. Check diagnostics.")
            
        target_model = model or self.model
        kwargs = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if response_format:
            if self.provider != "Hugging Face":
                kwargs["response_format"] = response_format
                
        try:
            resp = self.client.chat.completions.create(**kwargs)
            return self._normalize_response(resp)
        except Exception as e:
            # If primary model fails and a fallback is configured, try fallback
            fallback = getattr(self, "fallback_model", None)
            if fallback and target_model != fallback and self.provider == "Nvidia API":
                try:
                    kwargs["model"] = fallback
                    # Ensure reasoning models have enough tokens to output response
                    if kwargs.get("max_tokens", 0) < 384:
                        kwargs["max_tokens"] = 512
                    resp = self.client.chat.completions.create(**kwargs)
                    return self._normalize_response(resp)
                except Exception:
                    pass
            raise e

    def audio_transcriptions_create(self, file, model="whisper-1"):
        if not self.client:
            raise ValueError("AI Client not initialized properly. Check diagnostics.")
        
        if self.provider == "Groq":
            model = "whisper-large-v3"
            
        return self.client.audio.transcriptions.create(
            file=file,
            model=model
        )

    def vision_analysis(self, prompt: str, base64_images: list[str], model=None) -> str:
        if not self.client:
            raise ValueError("AI Client not initialized properly.")
            
        if not model:
            if self.provider == "Nvidia API":
                model = "nvidia/nemotron-3.5-super-vl-120b-a12b"
            else:
                model = "meta/llama-3.2-11b-vision-instruct"

        content = [{"type": "text", "text": prompt}]
        for b64 in base64_images:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{b64}"
                }
            })
            
        messages = [
            {
                "role": "user",
                "content": content
            }
        ]
        
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=512,
            temperature=0.7
        )
        self._normalize_response(response)
        msg = response.choices[0].message
        return msg.content or getattr(msg, "reasoning_content", "") or ""

# Global singleton
aurex_api = AurexAPIClient()
