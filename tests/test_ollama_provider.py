"""Tests for openexec/ai/ollama_provider.py — OllamaProvider."""

import pytest
from unittest.mock import patch, Mock
from openexec.ai.ollama_provider import OllamaProvider


def test_ollama_provider_complete():
    """Test that OllamaProvider can complete a prompt."""
    # Mock response for the chat/completions API
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "test output"}}]
    }
    mock_response.status_code = 200

    with patch('openexec.ai.ollama_provider.requests.post') as mock_post:
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
        assert url == "http://localhost:11434/chat/completions"

        payload = mock_post.call_args[1]['json']
        assert payload['model'] == "llama3"
        assert payload['messages'][0]['role'] == 'user'
        assert payload['messages'][0]['content'] == "Hello, Ollama!"


def test_ollama_provider_complete_json():
    """Test that OllamaProvider can complete and parse a prompt as JSON."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "{\"key\": \"value\"}"}}]
    }
    mock_response.status_code = 200

    with patch('openexec.ai.ollama_provider.requests.post') as mock_post:
        mock_post.return_value = mock_response

        ai_config = {
            "base_url": "http://localhost:11434",
            "model": "llama3"
        }
        provider = OllamaProvider(ai_config)

        # Mock _pipeline.parse to return our test JSON directly
        with patch.object(provider._pipeline, 'parse', return_value={"key": "value"}):
            result = provider.complete_json("Hello, Ollama!\n\nOutput as JSON only: {\"key\": \"value\"}")

        assert result == {"key": "value"}

        mock_post.assert_called()  # complete_json may call multiple times due to retry logic


def test_preprocess_bracket_strings_not_matched():
    """Braces inside strings should not affect bracket matching."""
    provider = OllamaProvider({"base_url": "http://localhost:11434", "model": "test"})

    from openexec.ai.json_utils import JSONPipeline
    pipeline = JSONPipeline()

    # Braces inside string values should not break extraction
    raw = '{"title": "Goal {2026}", "summary": "Cost {high}"}'
    result = pipeline._preprocess(raw)
    assert result == raw

    # Extra text after JSON should be stripped
    raw2 = 'Here is JSON: {\"key\": \"value\"} trailing text'
    result2 = pipeline._preprocess(raw2)
    assert result2 == '{\"key\": \"value\"}'


def test_preprocess_strips_markdown_fences():
    """Markdown code fences should be stripped from JSON."""
    from openexec.ai.json_utils import JSONPipeline
    pipeline = JSONPipeline()

    raw = '```json\n{\"key\": \"value\"}\n```'
    result = pipeline._preprocess(raw)
    assert result == '{\"key\": \"value\"}'


def test_complete_retries_on_timeout():
    """complete() should retry on timeout with exponential backoff."""
    from unittest.mock import Mock, patch
    import requests

    # First two calls timeout, third succeeds
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "success"}}]
    }
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()

    side_effects = [
        requests.exceptions.Timeout("Connection timed out"),
        requests.exceptions.Timeout("Connection timed out"),
        mock_response
    ]

    with patch('openexec.ai.ollama_provider.requests.post') as mock_post:
        mock_post.side_effect = side_effects
        with patch('time.sleep', return_value=None):  # Skip actual sleep
            ai_config = {
                "base_url": "http://localhost:11434",
                "model": "llama3",
                "timeout": 120,
                "max_retries": 2
            }
            provider = OllamaProvider(ai_config)
            result = provider.complete("Hello!")

    assert result == "success"
    assert mock_post.call_count == 3


def test_complete_fails_after_all_retries():
    """complete() should raise RuntimeError after exhausting retries."""
    from unittest.mock import Mock, patch
    import requests

    with patch('openexec.ai.ollama_provider.requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")
        with patch('time.sleep', return_value=None):
            ai_config = {
                "base_url": "http://localhost:11434",
                "model": "llama3",
                "timeout": 120,
                "max_retries": 2
            }
            provider = OllamaProvider(ai_config)
            with pytest.raises(RuntimeError) as exc_info:
                provider.complete("Hello!")
            assert "timed out" in str(exc_info.value).lower()
