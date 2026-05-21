import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import RatingTable from './components/RatingTable';
import ChartComponent from './components/ChartComponent';
import ImportPage from './pages/ImportPage';
import Header from './components/Header';
import Footer from './components/Footer';
import './App.css';

const COMPANY = {
  name: "АО «Татэнергосбыт»",
  website: "https://tatenergosbyt.ru",
  email: "info@tatenergosbyt.ru",
  phone: "8 (800) 200-25-26",
  logoUrl: "/logo.jpg"
};

// Отдельный компонент для главной страницы (рейтинг)
const HomePage = () => {
  const [periodType, setPeriodType] = useState('year');
  const [selectedMonth, setSelectedMonth] = useState('2025-01-01');
  const [selectedYear, setSelectedYear] = useState('2025');
  const [ratingData, setRatingData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchRating = async () => {
    setLoading(true);
    setError('');
    try {
      let url;
      if (periodType === 'month') {
        url = `/api/rating?period=${selectedMonth}`;
      } else {
        url = `/api/rating/year?year=${selectedYear}`;
      }
      const response = await axios.get(url);
      setRatingData(response.data);
    } catch (err) {
      console.error(err);
      setError('Ошибка загрузки рейтинга');
    } finally {
      setLoading(false);
    }
  };

    useEffect(() => {
    fetchRating();
  }, [periodType, selectedMonth, selectedYear]);

  const handleCalculate = async () => {
    setLoading(true);
    setError('');
    try {
      let periodToSend;
      if (periodType === 'month') {
        periodToSend = selectedMonth;
      } else {
        // Для года: ваш API ожидает период в формате ГГГГ-ММ-ДД. 
        // Будем пересчитывать рейтинг за первый месяц этого года.
        periodToSend = `${selectedYear}-01-01`;
      }
      await axios.post(`/api/calculate-from-primary?period=${periodToSend}`);
      // После успешного пересчёта обновляем таблицу
      await fetchRating();
    } catch (err) {
      console.error(err);
      setError('Ошибка пересчёта рейтинга: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };



  return (
    <>
      <h1>Рейтинг филиалов</h1>
      <div className="controls">
        <div className="period-toggle">
          <button 
            className={periodType === 'month' ? 'active' : ''} 
            onClick={() => setPeriodType('month')}
          >По месяцам</button>
          <button 
            className={periodType === 'year' ? 'active' : ''} 
            onClick={() => setPeriodType('year')}
          >По годам</button>
          <button onClick={handleCalculate} style={{marginLeft: '10px'}}>Пересчитать рейтинг</button>
        </div>

        {periodType === 'month' && (
          <>
            <label>Период: </label>
            <input
              type="month"
              value={selectedMonth.slice(0, 7)}
              onChange={(e) => setSelectedMonth(e.target.value + '-01')}
            />
            <button onClick={fetchRating}>Обновить</button>
          </>
        )}

        {periodType === 'year' && (
          <>
            <label>Год: </label>
            <input
              type="number"
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value)}
              min="2020"
              max="2030"
              step="1"
              className="year-input"
            />
            <button onClick={fetchRating}>Обновить</button>
          </>
        )}
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
    </>
  );
};

// Главный компонент с роутингом
function App() {
  const location = useLocation();
  return (
    <div className="app-wrapper">
      <Header 
        logoUrl={COMPANY.logoUrl}
        companyWebsite={COMPANY.website}
        companyName={COMPANY.name}
      />
      <main className="container">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/import" element={<ImportPage />} />
        </Routes>
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

export default () => (
  <Router>
    <App />
  </Router>
);