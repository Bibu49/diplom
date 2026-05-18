import React, { useState } from 'react';
import axios from 'axios';
import './ImportPage.css';

const ImportPage = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setMessage('');
    setError('');
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Пожалуйста, выберите файл');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    setMessage('');
    setError('');

    try {
      const response = await axios.post('/api/import/excel', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setMessage(`Успешно! Загружено строк: ${response.data.rows || '?'}`);
      setFile(null);
      // очистить input file
      document.getElementById('fileInput').value = '';
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Ошибка при загрузке файла');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="import-container">
      <h2>Импорт данных из Excel</h2>
      <p className="import-description">
        Загрузите файл с фактическими значениями KPI филиалов. 
        Поддерживаются форматы <strong>.xlsx, .xls</strong>.
      </p>
      <div className="import-card">
        <div className="file-input-wrapper">
          <label htmlFor="fileInput" className="file-label">
            {file ? file.name : 'Выберите файл'}
          </label>
          <input
            id="fileInput"
            type="file"
            accept=".xlsx, .xls"
            onChange={handleFileChange}
            className="file-input"
          />
        </div>
        <button 
          onClick={handleUpload} 
          disabled={!file || loading}
          className="upload-button"
        >
          {loading ? 'Загрузка...' : 'Загрузить и рассчитать рейтинг'}
        </button>
        {message && <div className="success-message">{message}</div>}
        {error && <div className="error-message">{error}</div>}
      </div>
      <div className="import-note">
        <h4>Требования к файлу:</h4>
        <ul>
          <li>Первый лист (Sheet1) содержит данные</li>
          <li>Колонки: Филиал, Период, KPI, Значение</li>
          <li>Пример: <code>Филиал Москва, 2025-01-01, Выручка, 120</code></li>
        </ul>
      </div>
    </div>
  );
};

export default ImportPage;