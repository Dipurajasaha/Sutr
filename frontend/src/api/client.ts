import axios from 'axios'

export const apiBaseURL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: apiBaseURL,
})

export const uploadClient = axios.create({
  baseURL: apiBaseURL,
})

export const buildUploadUrl = (filePath: string) => `${apiBaseURL}/uploads/${encodeURIComponent(filePath)}`