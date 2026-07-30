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