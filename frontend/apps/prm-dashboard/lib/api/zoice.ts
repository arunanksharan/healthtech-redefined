/**
 * Zoice API Module
 *
 * API calls for Zoice voice agent integration.
 * All calls go through the PRM backend proxy at /api/v1/prm/admin/zoice
 */

import apiClient, { apiCall } from "./client";
import {
  ZoicePipeline,
  ZoiceAgent,
  ZoiceCall,
  ZoicePhoneNumber,
  ZoiceAnalytics,
} from "../store/admin-store";

// =============================================================================
// BASE PATH
// =============================================================================

const ZOICE_BASE = "/api/v1/prm/admin/zoice";

// =============================================================================
// RESPONSE TYPES
// =============================================================================

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface ZoicePipelineResponse {
  id: string;
  name: string;
  description?: string;
  pipeline_type: "realtime" | "turn_based";
  status: "active" | "inactive" | "draft";
  agent_id?: string;
  phone_numbers?: string[];
  created_at: string;
  updated_at: string;
  // Additional fields from Zoice
  agent?: ZoiceAgentResponse;
  extraction_prompt_id?: string;
  webhook_config?: Record<string, unknown>;
}

export interface ZoiceAgentResponse {
  id: string;
  name: string;
  description?: string;
  system_prompt?: string;
  language?: string;
  voice_id?: string;
  llm_config_id?: string;
  stt_config_id?: string;
  tts_config_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ZoiceCallResponse {
  id: string;
  pipeline_id?: string;
  call_type: "inbound" | "outbound";
  status: "queued" | "in_progress" | "completed" | "failed";
  from_number: string;
  to_number: string;
  duration_seconds?: number;
  transcript?: string;
  recording_url?: string;
  created_at: string;
  ended_at?: string;
  extracted_data?: Record<string, unknown>;
}

export interface ZoicePhoneNumberResponse {
  id: string;
  phone_number: string;
  provider: string;
  status: "active" | "inactive";
  pipeline_id?: string;
  created_at: string;
}

export interface ZoiceTelephonyConfigResponse {
  id: string;
  name: string;
  provider: string;
  phone_numbers: ZoicePhoneNumberResponse[];
}

export interface ZoiceProviderConfigResponse {
  id: string;
  name: string;
  service_type: "stt" | "tts" | "llm" | "vad" | "realtime_audio";
  provider: string;
  config: Record<string, unknown>;
  is_default: boolean;
}

export interface ZoiceAgentTemplateResponse {
  id: string;
  name: string;
  description?: string;
  industry?: string;
  use_case?: string;
  preview_image_url?: string;
}

export interface ZoiceIndustryResponse {
  id: string;
  name: string;
  description?: string;
}

export interface ZoiceUseCaseResponse {
  id: string;
  name: string;
  description?: string;
  industry_id?: string;
}

export interface ZoiceLanguageResponse {
  id: string;
  name: string;
  code: string;
}

export interface ZoiceVoiceResponse {
  id: string;
  name: string;
  provider: string;
  language_id?: string;
  sample_url?: string;
}

// =============================================================================
// PIPELINES API
// =============================================================================

export const zoicePipelinesAPI = {
  /**
   * Get all pipelines
   */
  getAll: async (pipelineType?: "realtime" | "turn_based") => {
    const params = pipelineType ? { pipeline_type: pipelineType } : {};
    return apiCall<{ data: ZoicePipelineResponse[] }>(
      apiClient.get(`${ZOICE_BASE}/pipelines`, { params })
    );
  },

  /**
   * Get a single pipeline by ID
   */
  getById: async (id: string) => {
    return apiCall<ZoicePipelineResponse>(
      apiClient.get(`${ZOICE_BASE}/pipelines/${id}`)
    );
  },

  /**
   * Create a new pipeline
   */
  create: async (
    data: Partial<ZoicePipelineResponse>,
    agentTemplateId?: string
  ) => {
    const params = agentTemplateId ? { agent_template_id: agentTemplateId } : {};
    return apiCall<ZoicePipelineResponse>(
      apiClient.post(`${ZOICE_BASE}/pipelines`, data, { params })
    );
  },

  /**
   * Update a pipeline
   */
  update: async (id: string, data: Partial<ZoicePipelineResponse>) => {
    return apiCall<ZoicePipelineResponse>(
      apiClient.put(`${ZOICE_BASE}/pipelines/${id}`, data)
    );
  },

  /**
   * Delete a pipeline
   */
  delete: async (id: string) => {
    return apiCall<{ success: boolean }>(
      apiClient.delete(`${ZOICE_BASE}/pipelines/${id}`)
    );
  },

  /**
   * Get pipeline analytics
   */
  getAnalytics: async (id: string, period?: "last_7_days" | "last_30_days") => {
    const params = period ? { period } : {};
    return apiCall<ZoiceAnalytics>(
      apiClient.get(`${ZOICE_BASE}/pipelines/${id}/analytics`, { params })
    );
  },

  /**
   * Get phone numbers assigned to a pipeline
   */
  getPhoneNumbers: async (id: string) => {
    return apiCall<ZoicePhoneNumberResponse[]>(
      apiClient.get(`${ZOICE_BASE}/pipelines/${id}/phone-numbers`)
    );
  },

  /**
   * Assign phone numbers to a pipeline
   */
  assignPhoneNumbers: async (id: string, phoneNumberIds: string[]) => {
    return apiCall<{ success: boolean }>(
      apiClient.post(`${ZOICE_BASE}/pipelines/${id}/assign-phone-numbers`, {
        phone_number_ids: phoneNumberIds,
      })
    );
  },
};

// =============================================================================
// AGENTS API
// =============================================================================

export const zoiceAgentsAPI = {
  /**
   * Get all agents
   */
  getAll: async () => {
    return apiCall<{ data: ZoiceAgentResponse[] }>(
      apiClient.get(`${ZOICE_BASE}/agents`)
    );
  },

  /**
   * Get agent templates
   */
  getTemplates: async (page = 1, pageSize = 10) => {
    return apiCall<PaginatedResponse<ZoiceAgentTemplateResponse>>(
      apiClient.get(`${ZOICE_BASE}/agents/templates`, {
        params: { page, page_size: pageSize },
      })
    );
  },

  /**
   * Get a single agent by ID
   */
  getById: async (id: string) => {
    return apiCall<ZoiceAgentResponse>(
      apiClient.get(`${ZOICE_BASE}/agents/${id}`)
    );
  },

  /**
   * Create a new agent
   */
  create: async (data: Partial<ZoiceAgentResponse>) => {
    return apiCall<ZoiceAgentResponse>(
      apiClient.post(`${ZOICE_BASE}/agents`, data)
    );
  },

  /**
   * Update an agent
   */
  update: async (id: string, data: Partial<ZoiceAgentResponse>) => {
    return apiCall<ZoiceAgentResponse>(
      apiClient.put(`${ZOICE_BASE}/agents/${id}`, data)
    );
  },

  /**
   * Delete an agent
   */
  delete: async (id: string) => {
    return apiCall<{ success: boolean }>(
      apiClient.delete(`${ZOICE_BASE}/agents/${id}`)
    );
  },
};

// =============================================================================
// CALLS API
// =============================================================================

export const zoiceCallsAPI = {
  /**
   * Get all calls (paginated)
   */
  getAll: async (page = 1, limit = 10) => {
    return apiCall<PaginatedResponse<ZoiceCallResponse>>(
      apiClient.get(`${ZOICE_BASE}/calls`, { params: { page, limit } })
    );
  },

  /**
   * Get a single call by ID
   */
  getById: async (id: string) => {
    return apiCall<ZoiceCallResponse>(apiClient.get(`${ZOICE_BASE}/calls/${id}`));
  },

  /**
   * Schedule/create a new outbound call
   */
  create: async (data: {
    pipeline_id: string;
    to_number: string;
    scheduled_at?: string;
    context?: Record<string, unknown>;
  }) => {
    return apiCall<ZoiceCallResponse>(apiClient.post(`${ZOICE_BASE}/calls`, data));
  },

  /**
   * Get call statistics
   */
  getAggregate: async (data: {
    start_date: string;
    end_date: string;
    pipeline_id?: string;
    group_by?: "day" | "week" | "month";
  }) => {
    return apiCall<{
      total_calls: number;
      completed_calls: number;
      failed_calls: number;
      average_duration: number;
      by_period: { period: string; count: number }[];
    }>(apiClient.post(`${ZOICE_BASE}/calls/aggregate`, data));
  },
};

// =============================================================================
// PHONE NUMBERS API
// =============================================================================

export const zoicePhoneNumbersAPI = {
  /**
   * Get available phone numbers (not assigned to any pipeline)
   */
  getAvailable: async () => {
    return apiCall<ZoicePhoneNumberResponse[]>(
      apiClient.get(`${ZOICE_BASE}/phone-numbers/available`)
    );
  },
};

// =============================================================================
// TELEPHONY CONFIGS API
// =============================================================================

export const zoiceTelephonyAPI = {
  /**
   * Get all telephony configurations
   */
  getAll: async () => {
    return apiCall<ZoiceTelephonyConfigResponse[]>(
      apiClient.get(`${ZOICE_BASE}/telephony-configs`)
    );
  },
};

// =============================================================================
// PROVIDER CONFIGURATIONS API
// =============================================================================

export const zoiceProviderConfigsAPI = {
  /**
   * Get provider configurations
   */
  getAll: async (serviceType?: "stt" | "tts" | "llm" | "vad" | "realtime_audio") => {
    const params = serviceType ? { service_type: serviceType } : {};
    return apiCall<ZoiceProviderConfigResponse[]>(
      apiClient.get(`${ZOICE_BASE}/provider-configurations`, { params })
    );
  },

  /**
   * Get provider library (default configurations)
   */
  getLibrary: async (
    serviceType?: "stt" | "tts" | "llm" | "vad" | "realtime_audio"
  ) => {
    const params = serviceType ? { service_type: serviceType } : {};
    return apiCall<ZoiceProviderConfigResponse[]>(
      apiClient.get(`${ZOICE_BASE}/provider-configurations/library`, { params })
    );
  },

  /**
   * Create a provider configuration
   */
  create: async (data: Partial<ZoiceProviderConfigResponse>) => {
    return apiCall<ZoiceProviderConfigResponse>(
      apiClient.post(`${ZOICE_BASE}/provider-configurations`, data)
    );
  },
};

// =============================================================================
// WEBHOOKS API
// =============================================================================

export const zoiceWebhooksAPI = {
  /**
   * Get all webhooks
   */
  getAll: async () => {
    return apiCall<
      {
        id: string;
        name: string;
        url: string;
        events: string[];
        is_active: boolean;
      }[]
    >(apiClient.get(`${ZOICE_BASE}/webhooks`));
  },

  /**
   * Create a webhook
   */
  create: async (data: { name: string; url: string; events: string[] }) => {
    return apiCall<{ id: string }>(apiClient.post(`${ZOICE_BASE}/webhooks`, data));
  },

  /**
   * Update a webhook
   */
  update: async (
    id: string,
    data: Partial<{ name: string; url: string; events: string[]; is_active: boolean }>
  ) => {
    return apiCall<{ success: boolean }>(
      apiClient.put(`${ZOICE_BASE}/webhooks/${id}`, data)
    );
  },

  /**
   * Delete a webhook
   */
  delete: async (id: string) => {
    return apiCall<{ success: boolean }>(
      apiClient.delete(`${ZOICE_BASE}/webhooks/${id}`)
    );
  },
};

// =============================================================================
// REFERENCE DATA API
// =============================================================================

export const zoiceReferenceDataAPI = {
  /**
   * Get industries
   */
  getIndustries: async () => {
    return apiCall<ZoiceIndustryResponse[]>(
      apiClient.get(`${ZOICE_BASE}/industries`)
    );
  },

  /**
   * Get use cases
   */
  getUseCases: async (industryId?: string) => {
    const params = industryId ? { industry_id: industryId } : {};
    return apiCall<ZoiceUseCaseResponse[]>(
      apiClient.get(`${ZOICE_BASE}/use-cases`, { params })
    );
  },

  /**
   * Get languages
   */
  getLanguages: async () => {
    return apiCall<ZoiceLanguageResponse[]>(
      apiClient.get(`${ZOICE_BASE}/languages`)
    );
  },

  /**
   * Get voices
   */
  getVoices: async (languageIds?: string) => {
    const params = languageIds ? { language_ids: languageIds } : {};
    return apiCall<ZoiceVoiceResponse[]>(
      apiClient.get(`${ZOICE_BASE}/voices`, { params })
    );
  },

  /**
   * Get LLMs
   */
  getLLMs: async () => {
    return apiCall<{ id: string; name: string; provider: string }[]>(
      apiClient.get(`${ZOICE_BASE}/llms`)
    );
  },

  /**
   * Get STT providers
   */
  getSTTs: async () => {
    return apiCall<{ id: string; name: string; provider: string }[]>(
      apiClient.get(`${ZOICE_BASE}/stts`)
    );
  },
};

// =============================================================================
// HEALTH CHECK API
// =============================================================================

export const zoiceHealthAPI = {
  /**
   * Check Zoice backend health
   */
  check: async () => {
    return apiCall<{
      status: "connected" | "error";
      zoice_status?: number;
      zoice_healthy?: boolean;
      error?: string;
    }>(apiClient.get(`${ZOICE_BASE}/health`));
  },
};

// =============================================================================
// COMBINED API EXPORT
// =============================================================================

export const zoiceAPI = {
  pipelines: zoicePipelinesAPI,
  agents: zoiceAgentsAPI,
  calls: zoiceCallsAPI,
  phoneNumbers: zoicePhoneNumbersAPI,
  telephony: zoiceTelephonyAPI,
  providerConfigs: zoiceProviderConfigsAPI,
  webhooks: zoiceWebhooksAPI,
  referenceData: zoiceReferenceDataAPI,
  health: zoiceHealthAPI,
};

export default zoiceAPI;
