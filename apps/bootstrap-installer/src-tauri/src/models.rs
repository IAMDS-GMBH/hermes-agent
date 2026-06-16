//! Fetch available models from litellm endpoint.

use serde::{Deserialize, Serialize};

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

    let mut models: Vec<String> = data.data.into_iter().map(|m| m.id).collect();
    models.sort();

    if models.is_empty() {
        return Err("No models found in response".to_string());
    }

    tracing::info!("Fetched {} models", models.len());
    Ok(models)
}
