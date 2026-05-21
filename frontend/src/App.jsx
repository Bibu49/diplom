import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import axios from 'axios';
import RatingTable from './components/RatingTable';
import ChartComponent from './components/ChartComponent';
import ImportPage from './pages/ImportPage';
import Header from './components/Header';
import Footer from './components/Footer';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import './App.css';


const COMPANY = {
  name: "АО «Татэнергосбыт»",
  website: "https://tatenergosbyt.ru",
  email: "info@tatenergosbyt.ru",
  phone: "8 (800) 200-25-26",
  logoUrl: "/logo.jpg"
};


const HomePage = () => {
  const [periodType, setPeriodType] = useState('year');
  const [selectedMonth, setSelectedMonth] = useState('2025-01-01');
  const [selectedYear, setSelectedYear] = useState('2025');
  const [ratingData, setRatingData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sortBy, setSortBy] = useState('');
  const { user } = useAuth();  

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
      // Если пользователь не админ, фильтруем данные по его филиалу
      let data = response.data;
      if (!user?.is_admin && user?.filial_id) {
        data = data.filter(item => item.filial_id === user.filial_id);
      }
      setRatingData(data);
    } catch (err) {
      console.error(err);
      setError('Ошибка загрузки рейтинга');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRating();
  }, [periodType, selectedMonth, selectedYear, user]);

  const handleCalculate = async () => {
    setLoading(true);
    setError('');
    try {
      let periodToSend;
      if (periodType === 'month') {
        periodToSend = selectedMonth;
      } else {
        periodToSend = `${selectedYear}-01-01`;
      }
      await axios.post(`/api/calculate-from-primary?period=${periodToSend}`);
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

const PrivateRoute = ({ children }) => {
  const { user } = useAuth();
  const location = useLocation();
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} />;
  }
  return children;
};

function AppContent() {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <div className="loader">Загрузка...</div>;
  console.log(location.pathname);

  return (
    <div className="app-wrapper">
      <Header 
        logoUrl={COMPANY.logoUrl}
        companyWebsite={COMPANY.website}
        companyName={COMPANY.name}
      />
      <main className="container">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={
            <PrivateRoute>
              <HomePage />
            </PrivateRoute>
          } />
          <Route path="/import" element={
            <PrivateRoute>
              <ImportPage />
            </PrivateRoute>
          } />
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
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  </Router>
);