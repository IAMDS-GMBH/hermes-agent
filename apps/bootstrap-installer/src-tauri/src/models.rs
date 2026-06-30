//! Fetch available models from litellm endpoint and cache them.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize)]
pub struct ModelInfo {
    pub id: String,
    #[serde(flatten)]
    pub extra: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ModelsResponse {
    pub object: String,
    pub data: Vec<ModelInfo>,
}

/// Provider model cache entry (matches hermes-agent's structure).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProviderCacheEntry {
    pub fp: String,       // "pinned" or timestamp
    pub at: f64,          // timestamp
    pub models: Vec<String>,
}

/// Full provider models cache structure.
#[derive(Debug, Serialize, Deserialize)]
pub struct ProviderModelsCache {
    #[serde(flatten)]
    pub providers: std::collections::HashMap<String, ProviderCacheEntry>,
}

/// Fetch available models from a litellm endpoint (server-side).
///
/// This bypasses Tauri's ACL restrictions on client-side HTTP by doing the
/// fetch on the Rust side and returning the results to the frontend.
#[tauri::command]
pub async fn fetch_models(base_url: String, api_key: String) -> Result<Vec<String>, String> {
    let normalized_url = base_url.trim().trim_end_matches('/');
    let endpoint = format!("{}/litellm/v1/models", normalized_url);

    tracing::info!("Fetching models from: {}", endpoint);

    let client = reqwest::Client::new();
    let response = client
        .get(&endpoint)
        .header("Authorization", format!("Bearer {}", api_key))
        .header("Content-Type", "application/json")
        .send()
        .await
        .map_err(|e| format!("Network error: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("HTTP {}: {}", response.status(), response.status().canonical_reason().unwrap_or("Unknown")));
    }

    let data: ModelsResponse = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    let mut models: Vec<String> = data
        .data
        .into_iter()
        .map(|m| m.id.trim().to_string())
        .filter(|id| !id.is_empty() && !id.starts_with('_'))
        .collect();
    models.sort();

    if models.is_empty() {
        return Err("No models found in response".to_string());
    }

    tracing::info!("Fetched {} models", models.len());
    Ok(models)
}

/// Write provider_models_cache.json with fetched LiteLLM models pinned for OpenAI slugs.
///
/// Updates `~/.hermes/provider_models_cache.json` while preserving unrelated
/// provider cache entries (so reinstall does not wipe prior discovery state).
/// The installer pins `iamds-litellm`, `openai-api` and `openai` to the fetched
/// list and removes Copilot cache entries to keep the picker aligned with the
/// bootstrap LiteLLM endpoint.
#[tauri::command]
pub async fn write_provider_models_cache(
    hermes_home: Option<String>,
    model_names: Vec<String>,
) -> Result<(), String> {
    if model_names.is_empty() {
        return Err("No models provided".to_string());
    }

    // Determine HERMES_HOME path
    let hermes_home_path = if let Some(home) = hermes_home {
        PathBuf::from(home)
    } else {
        // Use the platform-correct default: %LOCALAPPDATA%\hermes on Windows,
        // ~/.hermes on macOS/Linux — mirrors paths::hermes_home() exactly.
        crate::paths::hermes_home()
    };

    let cache_file = hermes_home_path.join("provider_models_cache.json");

    // Load existing cache so reinstall/update keeps previously discovered
    // provider entries instead of blowing them away.
    let mut providers: std::collections::HashMap<String, ProviderCacheEntry> = if cache_file.exists()
    {
        match std::fs::read_to_string(&cache_file) {
            Ok(raw) => serde_json::from_str::<ProviderModelsCache>(&raw)
                .map(|c| c.providers)
                .unwrap_or_default(),
            Err(_) => std::collections::HashMap::new(),
        }
    } else {
        std::collections::HashMap::new()
    };

    // Keep the bootstrap UX opinionated: no Copilot catalog in this path.
    providers.remove("copilot");
    providers.remove("copilot-acp");

    let pinned_entry = ProviderCacheEntry {
        fp: "pinned".to_string(),
        at: 9999999999.0, // Far future timestamp to indicate this is pinned
        models: model_names,
    };

    providers.insert(
        "iamds-litellm".to_string(),
        pinned_entry.clone(),
    );
    providers.insert(
        "openai-api".to_string(),
        pinned_entry.clone(),
    );
    providers.insert(
        "openai".to_string(),
        pinned_entry,
    );

    let model_count = providers
        .get("iamds-litellm")
        .map(|entry| entry.models.len())
        .unwrap_or(0);
    let cache = ProviderModelsCache { providers };

    // Write cache file (overwrites any existing cache to ensure clean state)
    let json_str = serde_json::to_string(&cache)
        .map_err(|e| format!("Failed to serialize cache: {}", e))?;

    std::fs::write(&cache_file, json_str)
        .map_err(|e| format!("Failed to write cache file: {}", e))?;

    tracing::info!(
        "Wrote provider models cache to: {} (pinned iamds-litellm/openai/openai-api, {} models)",
        cache_file.display(),
        model_count
    );
    Ok(())
}
