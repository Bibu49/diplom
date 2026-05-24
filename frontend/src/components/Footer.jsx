import React from 'react';
import './Footer.css';

const Footer = ({ companyName, year, contactEmail, companyPhone }) => {
  return (
    <footer className="app-footer">
      <div className="footer-content">
        <div className="footer-info">
          <p>© {year} {companyName} — Все права защищены</p>
          <p><a href={`mailto:${contactEmail}`}>{contactEmail}</a> |  {companyPhone}</p>
        </div>
        <div className="footer-credits">
          Разработано в рамках выпускной квалификационной работы: «Разработка информационного сервиса для расчёта и составления рейтингов компании АО«Татэнергосбыт»
        </div>
      </div>
    </footer>
  );
};

export default Footer;