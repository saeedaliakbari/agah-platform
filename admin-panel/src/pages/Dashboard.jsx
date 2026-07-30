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
      <p className="text-gray-600">به پنل ادمین آگاه پلتفرم خوش آمدید.</p>
    </div>
  )
}

export default Dashboard