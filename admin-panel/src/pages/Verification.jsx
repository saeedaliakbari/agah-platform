import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getPendingVerifications,
  getRejectionReasons,
  approveVerification,
  rejectVerification,
} from '../api/verification'

function Verification() {
  const queryClient = useQueryClient()
  const [selectedReason, setSelectedReason] = useState({})

  const { data: requests, isLoading } = useQuery({
    queryKey: ['pending-verifications'],
    queryFn: getPendingVerifications,
  })

  const { data: reasons } = useQuery({
    queryKey: ['rejection-reasons'],
    queryFn: getRejectionReasons,
  })

  const approveMutation = useMutation({
    mutationFn: approveVerification,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-verifications'] })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: ({ requestId, reasonId }) => rejectVerification(requestId, reasonId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-verifications'] })
    },
  })

  if (isLoading) {
    return <p className="p-8 text-gray-600">در حال بارگذاری...</p>
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        درخواست‌های احراز هویت در انتظار بررسی
      </h1>

      {requests?.length === 0 && (
        <p className="text-gray-500">هیچ درخواست در انتظاری وجود ندارد.</p>
      )}

      <div className="space-y-4">
        {requests?.map((req) => (
          <div key={req.id} className="bg-white rounded-lg shadow p-5">
            <div className="flex justify-between items-start mb-3">
              <div>
                <p className="font-semibold text-gray-800">درخواست #{req.id}</p>
                <p className="text-sm text-gray-500">
                  کاربر: {req.user_id} | تاریخ:{' '}
                  {new Date(req.created_at).toLocaleDateString('fa-IR')}
                </p>
              </div>
              <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                در انتظار بررسی
              </span>
            </div>

            <p className="text-sm text-gray-500 mb-4">
              برای مشاهده‌ی تصویر مدرک، به کانال احراز هویت در بله مراجعه کنید.
            </p>

            <div className="flex items-center gap-3">
              <button
                onClick={() => approveMutation.mutate(req.id)}
                disabled={approveMutation.isPending}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
              >
                تایید
              </button>

              <select
                value={selectedReason[req.id] || ''}
                onChange={(e) =>
                  setSelectedReason({ ...selectedReason, [req.id]: e.target.value })
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
                    requestId: req.id,
                    reasonId: selectedReason[req.id],
                  })
                }
                disabled={!selectedReason[req.id] || rejectMutation.isPending}
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

export default Verification