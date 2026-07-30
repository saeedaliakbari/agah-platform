import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function Dashboard() {
  const { logoutUser } = useAuth()

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Link to="/verification" className="bg-white p-6 rounded-lg shadow hover:shadow-md transition">
          <h2 className="font-semibold text-lg text-gray-800">احراز هویت</h2>
          <p className="text-sm text-gray-500 mt-1">بررسی درخواست‌های در انتظار</p>
        </Link>

        <Link to="/wallet-deposits" className="bg-white p-6 rounded-lg shadow hover:shadow-md transition">
          <h2 className="font-semibold text-lg text-gray-800">واریزهای کیف پول</h2>
          <p className="text-sm text-gray-500 mt-1">بررسی واریزهای در انتظار</p>
        </Link>

        <Link to="/bank-accounts" className="bg-white p-6 rounded-lg shadow hover:shadow-md transition">
          <h2 className="font-semibold text-lg text-gray-800">حساب‌های بانکی</h2>
          <p className="text-sm text-gray-500 mt-1">تایید حساب‌های در انتظار</p>
        </Link>

        <Link to="/rejection-reasons" className="bg-white p-6 rounded-lg shadow hover:shadow-md transition">
          <h2 className="font-semibold text-lg text-gray-800">دلایل رد</h2>
          <p className="text-sm text-gray-500 mt-1">مدیریت دلایل رد درخواست‌ها</p>
        </Link>

        <Link to="/users" className="bg-white p-6 rounded-lg shadow hover:shadow-md transition">
          <h2 className="font-semibold text-lg text-gray-800">کاربران</h2>
          <p className="text-sm text-gray-500 mt-1">لیست تمام کاربران</p>
        </Link>
      </div>
  )
}

export default Dashboard