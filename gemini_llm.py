 
import os
import requests
from langchain.llms.base import LLM
from typing import Optional, List

class GeminiLLM(LLM):
    api_key: str
    api_url: str = "https://api.gemini.com/v1/completions"   
    model: str = "gemini-large"   
    temperature: float = 0.0
    max_tokens: int = 1000  #  

    @property
    def _llm_type(self) -> str:
        return "gemini"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            response_json = response.json()
            # Adjust response parsing based on Gemini's actual response structure
            return response_json.get("choices", [])[0].get("text", "")
        except requests.exceptions.RequestException as e:
            return f"An error occurred while communicating with the Gemini API: {e}"
        except (KeyError, IndexError) as e:
            return f"Unexpected response format from Gemini API: {e}"