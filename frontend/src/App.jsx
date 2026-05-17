import React, { useState, useEffect } from 'react';
import axios from 'axios';
import RatingTable from './components/RatingTable';
import ChartComponent from './components/ChartComponent';
import Header from './components/Header';
import Footer from './components/Footer';
import './App.css';

// Конфигурация компании (замените на реальные данные)
const COMPANY = {
  name: "АО «Татэнергосбыт»",
  website: "https://tatenergosbyt.ru/",
  email: "info@tatenergosbyt.ru",
  phone: "8 (800) 200-25-26",
  logoUrl: "/logo.jpg"   
};

function App() {
  const [period, setPeriod] = useState('2025-01-01');
  const [ratingData, setRatingData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchRating();
  }, [period]);

  const fetchRating = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.get(`/api/rating?period=${period}`);
      setRatingData(response.data);
    } catch (err) {
      console.error(err);
      setError('Ошибка загрузки рейтинга. Возможно, нет данных за этот период.');
    } finally {
      setLoading(false);
    }
  };

  const handlePeriodChange = (e) => {
    const newPeriod = e.target.value + '-01';
    setPeriod(newPeriod);
  };

  return (
    <div className="app-wrapper">
      <Header 
        logoUrl={COMPANY.logoUrl}
        companyWebsite={COMPANY.website}
        companyName={COMPANY.name}
      />
      <main className="container">
        <h1>📊 Рейтинг филиалов по KPI</h1>
        <div className="controls">
          <label>📅 Период: </label>
          <input
            type="month"
            value={period.slice(0, 7)}
            onChange={handlePeriodChange}
          />
          <button onClick={fetchRating}>Обновить</button>
        </div>
        {loading && <div className="loader">Загрузка...</div>}
        {error && <div className="error">{error}</div>}
        {!loading && ratingData.length > 0 && (
          <>
            <RatingTable data={ratingData} />
            <ChartComponent data={ratingData} />
          </>
        )}
        {!loading && ratingData.length === 0 && !error && (
          <p className="no-data">Нет данных для отображения. Добавьте филиалы, KPI и фактические значения.</p>
        )}
      </main>
      <Footer 
        companyName={COMPANY.name}
        year={new Date().getFullYear()}
        contactEmail={COMPANY.email}
        companyPhone={COMPANY.phone}
      />
    </div>
  );
}

export default App;