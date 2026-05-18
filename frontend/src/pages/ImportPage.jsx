import React, { useState } from 'react';
import axios from 'axios';
import './ImportPage.css';

const filialList = [
  "Буинское", "Елабужское", "Камское", "Чистопольское",
  "Альметьевское", "Набережночелнинское", "Приволжское",
  "Бугульминское", "Казанское городское"
];

const categories = ["ЮЛ", "ФЛ", "ИКУ"];

const indicatorsByCategory = {
  "ЮЛ": [
    "НУР",
    "Оценка доли ПЗ в V продаж за тек/месяц и снижение ПЗ",
    "Доля задолженности в объеме продаж"
  ],
  "ФЛ": [
    "НУР",
    "Оценка доли ПЗ в V продаж за тек/месяц и снижение ПЗ",
    "Доля задолженности в объеме продаж"
  ],
  "ИКУ": [
    "НУР",
    "Оценка доли ПЗ в V продаж за тек/месяц и снижение ПЗ",
    "Доля задолженности в объеме продаж"
  ]
};

const ImportPage = () => {
  const [filial, setFilial] = useState('');
  const [category, setCategory] = useState('');
  const [indicator, setIndicator] = useState('');
  const [file, setFile] = useState(null);
  const [period, setPeriod] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleFileChange = (e) => setFile(e.target.files[0]);
  const handlePeriodChange = (e) => setPeriod(e.target.value + '-01');

  const handleUpload = async () => {
    if (!filial || !category || !indicator || !file || !period) {
      setError('Заполните все поля и выберите файл');
      return;
    }

    setLoading(true);
    setMessage('');
    setError('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('filial', filial);
    formData.append('category', category);
    formData.append('indicator', indicator);
    formData.append('period', period);

    try {
      const response = await axios.post('/api/import/kpi-structured', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setMessage(`Импортировано записей: ${response.data.rows_imported}`);
      // очистка формы
      setFile(null);
      document.getElementById('fileInput').value = '';
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="import-container">
      <h2>Импорт данных по показателям</h2>
      <div className="import-card">
        <div className="field-group">
          <label>🏢 Филиал:</label>
          <select value={filial} onChange={(e) => setFilial(e.target.value)}>
            <option value="">-- Выберите --</option>
            {filialList.map(f => <option key={f}>{f}</option>)}
          </select>
        </div>
        <div className="field-group">
          <label>👥 Категория:</label>
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">-- Выберите --</option>
            {categories.map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
        <div className="field-group">
          <label>Показатель:</label>
          <select value={indicator} onChange={(e) => setIndicator(e.target.value)} disabled={!category}>
            <option value="">-- Выберите --</option>
            {category && indicatorsByCategory[category].map(i => <option key={i}>{i}</option>)}
          </select>
        </div>
        <div className="field-group">
          <label>Период (месяц):</label>
          <input type="month" onChange={handlePeriodChange} />
        </div>
        <div className="file-input-wrapper">
          <label htmlFor="fileInput" className="file-label">{file ? file.name : 'Выберите файл Excel'}</label>
          <input id="fileInput" type="file" accept=".xlsx,.xls" onChange={handleFileChange} />
        </div>
        <button onClick={handleUpload} disabled={loading || !filial || !category || !indicator || !file || !period}>
          {loading ? 'Загрузка...' : '📤 Загрузить'}
        </button>
        {message && <div className="success-message">{message}</div>}
        {error && <div className="error-message">{error}</div>}
      </div>
      <div className="import-note">
        <h4>Формат Excel-файла:</h4>
        <ul>
          <li>Первый лист, колонка A: <strong>Период</strong> (дата, например 2025-10-01)</li>
          <li>Колонка B: <strong>Значение</strong> (число)</li>
          <li>Если нужно загрузить несколько периодов, просто перечислите строки.</li>
          <li>Пример: <code>2025-01-01 | 85.5</code></li>
        </ul>
        <p><strong>Примечание:</strong> Для каждого показателя загружается отдельный файл.</p>
      </div>
    </div>
  );
};

export default ImportPage;