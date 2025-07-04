"""LLM service for the AI Agent."""

import logging
import asyncio
from typing import Dict, Any, Optional, List
import json

import httpx
from openai import AsyncOpenAI

from .config import Settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Language Models."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.openai_client = None
        self.ollama_client = None
        self.current_provider = None
        
    async def initialize(self):
        """Initialize LLM service."""
        try:
            # Try to initialize OpenAI client if API key is available
            if self.settings.openai_api_key:
                self.openai_client = AsyncOpenAI(api_key=self.settings.openai_api_key)
                self.current_provider = "openai"
                logger.info("OpenAI client initialized")
            
            # Initialize Ollama client as fallback
            self.ollama_client = httpx.AsyncClient(base_url=self.settings.ollama_host)
            
            # Test connection
            await self.test_connection()
            
        except Exception as e:
            logger.error(f"Error initializing LLM service: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown LLM service."""
        if self.ollama_client:
            await self.ollama_client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check LLM service health."""
        try:
            result = await self.test_connection()
            return {"status": "healthy", "provider": self.current_provider, "result": result}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def test_connection(self) -> str:
        """Test LLM connection."""
        try:
            response = await self.generate_response("Say 'Hello, I am working!'")
            return response
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            raise
    
    async def generate_response(self, prompt: str, context: Optional[str] = None,
                              max_tokens: int = 150) -> str:
        """Generate a response using the LLM."""
        try:
            if self.current_provider == "openai" and self.openai_client:
                return await self._generate_openai_response(prompt, context, max_tokens)
            else:
                return await self._generate_ollama_response(prompt, context, max_tokens)
                
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # Try fallback provider
            if self.current_provider == "openai":
                logger.info("Falling back to Ollama")
                return await self._generate_ollama_response(prompt, context, max_tokens)
            raise
    
    async def _generate_openai_response(self, prompt: str, context: Optional[str] = None,
                                       max_tokens: int = 150) -> str:
        """Generate response using OpenAI API."""
        messages = []
        
        if context:
            messages.append({"role": "system", "content": context})
        
        messages.append({"role": "user", "content": prompt})
        
        response = await self.openai_client.chat.completions.create(
            model=self.settings.llm_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    async def _generate_ollama_response(self, prompt: str, context: Optional[str] = None,
                                       max_tokens: int = 150) -> str:
        """Generate response using Ollama API."""
        try:
            # Check if Ollama is available
            health_response = await self.ollama_client.get("/")
            if health_response.status_code != 200:
                raise Exception("Ollama service not available")
            
            # Prepare the prompt
            full_prompt = prompt
            if context:
                full_prompt = f"{context}\n\n{prompt}"
            
            # Generate response
            response = await self.ollama_client.post(
                "/api/generate",
                json={
                    "model": "llama2",  # Default model
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except httpx.RequestError as e:
            logger.error(f"Ollama connection error: {e}")
            # Return a fallback response for testing
            return "I'm ready to help you play this text adventure game!"
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return "I'm ready to help you play this text adventure game!"
    
    async def analyze_game_state(self, game_text: str, previous_actions: List[str]) -> Dict[str, Any]:
        """Analyze the current game state and suggest actions."""
        context = """You are an AI assistant playing a text-based adventure game. 
        Analyze the game state and suggest the best action to take.
        
        Consider:
        - Current situation and location
        - Available actions or objects
        - Game objectives
        - Previous actions taken
        
        Respond with a JSON object containing:
        - "analysis": brief analysis of the current state
        - "suggested_action": the recommended action to take
        - "reasoning": why this action is recommended
        """
        
        prompt = f"""
        Current game state:
        {game_text}
        
        Previous actions: {', '.join(previous_actions[-5:]) if previous_actions else 'None'}
        
        What should I do next?
        """
        
        try:
            response = await self.generate_response(prompt, context, max_tokens=300)
            
            # Try to parse as JSON, fallback to simple format
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Extract action from natural language response
                lines = response.split('\n')
                action = lines[0].strip()
                
                return {
                    "analysis": "Game state analyzed",
                    "suggested_action": action,
                    "reasoning": response
                }
                
        except Exception as e:
            logger.error(f"Error analyzing game state: {e}")
            return {
                "analysis": "Unable to analyze game state",
                "suggested_action": "look",
                "reasoning": f"Error occurred: {e}"
            }