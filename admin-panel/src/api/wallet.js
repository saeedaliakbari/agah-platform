import apiClient from './client'

export async function getPendingDeposits() {
  const response = await apiClient.get('/wallet/deposit/pending')
  return response.data
}

export async function approveDeposit(transactionId) {
  const response = await apiClient.post(`/wallet/deposit/${transactionId}/approve`)
  return response.data
}

export async function rejectDeposit(transactionId, rejectionReasonId) {
  const response = await apiClient.post(`/wallet/deposit/${transactionId}/reject`, null, {
    params: { rejection_reason_id: rejectionReasonId },
  })
  return response.data
}