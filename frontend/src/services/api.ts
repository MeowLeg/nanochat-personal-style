import axios from 'axios'
import type { WritingSample, StyleProfile, RewriteRequest, RewriteResponse, TrainingJob, MLXModel, AuthorProfile } from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000
})

export const authorsApi = {
  createAuthor: (data: { name: string; description?: string }) =>
    api.post<AuthorProfile>('/authors', data),

  listAuthors: () => api.get<AuthorProfile[]>('/authors'),

  getAuthor: (id: string) => api.get<AuthorProfile>(`/authors/${id}`),

  deleteAuthor: (id: string) => api.delete(`/authors/${id}`),

  getAuthorSamples: (authorId: string) => api.get<any[]>(`/authors/${authorId}/samples`)
}

export const samplesApi = {
  importSamples: (files: File[], authorName: string, source?: string, language: string = 'zh', authorId?: string) => {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    formData.append('author_name', authorName)
    if (source) formData.append('source', source)
    formData.append('language', language)
    if (authorId) formData.append('author_id', authorId)
    return api.post<WritingSample[]>('/samples/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  listSamples: () => api.get<WritingSample[]>('/samples'),

  getSample: (id: string) => api.get<WritingSample>(`/samples/${id}`)
}

export const stylesApi = {
  createProfile: (data: { name: string; description?: string; sample_ids: string[]; author_id?: string }) =>
    api.post<StyleProfile>('/style_profiles', data),

  listProfiles: () => api.get<StyleProfile[]>('/style_profiles'),

  getProfile: (id: string) => api.get<StyleProfile>(`/style_profiles/${id}`),

  deleteProfile: (id: string) => api.delete(`/style_profiles/${id}`)
}

export const rewriteApi = {
  rewrite: (data: RewriteRequest) => api.post<RewriteResponse>('/rewrite', data)
}

export const trainingApi = {
  listModels: () => api.get<{ models: MLXModel[] }>('/training/models'),
  
  listNanochatModels: () => api.get<{ models: any[] }>('/training/models/zh'),

  createJob: (styleProfile: StyleProfile, modelName?: string) =>
    api.post<{ job_id: string; style_id: string; style_name: string; model_name: string; status: string; created_at: string }>(
      '/training/jobs',
      { style_profile: styleProfile, model_name: modelName }
    ),

  listJobs: () => api.get<TrainingJob[]>('/training/jobs'),

  getJob: (jobId: string) => api.get<TrainingJob>(`/training/jobs/${jobId}`),

  deleteJob: (jobId: string) => api.delete(`/training/jobs/${jobId}`)
}

export const healthApi = {
  check: () => api.get('/health')
}