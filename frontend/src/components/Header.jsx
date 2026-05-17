import React from 'react';
import './Header.css';

const Header = ({ logoUrl, companyWebsite, companyName }) => {
  const handleLogoClick = () => {
    window.open(companyWebsite, '_blank');
  };

  return (
    <header className="app-header">
      <div className="logo" onClick={handleLogoClick}>
        <img src={logoUrl} alt="Логотип компании" className="logo-img" />
      </div>
      <div className="header-title">Система рейтингов филиалов</div>
    </header>
  );
};

export default Header;  