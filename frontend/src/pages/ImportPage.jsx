import { useState } from 'react'
import axios from 'axios'

export default function ImportPage() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [ratings, setRatings] = useState([])
  const [error, setError] = useState('')

  const handleFileChange = (e) => {
    const selected = e.target.files[0]

    if (!selected) return

    const allowed = ['.xlsx', '.csv', '.xml']

    const ext = selected.name
      .substring(selected.name.lastIndexOf('.'))
      .toLowerCase()

    if (!allowed.includes(ext)) {
      setError('Поддерживаются только XLSX, CSV и XML')
      return
    }

    setError('')
    setFile(selected)
  }

  const uploadFile = async () => {
    if (!file) {
      setError('Выберите файл')
      return
    }

    try {
      setLoading(true)
      setError('')
      setMessage('')

      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(
        'http://localhost:8000/api/import/excel',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )

      setMessage('Файл успешно импортирован')

      if (response.data.ratings) {
        setRatings(response.data.ratings)
      }
    } catch (err) {
      console.error(err)

      setError(
        err.response?.data?.detail ||
          'Ошибка загрузки файла'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='min-h-screen bg-gray-100 p-8'>
      <div className='max-w-6xl mx-auto'>
        <div className='bg-white rounded-2xl shadow-lg p-8'>
          <h1 className='text-3xl font-bold mb-6'>
            Импорт KPI рейтинга филиалов
          </h1>

          <div className='border-2 border-dashed border-gray-300 rounded-xl p-8 mb-6'>
            <div className='flex flex-col gap-4'>
              <input
                type='file'
                accept='.xlsx,.csv,.xml'
                onChange={handleFileChange}
                className='block w-full text-sm text-gray-700
                file:mr-4
                file:py-2
                file:px-4
                file:rounded-lg
                file:border-0
                file:text-sm
                file:font-semibold
                file:bg-blue-50
                file:text-blue-700
                hover:file:bg-blue-100'
              />

              {file && (
                <div className='bg-gray-50 p-4 rounded-lg'>
                  <p className='text-sm'>
                    <span className='font-semibold'>Файл:</span>{' '}
                    {file.name}
                  </p>

                  <p className='text-sm'>
                    <span className='font-semibold'>Размер:</span>{' '}
                    {(file.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              )}

              <button
                onClick={uploadFile}
                disabled={loading}
                className='bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold transition-all disabled:opacity-50'
              >
                {loading
                  ? 'Импорт и расчет...'
                  : 'Загрузить и рассчитать рейтинг'}
              </button>
            </div>
          </div>

          {message && (
            <div className='bg-green-100 border border-green-300 text-green-800 p-4 rounded-xl mb-6'>
              {message}
            </div>
          )}

          {error && (
            <div className='bg-red-100 border border-red-300 text-red-800 p-4 rounded-xl mb-6'>
              {error}
            </div>
          )}

          {ratings.length > 0 && (
            <div className='overflow-x-auto'>
              <h2 className='text-2xl font-bold mb-4'>
                Рейтинг филиалов
              </h2>

              <table className='min-w-full bg-white border border-gray-200 rounded-xl overflow-hidden'>
                <thead className='bg-gray-100'>
                  <tr>
                    <th className='px-4 py-3 text-left'>Место</th>
                    <th className='px-4 py-3 text-left'>Филиал</th>
                    <th className='px-4 py-3 text-left'>Баллы</th>
                    <th className='px-4 py-3 text-left'>Период</th>
                  </tr>
                </thead>

                <tbody>
                  {ratings.map((item, index) => (
                    <tr
                      key={index}
                      className='border-t border-gray-200 hover:bg-gray-50'
                    >
                      <td className='px-4 py-3 font-semibold'>
                        {item.rank}
                      </td>

                      <td className='px-4 py-3'>
                        {item.filial_name}
                      </td>

                      <td className='px-4 py-3'>
                        {Number(item.score).toFixed(2)}
                      </td>

                      <td className='px-4 py-3'>
                        {item.period}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
