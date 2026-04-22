export interface WritingSample {
  id: string
  user_id: string
  author_name: string
  author_id?: string
  source?: string
  language: string
  text: string
  length_chars: number
  date_collected: string
  created_at: string
}

export interface AuthorProfile {
  id: string
  user_id: string
  name: string
  description?: string
  sample_count: number
  style_count: number
  created_at: string
  updated_at: string
}

export interface StyleProfile {
  id: string
  user_id: string
  author_id?: string
  name: string
  description?: string
  sample_ids: string[]
  features: Record<string, any>
  created_at: string
  updated_at: string
}

export interface RewriteRequest {
  style_id: string
  source_text: string
  style_strength: number
  max_length: number
}

export interface RewriteResponse {
  rewritten_text: string
  retrieved_sample_ids: string[]
  generation_metadata: Record<string, any>
}

export type TrainingStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface MLXModel {
  name: string
  path: string
  type: string
}

export interface TrainingJob {
  job_id: string
  style_id: string
  style_name: string
  model_name: string
  status: TrainingStatus
  progress: number
  adapter_path?: string
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
}