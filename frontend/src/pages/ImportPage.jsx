import React, { useState } from 'react';
import axios from 'axios';
import './ImportPage.css';

const ImportPage = () => {
  // --- Состояния для импорта готового рейтинга ---
  const [ratingFile, setRatingFile] = useState(null);
  const [ratingPeriod, setRatingPeriod] = useState('');
  const [ratingMessage, setRatingMessage] = useState('');
  const [ratingError, setRatingError] = useState('');

  // --- Состояния для импорта первичных данных ---
  const [primaryFile, setPrimaryFile] = useState(null);
  const [primaryMessage, setPrimaryMessage] = useState('');
  const [primaryError, setPrimaryError] = useState('');

  // --- Импорт готового рейтинга ---
  const handleRatingUpload = async () => {
    if (!ratingFile || !ratingPeriod) {
      setRatingError('Выберите файл и укажите период');
      return;
    }
    setRatingMessage('');
    setRatingError('');
    const formData = new FormData();
    formData.append('file', ratingFile);
    formData.append('period', ratingPeriod);
    try {
      const res = await axios.post('/api/import/rating', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setRatingMessage(`Импортировано: ${res.data.imported} записей за период ${res.data.period}`);
      setRatingFile(null);
      setRatingPeriod('');
      document.getElementById('ratingFileInput').value = '';
    } catch (err) {
      setRatingError(err.response?.data?.detail || 'Ошибка импорта');
    }
  };

  // --- Импорт первичных данных ---
  const handlePrimaryUpload = async () => {
    if (!primaryFile) {
      setPrimaryError('Выберите файл');
      return;
    }
    setPrimaryMessage('');
    setPrimaryError('');
    const formData = new FormData();
    formData.append('file', primaryFile);
    try {
      const res = await axios.post('/api/primary/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setPrimaryMessage(`Импортировано: добавлено ${res.data.stats.added}, обновлено ${res.data.stats.updated}`);
      setPrimaryFile(null);
      document.getElementById('primaryFileInput').value = '';
    } catch (err) {
      setPrimaryError(err.response?.data?.detail || 'Ошибка импорта');
    }
  };

  return (
    <div className="import-container">
      <h2>Импорт данных</h2>
      
      <div className="import-card">
        <h3>Импорт готового рейтинга</h3>
        <p>Поддерживаются форматы: Excel (.xlsx, .xls), CSV (.csv), XML (.xml).</p>
        <div className="field-group">
          <label>Период (месяц):</label>
          <input type="month" value={ratingPeriod.slice(0,7)} onChange={(e) => setRatingPeriod(e.target.value + '-01')} />
        </div>
        <div className="file-input-wrapper">
          <label htmlFor="ratingFileInput" className="file-label">
            {ratingFile ? ratingFile.name : 'Выберите файл'}
          </label>
          <input
            id="ratingFileInput"
            type="file"
            accept=".xlsx,.xls,.csv,.xml"
            onChange={(e) => setRatingFile(e.target.files[0])}
            className="file-input-hidden"
          />
        </div>
        <button onClick={handleRatingUpload}>Загрузить рейтинг</button>
        {ratingMessage && <div className="success-message">{ratingMessage}</div>}
        {ratingError && <div className="error-message">{ratingError}</div>}
      </div>

      <div className="import-card">
        <h3>Импорт первичных данных</h3>
        <p>Поддерживаются форматы: Excel (.xlsx, .xls), CSV (.csv), XML (.xml).</p>
        <div className="file-input-wrapper">
          <label htmlFor="primaryFileInput" className="file-label">
            {primaryFile ? primaryFile.name : 'Выберите файл'}
          </label>
          <input
            id="primaryFileInput"
            type="file"
            accept=".xlsx,.xls,.csv,.xml"
            onChange={(e) => setPrimaryFile(e.target.files[0])}
            className="file-input-hidden"
          />
        </div>
        <button onClick={handlePrimaryUpload}>Загрузить первичные данные</button>
        {primaryMessage && <div className="success-message">{primaryMessage}</div>}
        {primaryError && <div className="error-message">{primaryError}</div>}
      </div>

      <div className="import-note">
        <h4>Примечание:</h4>
        <ul>
          <li>После загрузки первичных данных необходимо <strong>пересчитать рейтинг</strong> на странице рейтинга.</li>
        </ul>
      </div>
    </div>
  );
};

export default ImportPage;