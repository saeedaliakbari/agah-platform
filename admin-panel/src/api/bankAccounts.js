import apiClient from './client'

export async function getPendingBankAccounts() {
  const response = await apiClient.get('/bank-accounts/pending')
  return response.data
}

export async function approveBankAccount(accountId) {
  const response = await apiClient.post(`/bank-accounts/${accountId}/approve`)
  return response.data
}

export async function rejectBankAccount(accountId, rejectionReasonId) {
  const response = await apiClient.post(`/bank-accounts/${accountId}/reject`, null, {
    params: { rejection_reason_id: rejectionReasonId },
  })
  return response.data
}