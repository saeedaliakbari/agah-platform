import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function Dashboard() {
  const { logoutUser } = useAuth()

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">داشبورد ادمین</h1>
        <button
          onClick={logoutUser}
          className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
        >
          خروج
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          to="/verification"
          className="bg-white p-6 rounded-lg shadow hover:shadow-md transition"
        >
          <h2 className="font-semibold text-lg text-gray-800">احراز هویت</h2>
          <p className="text-sm text-gray-500 mt-1">بررسی درخواست‌های در انتظار</p>
        </Link>
      </div>
    </div>
  )
}

export default Dashboard