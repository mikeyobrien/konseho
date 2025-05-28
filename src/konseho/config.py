"""Configuration management for Konseho model providers."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class ModelConfig:
    """Configuration for a model provider."""
    provider: str
    model_id: str
    api_key: str | None = None
    additional_args: dict[str, Any] | None = None


def get_model_config() ->ModelConfig:
    """Get model configuration from environment variables.

    Returns:
        ModelConfig object with provider settings
    """
    provider = os.getenv('DEFAULT_PROVIDER', 'bedrock').lower()
    if provider == 'openai':
        return ModelConfig(provider='openai', model_id=os.getenv(
            'DEFAULT_MODEL', 'gpt-4'), api_key=os.getenv('OPENAI_API_KEY'),
            additional_args={'temperature': float(os.getenv('TEMPERATURE',
            '0.7')), 'max_tokens': int(os.getenv('MAX_TOKENS', '2000'))})
    elif provider == 'anthropic':
        return ModelConfig(provider='anthropic', model_id=os.getenv(
            'DEFAULT_MODEL', 'claude-sonnet-4-20250514'), api_key=os.getenv
            ('ANTHROPIC_API_KEY'), additional_args={'temperature': float(os
            .getenv('TEMPERATURE', '0.7')), 'max_tokens': int(os.getenv(
            'MAX_TOKENS', '2000'))})
    elif provider == 'bedrock':
        return ModelConfig(provider='bedrock', model_id=os.getenv(
            'DEFAULT_MODEL', 'anthropic.claude-3-sonnet-20240229-v1:0'),
            additional_args={'region_name': os.getenv('AWS_DEFAULT_REGION',
            'us-east-1')})
    elif provider == 'ollama':
        return ModelConfig(provider='ollama', model_id=os.getenv(
            'DEFAULT_MODEL', 'llama2'), additional_args={'host': os.getenv(
            'OLLAMA_HOST', 'http://localhost:11434')})
    else:
        return ModelConfig(provider='bedrock', model_id=
            'anthropic.claude-3-sonnet-20240229-v1:0')


def create_model_from_config(config: (ModelConfig | None)=None):
    """Create a Strands model instance from configuration.

    Args:
        config: Optional ModelConfig, uses environment if not provided

    Returns:
        Configured model instance for use with Strands agents
    """
    if config is None:
        config = get_model_config()
    try:
        if config.provider == 'openai':
            from strands.models.openai import OpenAIModel
            return OpenAIModel(client_args={'api_key': config.api_key},
                model_id=config.model_id, **config.additional_args or {})
        elif config.provider == 'anthropic':
            from strands.models.anthropic import AnthropicModel
            additional_args = config.additional_args or {}
            max_tokens = additional_args.get('max_tokens', 2000)
            temperature = additional_args.get('temperature', 0.7)
            model = AnthropicModel(client_args={'api_key': config.api_key},
                model_id=config.model_id)
            model.config = {'max_tokens': max_tokens, 'model_id': config.
                model_id, 'temperature': temperature}
            return model
        elif config.provider == 'ollama':
            from strands.models.ollama import OllamaModel
            return OllamaModel(model_id=config.model_id, host=config.
                additional_args.get('host') if config.additional_args else None
                )
        elif config.provider == 'bedrock':
            return config.model_id
        else:
            raise ValueError(f'Unknown provider: {config.provider}')
    except ImportError as e:
        raise ImportError(
            f"Provider '{config.provider}' not installed. Install with: pip install strands-agents[{config.provider}]"
            ) from e
    except Exception as e:
        raise RuntimeError(f'Failed to create model: {e}') from e


def print_config_info():
    """Print current configuration information."""
    config = get_model_config()
    print(f'Provider: {config.provider}')
    print(f'Model: {config.model_id}')
    print(f"API Key: {'Set' if config.api_key else 'Not set'}")
    if config.additional_args:
        print(f'Additional args: {config.additional_args}')
