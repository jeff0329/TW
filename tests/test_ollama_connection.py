#!/usr/bin/env python3
"""
Ollama 連接測試工具
測試本地或遠程 Ollama 服務
"""

import os
import requests
import json
import logging
from typing import Tuple, Dict, Any
import pytest

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_ollama_connection(base_url: str = "http://localhost:11434") -> Tuple[bool, str]:
    """Test Ollama service connection"""
    try:
        logger.info(f"Testing Ollama connection: {base_url}")
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            logger.info(f"Connection successful!")
            logger.info(f"Available models: {len(models)}")
            for model in models:
                logger.info(f"  - {model['name']}")
            return True, "Connected"
        else:
            return False, f"Status code: {response.status_code}"
    except requests.exceptions.ConnectionError as e:
        return False, f"Connection refused: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_ollama_generation(base_url: str, model: str, prompt: str, timeout_seconds: float = 60.0) -> Tuple[bool, str]:
    """Test Ollama generation"""
    try:
        logger.info(f"Testing generation with model: {model}")
        
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=timeout_seconds
        )
        
        if response.status_code == 200:
            result = response.json()
            return True, result.get("response", "")
        else:
            return False, f"Status code: {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def interactive_test():
    """Interactive testing interface"""
    print("\n" + "="*60)
    print("Ollama 連接測試工具")
    print("="*60)
    
    # Get Ollama URL
    default_url = "http://localhost:11434"
    user_url = input(f"\nEnter Ollama URL (default: {default_url}): ").strip()
    ollama_url = user_url if user_url else default_url
    
    # Test connection
    print("\n[1] Testing connection...")
    success, message = check_ollama_connection(ollama_url)
    
    if not success:
        logger.error(f"Failed to connect: {message}")
        print("\nTroubleshooting tips:")
        print("  - Check if Ollama is running: ollama serve")
        print("  - Check firewall settings")
        print("  - Verify the URL and port")
        print(f"  - Try: curl {ollama_url}/api/tags")
        return
    
    logger.info(f"Connection successful to {ollama_url}")
    
    # Get available models
    print("\n[2] Getting available models...")
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        models = response.json().get("models", [])
        
        if not models:
            logger.error("No models available!")
            print("Download a model first: ollama pull llama2")
            return
        
        print("\nAvailable models:")
        for i, model in enumerate(models):
            print(f"  {i+1}. {model['name']}")
        
        # Select model
        choice = input(f"\nSelect model (1-{len(models)}): ").strip()
        try:
            model_idx = int(choice) - 1
            if 0 <= model_idx < len(models):
                selected_model = models[model_idx]['name']
            else:
                selected_model = models[0]['name']
        except:
            selected_model = models[0]['name']
        
        logger.info(f"Selected model: {selected_model}")
        
        # Test generation
        print("\n[3] Testing AI generation...")
        test_prompt = "台灣最受歡迎的旅遊景點有哪些？請列出5個。"
        logger.info(f"Prompt: {test_prompt}")
        
        success, response_text = check_ollama_generation(ollama_url, selected_model, test_prompt)
        
        if success:
            logger.info("Generation successful!")
            print("\nAI Response:")
            print("-" * 60)
            print(response_text)
            print("-" * 60)
        else:
            logger.error(f"Generation failed: {response_text}")
        
    except Exception as e:
        logger.error(f"Error: {e}")


def test_ollama_connection():
    """Pytest: verify Ollama API is reachable when service is running."""
    success, message = check_ollama_connection()
    if not success:
        pytest.skip(f"Ollama unavailable: {message}")
    assert success, message


def test_ollama_generation():
    """Pytest: verify text generation works for at least one available model."""
    base_url = "http://localhost:11434"
    success, message = check_ollama_connection(base_url)
    if not success:
        pytest.skip(f"Ollama unavailable: {message}")

    response = requests.get(f"{base_url}/api/tags", timeout=5)
    response.raise_for_status()
    models = response.json().get("models", [])
    if not models:
        pytest.skip("No Ollama models available")

    model_name = models[0]["name"]
    timeout_seconds = float(os.getenv("OLLAMA_TEST_TIMEOUT", "90"))

    gen_success, response_text = check_ollama_generation(
        base_url=base_url,
        model=model_name,
        prompt="請列出台灣三個熱門旅遊城市。",
        timeout_seconds=timeout_seconds
    )

    if not gen_success and "Read timed out" in response_text:
        pytest.skip(f"Generation timed out after {timeout_seconds}s")

    assert gen_success, response_text
    assert isinstance(response_text, str)
    assert response_text.strip() != ""


if __name__ == "__main__":
    interactive_test()
