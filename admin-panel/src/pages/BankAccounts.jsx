import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getPendingBankAccounts,
  approveBankAccount,
  rejectBankAccount,
} from '../api/bankAccounts'
import { getRejectionReasons } from '../api/verification'

function BankAccounts() {
  const queryClient = useQueryClient()
  const [selectedReason, setSelectedReason] = useState({})

  const { data: accounts, isLoading } = useQuery({
    queryKey: ['pending-bank-accounts'],
    queryFn: getPendingBankAccounts,
  })

  const { data: reasons } = useQuery({
    queryKey: ['rejection-reasons'],
    queryFn: getRejectionReasons,
  })

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['pending-bank-accounts'] })

  const approveMutation = useMutation({
    mutationFn: approveBankAccount,
    onSuccess: invalidate,
  })

  const rejectMutation = useMutation({
    mutationFn: ({ accountId, reasonId }) => rejectBankAccount(accountId, reasonId),
    onSuccess: invalidate,
  })

  if (isLoading) {
    return <p className="p-8 text-gray-600">در حال بارگذاری...</p>
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        حساب‌های بانکی در انتظار تایید
      </h1>

      {accounts?.length === 0 && (
        <p className="text-gray-500">هیچ حساب بانکی در انتظاری وجود ندارد.</p>
      )}

      <div className="space-y-4">
        {accounts?.map((acc) => (
          <div key={acc.id} className="bg-white rounded-lg shadow p-5">
            <div className="mb-3">
              <p className="font-semibold text-gray-800">
                {acc.bank_name} - {acc.account_holder_name}
              </p>
              <p className="text-sm text-gray-500">شبا: {acc.sheba_number}</p>
              <p className="text-sm text-gray-500">
                کارت: {acc.card_number || 'ثبت نشده'}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => approveMutation.mutate(acc.id)}
                disabled={approveMutation.isPending}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
              >
                تایید
              </button>

              <select
                value={selectedReason[acc.id] || ''}
                onChange={(e) =>
                  setSelectedReason({ ...selectedReason, [acc.id]: e.target.value })
                }
                className="border border-gray-300 rounded px-3 py-2"
              >
                <option value="">انتخاب دلیل رد...</option>
                {reasons?.map((reason) => (
                  <option key={reason.id} value={reason.id}>
                    {reason.text}
                  </option>
                ))}
              </select>

              <button
                onClick={() =>
                  rejectMutation.mutate({
                    accountId: acc.id,
                    reasonId: selectedReason[acc.id],
                  })
                }
                disabled={!selectedReason[acc.id] || rejectMutation.isPending}
                className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 disabled:opacity-50"
              >
                رد
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default BankAccounts