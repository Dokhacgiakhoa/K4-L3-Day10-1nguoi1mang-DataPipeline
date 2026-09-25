from __future__ import annotations

from dataclasses import replace

import pytest

from core.config import normalized_provider, require_llm_credentials


def _with_provider(settings, provider, **overrides):
    return replace(settings, llm_provider=provider, **overrides)


def test_normalized_provider_lowercases_and_strips_separators(base_settings):
    s = _with_provider(base_settings, "Google-Gen AI")
    assert normalized_provider(s) == "googlegenai"


def test_normalized_provider_fixes_anthorpic_typo(base_settings):
    s = _with_provider(base_settings, "anthorpic")
    assert normalized_provider(s) == "anthropic"


def test_normalized_provider_maps_custom_llm(base_settings):
    s = _with_provider(base_settings, "custom-llm")
    assert normalized_provider(s) == "custom"


@pytest.mark.parametrize("provider", ["mock", "ollama"])
def test_require_llm_credentials_no_key_needed(base_settings, provider):
    s = _with_provider(base_settings, provider)
    require_llm_credentials(s)  # phai khong raise


def test_require_llm_credentials_gemini_needs_google_key(base_settings):
    s = _with_provider(base_settings, "gemini", google_api_key=None)
    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        require_llm_credentials(s)


def test_require_llm_credentials_gemini_passes_with_key(base_settings):
    s = _with_provider(base_settings, "gemini", google_api_key="fake-key")
    require_llm_credentials(s)


def test_require_llm_credentials_openai_needs_key(base_settings):
    s = _with_provider(base_settings, "openai", openai_api_key=None)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        require_llm_credentials(s)


def test_require_llm_credentials_anthropic_needs_key(base_settings):
    s = _with_provider(base_settings, "anthropic", anthropic_api_key=None)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        require_llm_credentials(s)


def test_require_llm_credentials_openrouter_needs_key(base_settings):
    s = _with_provider(base_settings, "openrouter", openrouter_api_key=None)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        require_llm_credentials(s)


def test_require_llm_credentials_custom_needs_base_url(base_settings):
    s = _with_provider(base_settings, "custom", custom_llm_base_url=None)
    with pytest.raises(RuntimeError, match="CUSTOM_LLM_BASE_URL"):
        require_llm_credentials(s)


def test_require_llm_credentials_unsupported_provider_raises(base_settings):
    s = _with_provider(base_settings, "not-a-real-provider")
    with pytest.raises(RuntimeError, match="Unsupported LLM_PROVIDER"):
        require_llm_credentials(s)


def test_load_settings_paths_point_under_project_dir(base_settings):
    assert base_settings.paths.clean_json.is_relative_to(base_settings.paths.project_dir)
    assert base_settings.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
    assert base_settings.top_k > 0
    assert base_settings.freshness_threshold_days == 180
