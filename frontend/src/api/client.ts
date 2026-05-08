import axios from 'axios'

const baseURL = 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL,
})

export const uploadClient = axios.create({
  baseURL,
})