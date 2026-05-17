import axios from 'axios'

export default function FileUploader() {

  const upload = async (e) => {

    const file = e.target.files[0]

    const form = new FormData()

    form.append('file', file)

    await axios.post(
      'http://localhost:8000/api/import/excel',
      form
    )
  }

  return (
    <input type='file' onChange={upload} />
  )
}