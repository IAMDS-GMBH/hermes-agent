/**
 * Model fetching utilities for litellm API
 */

import { fetch } from '@tauri-apps/plugin-http'

export interface ModelInfo {
  id: string
  [key: string]: unknown
}

export interface ModelsResponse {
  object: string
  data: ModelInfo[]
}

/**
 * Fetch available models from a litellm endpoint
 * @param baseUrl - Base URL (e.g., https://suite.example.com)
 * @param apiKey - API key for authentication
 * @returns Array of model IDs
 */
export async function fetchModelsFromLitellm(
  baseUrl: string,
  apiKey: string
): Promise<string[]> {
  // Normalize base URL by removing trailing slash
  const normalizedUrl = baseUrl.trim().replace(/\/$/, '')
  const endpoint = `${normalizedUrl}/litellm/v1/models`

  console.log('[fetchModelsFromLitellm] Fetching from:', endpoint)

  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    })

    console.log('[fetchModelsFromLitellm] Response status:', response.status)

    if (response.status !== 200) {
      try {
        const text = await response.text()
        const errorData = text ? JSON.parse(text) : {}
        console.log('[fetchModelsFromLitellm] Error data:', errorData)
        const errorMessage =
          errorData.error?.message ||
          errorData.message ||
          `HTTP ${response.status}`
        throw new Error(errorMessage)
      } catch (e) {
        console.log('[fetchModelsFromLitellm] Could not parse error response:', e)
        throw new Error(`HTTP ${response.status}`)
      }
    }

    const text = await response.text()
    const data: ModelsResponse = JSON.parse(text)
    console.log('[fetchModelsFromLitellm] Response data:', data)

    // Extract model IDs from the response
    if (Array.isArray(data.data)) {
      const models = data.data.map((model) => model.id).sort()
      console.log('[fetchModelsFromLitellm] Extracted models:', models)
      if (models.length === 0) {
        throw new Error('No models found in response')
      }
      return models
    }

    throw new Error('Invalid response format: missing data array')
  } catch (error) {
    console.error('[fetchModelsFromLitellm] Error:', error)
    if (error instanceof Error) {
      throw error
    }
    throw new Error(`Failed to fetch models: ${String(error)}`)
  }
}
