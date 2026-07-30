import apiClient from './client'

export async function getCustomers() {
  const response = await apiClient.get('/users/')
  return response.data
}