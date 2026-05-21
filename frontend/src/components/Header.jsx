import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Header.css';

const Header = ({ logoUrl, companyWebsite, companyName }) => {
  const location = useLocation();
  const { user, logout } = useAuth();

  const handleLogoClick = () => {
    window.open(companyWebsite, '_blank');
  };

  return (
    <header className="app-header">
      <div className="logo" onClick={handleLogoClick}>
        <img src={logoUrl} alt="Логотип компании" className="logo-img" />
      </div>
      <nav className="nav-menu">
        <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>
          Рейтинг
        </Link>
        <Link to="/import" className={`nav-link ${location.pathname === '/import' ? 'active' : ''}`}>
          Импорт файлов
        </Link>
      </nav>
      <div className="user-info">
        <span className="username">{user?.username || 'Гость'}</span>
        {user && <button onClick={logout} className="logout-btn">Выйти</button>}
      </div>
      <div className="header-title">Система рейтингов филиалов</div>
    </header>
  );
};

export default Header;