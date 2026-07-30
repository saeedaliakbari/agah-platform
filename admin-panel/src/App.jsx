import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Verification from './pages/Verification'
import WalletDeposits from './pages/WalletDeposits'
import RejectionReasons from './pages/RejectionReasons'
import BankAccounts from './pages/BankAccounts'
import Users from './pages/Users'

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/verification" element={<ProtectedRoute><Verification /></ProtectedRoute>} />
      <Route path="/wallet-deposits" element={<ProtectedRoute><WalletDeposits /></ProtectedRoute>} />
      <Route path="/rejection-reasons" element={<ProtectedRoute><RejectionReasons /></ProtectedRoute>} />
      <Route path="/bank-accounts" element={<ProtectedRoute><BankAccounts /></ProtectedRoute>} />
      <Route path="/users" element={<ProtectedRoute><Users /></ProtectedRoute>} />
    </Routes>
  )
}

export default App