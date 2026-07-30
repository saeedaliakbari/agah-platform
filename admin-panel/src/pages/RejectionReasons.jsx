import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getRejectionReasons,
  createRejectionReason,
  updateRejectionReason,
  deleteRejectionReason,
} from '../api/verification'

function RejectionReasons() {
  const queryClient = useQueryClient()
  const [newText, setNewText] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editingText, setEditingText] = useState('')

  const { data: reasons, isLoading } = useQuery({
    queryKey: ['rejection-reasons'],
    queryFn: getRejectionReasons,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['rejection-reasons'] })

  const createMutation = useMutation({
    mutationFn: createRejectionReason,
    onSuccess: () => {
      setNewText('')
      invalidate()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, text }) => updateRejectionReason(id, text),
    onSuccess: () => {
      setEditingId(null)
      invalidate()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteRejectionReason,
    onSuccess: invalidate,
  })

  function handleCreate(e) {
    e.preventDefault()
    if (newText.trim()) {
      createMutation.mutate(newText.trim())
    }
  }

  function startEditing(reason) {
    setEditingId(reason.id)
    setEditingText(reason.text)
  }

  function saveEditing(id) {
    if (editingText.trim()) {
      updateMutation.mutate({ id, text: editingText.trim() })
    }
  }

  if (isLoading) {
    return <p className="p-8 text-gray-600">در حال بارگذاری...</p>
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">مدیریت دلایل رد</h1>

      <form onSubmit={handleCreate} className="flex gap-3 mb-6">
        <input
          type="text"
          value={newText}
          onChange={(e) => setNewText(e.target.value)}
          placeholder="متن دلیل رد جدید..."
          className="flex-1 border border-gray-300 rounded px-3 py-2"
        />
        <button
          type="submit"
          disabled={createMutation.isPending}
          className="bg-blue-600 text-white px-5 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          افزودن
        </button>
      </form>

      <div className="space-y-3">
        {reasons?.map((reason) => (
          <div
            key={reason.id}
            className="bg-white rounded-lg shadow p-4 flex items-center justify-between gap-3"
          >
            {editingId === reason.id ? (
              <input
                type="text"
                value={editingText}
                onChange={(e) => setEditingText(e.target.value)}
                className="flex-1 border border-gray-300 rounded px-3 py-2"
              />
            ) : (
              <span className="flex-1 text-gray-800">{reason.text}</span>
            )}

            <div className="flex gap-2 shrink-0">
              {editingId === reason.id ? (
                <button
                  onClick={() => saveEditing(reason.id)}
                  className="bg-green-600 text-white px-3 py-1.5 rounded text-sm hover:bg-green-700"
                >
                  ذخیره
                </button>
              ) : (
                <button
                  onClick={() => startEditing(reason)}
                  className="bg-gray-200 text-gray-700 px-3 py-1.5 rounded text-sm hover:bg-gray-300"
                >
                  ویرایش
                </button>
              )}
              <button
                onClick={() => deleteMutation.mutate(reason.id)}
                className="bg-red-100 text-red-700 px-3 py-1.5 rounded text-sm hover:bg-red-200"
              >
                حذف
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default RejectionReasons