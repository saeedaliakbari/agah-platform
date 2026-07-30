import { useQuery } from '@tanstack/react-query'
import { getCustomers } from '../api/users'

const verificationLabels = {
  unverified: { text: 'احراز نشده', className: 'bg-gray-100 text-gray-700' },
  pending: { text: 'در انتظار بررسی', className: 'bg-yellow-100 text-yellow-800' },
  approved: { text: 'تایید شده', className: 'bg-green-100 text-green-800' },
  rejected: { text: 'رد شده', className: 'bg-red-100 text-red-800' },
}

function Users() {
  const { data: users, isLoading } = useQuery({
    queryKey: ['customers'],
    queryFn: getCustomers,
  })

  if (isLoading) {
    return <p className="p-8 text-gray-600">در حال بارگذاری...</p>
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        لیست کاربران ({users?.length || 0})
      </h1>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-right">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-sm font-semibold text-gray-600">نام</th>
              <th className="px-4 py-3 text-sm font-semibold text-gray-600">یوزرنیم</th>
              <th className="px-4 py-3 text-sm font-semibold text-gray-600">آیدی بله</th>
              <th className="px-4 py-3 text-sm font-semibold text-gray-600">شماره موبایل</th>
              <th className="px-4 py-3 text-sm font-semibold text-gray-600">وضعیت احراز</th>
              <th className="px-4 py-3 text-sm font-semibold text-gray-600">تاریخ عضویت</th>
            </tr>
          </thead>
          <tbody>
            {users?.map((user) => {
              const verification =
                verificationLabels[user.verification_status] || verificationLabels.unverified
              return (
                <tr key={user.id} className="border-b border-gray-100 last:border-0">
                  <td className="px-4 py-3 text-gray-800">{user.full_name || '—'}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {user.bale_username ? `@${user.bale_username}` : '—'}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{user.bale_user_id}</td>
                  <td className="px-4 py-3 text-gray-600">{user.phone_number || '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-1 rounded ${verification.className}`}>
                      {verification.text}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-sm">
                    {new Date(user.created_at).toLocaleDateString('fa-IR')}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default Users