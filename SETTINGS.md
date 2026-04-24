# OpenExec Settings Configuration

This document explains how to configure `settings.json` for different AI providers and local LLM setups.

## Settings Structure

```json
{
  "agents": {
    "analysis_depth": "medium",
    "confidence_threshold": 0.6,
    "enabled": ["ceo", "cfo", "cto", "cmo"],
    "max_interactions": 10
  },
  "ai": {
    "api_key": "",
    "base_url": "http://localhost:11434/v1",
    "max_tokens": 4096,
    "model": "llama3",
    "provider": "openai_compatible",
    "temperature": 0.7,
    "timeout": 120
  },
  "output": {
    "format": "markdown",
    "include_sections": [
      "executive_summary",
      "individual_reports",
      "synthesized_recommendations",
      "risk_assessment"
    ]
  },
  "simulation": {
    "phases": [
      {"name": "inception", "weight": 0.1},
      {"name": "analysis", "weight": 0.5},
      {"name": "review", "weight": 0.25},
      {"name": "synthesis", "weight": 0.1}
    ]
  }
}
```

## AI Configuration Examples

### 1. Ollama (Local LLM)

```json
{
  "ai": {
    "base_url": "http://localhost:11434/v1",
    "model": "llama3",
    "temperature": 0.7,
    "max_tokens": 4096,
    "api_key": "",
    "timeout": 120
  }
}
```

**Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3

# Start Ollama server (usually runs automatically)
ollama serve
```

### 2. vLLM (Local LLM Server)

```json
{
  "ai": {
    "base_url": "http://localhost:8000/v1",
    "model": "meta-llama/Llama-2-7b-chat-hf",
    "temperature": 0.7,
    "max_tokens": 4096,
    "api_key": "",
    "timeout": 120
  }
}
```

**Setup:**
```bash
# Install vLLM
pip install vllm

# Start vLLM server
python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-2-7b-chat-hf
```

### 3. OpenAI API

```json
{
  "ai": {
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 4096,
    "api_key": "sk-your-openai-api-key",
    "timeout": 120
  }
}
```

### 4. Anthropic (via OpenAI-compatible endpoint)

```json
{
  "ai": {
    "base_url": "https://api.anthropic.com/v1",
    "model": "claude-3-5-sonnet-20241022",
    "temperature": 0.7,
    "max_tokens": 4096,
    "api_key": "sk-ant-your-anthropic-api-key",
    "timeout": 120
  }
}
```

### 5. LocalAI (OpenAI-compatible local server)

```json
{
  "ai": {
    "base_url": "http://localhost:8080/v1",
    "model": "ggml-gpt4all-j",
    "temperature": 0.7,
    "max_tokens": 4096,
    "api_key": "",
    "timeout": 120
  }
}
```

**Setup:**
```bash
# Install LocalAI
curl https://localai.io/install.sh | sh

# Start LocalAI
localai start
```

### 6. Together AI

```json
{
  "ai": {
    "base_url": "https://api.together.xyz/v1",
    "model": "meta-llama/Llama-2-70b-chat-hf",
    "temperature": 0.7,
    "max_tokens": 4096,
    "api_key": "your-together-ai-api-key",
    "timeout": 120
  }
}
```

## Configuration Parameters

### AI Settings

- **base_url**: Base URL for the API endpoint (required)
- **model**: Model name/identifier (required)
- **api_key**: API key (optional for local models)
- **temperature**: Sampling temperature (0.0-1.0, default: 0.7)
- **max_tokens**: Maximum tokens in response (default: 4096)
- **timeout**: Request timeout in seconds (default: 120)
- **provider**: Provider identifier (for reference, default: "openai_compatible")

### Agent Settings

- **enabled**: List of agent names to use (default: ["ceo", "cfo", "cto", "cmo"])
- **analysis_depth**: Analysis depth level (default: "medium")
- **confidence_threshold**: Minimum confidence for recommendations (default: 0.6)
- **max_interactions**: Maximum agent feedback loop iterations (default: 10)

### Output Settings

- **format**: Output format (default: "markdown")
- **include_sections**: Sections to include in report

## Troubleshooting

### Connection Issues

If you get connection errors:

1. **Check if the service is running:**
   ```bash
   curl http://localhost:11434/v1/models
   ```

2. **Verify the base_url in settings.json**

3. **Check firewall settings**

### Model Not Found

If you get "model not found" errors:

1. **Verify the model name matches exactly what the service expects**

2. **For Ollama, check available models:**
   ```bash
   ollama list
   ```

3. **For vLLM, ensure the model is downloaded and loaded**

### Timeout Issues

If requests timeout:

1. **Increase the timeout value in settings.json**

2. **Check if your local hardware can handle the model**

3. **Consider using a smaller model**

## Performance Tips

### For Local Models

1. **Use quantized models** (e.g., `llama3:8b` instead of `llama3:70b`)

2. **Adjust max_tokens** based on your needs

3. **Use GPU acceleration** if available

4. **Consider model size vs. quality tradeoffs**

### For Cloud APIs

1. **Monitor API usage and costs**

2. **Use appropriate model tiers**

3. **Implement rate limiting if needed**

## Security Notes

- **Never commit API keys** to version control
- **Use environment variables** for sensitive data when possible
- **Restrict API key permissions** to minimum required
- **Rotate API keys regularly**
- **Use separate keys for development/production**
