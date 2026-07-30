import apiClient from './client'

export async function getPendingVerifications() {
  const response = await apiClient.get('/verification/pending')
  return response.data
}

export async function getRejectionReasons() {
  const response = await apiClient.get('/verification/rejection-reasons')
  return response.data
}

export async function approveVerification(requestId) {
  const response = await apiClient.post(`/verification/${requestId}/approve`)
  return response.data
}

export async function rejectVerification(requestId, rejectionReasonId) {
  const response = await apiClient.post(`/verification/${requestId}/reject`, null, {
    params: { rejection_reason_id: rejectionReasonId },
  })
  return response.data
}

export async function createRejectionReason(text) {
  const response = await apiClient.post('/verification/rejection-reasons', { text })
  return response.data
}

export async function updateRejectionReason(reasonId, text) {
  const response = await apiClient.put(`/verification/rejection-reasons/${reasonId}`, { text })
  return response.data
}

export async function deleteRejectionReason(reasonId) {
  const response = await apiClient.delete(`/verification/rejection-reasons/${reasonId}`)
  return response.data
}