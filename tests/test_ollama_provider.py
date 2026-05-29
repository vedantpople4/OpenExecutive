import pytest
from unittest.mock import patch, Mock
from src.ai.ollama_provider import OllamaProvider

def test_ollama_provider_complete():
    """Test that OllamaProvider can complete a prompt."""
    mock_response = Mock()
    mock_response.json.return_value = {"response": "test output"}
    mock_response.status_code = 200
    
    with patch('src.ai.ollama_provider.requests.post') as mock_post:
        mock_post.return_value = mock_response
        
        ai_config = {
            "base_url": "http://localhost:11434",
            "model": "llama3"
        }
        provider = OllamaProvider(ai_config)
        
        result = provider.complete("Hello, Ollama!")
        
        assert result == "test output"
        
        mock_post.assert_called_once()
        
        url = mock_post.call_args[0][0]
        assert url == "http://localhost:11434/api/generate"
        
        payload = mock_post.call_args[1]['json']
        assert payload['model'] == "llama3"
        
        assert mock_post.call_args[1]['json']['messages'][0]['content'] == "Hello, Ollama!"

def test_ollama_provider_complete_json():
    """Test that OllamaProvider can complete and parse a prompt as JSON."""
    mock_response = Mock()
    mock_response.json.return_value = {"response": "{\"key\": \"value\"}"}
    mock_response.status_code = 200
    
    with patch('src.ai.ollama_provider.requests.post') as mock_post:
        mock_post.return_value = mock_response
        
        ai_config = {
            "base_url": "http://localhost:11434",
            "model": "llama3"
        }
        provider = OllamaProvider(ai_config)
        
        result = provider.complete_json("Hello, Ollama!\n\nOutput as JSON only: {\"key\": \"value\"}")
        
        assert result == {"key": "value"}
        
        mock_post.assert_called_once()
        
        url = mock_post.call_args[0][0]
        assert url == "http://localhost:11434/api/generate"
        
        payload = mock_post.call_args[1]['json']
        assert payload['model'] == "llama3"
        
        assert mock_post.call_args[1]['json']['messages'][0]['content'] == "Hello, Ollama!\n\nOutput as JSON only: {\"key\": \"value\"}"