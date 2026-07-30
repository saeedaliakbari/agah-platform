import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getPendingDeposits, approveDeposit, rejectDeposit } from '../api/wallet'
import { getRejectionReasons } from '../api/verification'

function WalletDeposits() {
  const queryClient = useQueryClient()
  const [selectedReason, setSelectedReason] = useState({})

  const { data: deposits, isLoading } = useQuery({
    queryKey: ['pending-deposits'],
    queryFn: getPendingDeposits,
  })

  const { data: reasons } = useQuery({
    queryKey: ['rejection-reasons'],
    queryFn: getRejectionReasons,
  })

  const approveMutation = useMutation({
    mutationFn: approveDeposit,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-deposits'] })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: ({ transactionId, reasonId }) => rejectDeposit(transactionId, reasonId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-deposits'] })
    },
  })

  if (isLoading) {
    return <p className="p-8 text-gray-600">در حال بارگذاری...</p>
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        واریزهای در انتظار بررسی
      </h1>

      {deposits?.length === 0 && (
        <p className="text-gray-500">هیچ واریز در انتظاری وجود ندارد.</p>
      )}

      <div className="space-y-4">
        {deposits?.map((dep) => (
          <div key={dep.id} className="bg-white rounded-lg shadow p-5">
            <div className="flex justify-between items-start mb-3">
              <div>
                <p className="font-semibold text-gray-800">تراکنش #{dep.id}</p>
                <p className="text-sm text-gray-500">
                  کاربر: {dep.user_id} | مبلغ: {Number(dep.amount).toLocaleString('fa-IR')} تومان
                </p>
                <p className="text-sm text-gray-500">
                  روش انتقال: {dep.transfer_method || 'ثبت نشده'} | تاریخ:{' '}
                  {new Date(dep.created_at).toLocaleDateString('fa-IR')}
                </p>
                {dep.withdrawal_request_id && (
                  <p className="text-xs text-blue-600 mt-1">
                    مرتبط با درخواست برداشت #{dep.withdrawal_request_id} (P2P)
                  </p>
                )}
              </div>
              <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                در انتظار بررسی
              </span>
            </div>

            <p className="text-sm text-gray-500 mb-4">
              برای مشاهده‌ی تصویر رسید، به کانال کیف پول در بله مراجعه کنید.
            </p>

            <div className="flex items-center gap-3">
              <button
                onClick={() => approveMutation.mutate(dep.id)}
                disabled={approveMutation.isPending}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
              >
                تایید
              </button>

              <select
                value={selectedReason[dep.id] || ''}
                onChange={(e) =>
                  setSelectedReason({ ...selectedReason, [dep.id]: e.target.value })
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
                    transactionId: dep.id,
                    reasonId: selectedReason[dep.id],
                  })
                }
                disabled={!selectedReason[dep.id] || rejectMutation.isPending}
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

export default WalletDeposits