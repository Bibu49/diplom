import React, { useState } from 'react';

const RatingTable = ({ data, viewMode = 'total' }) => {
  const [hoveredId, setHoveredId] = useState(null);

  const getDisplayValue = (item) => {
    switch(viewMode) {
      case 'total': return item.score;
      case 'kpi1': return item.kpi1;
      case 'kpi2': return item.kpi2;
      case 'kpi3': return item.kpi3;
      default: return item.score;
    }
  };

  const getColumnName = () => {
    switch(viewMode) {
      case 'total': return 'Интегральный балл';
      case 'kpi1': return 'Юридические лица (ЮЛ)';
      case 'kpi2': return 'Физические лица (ФЛ)';
      case 'kpi3': return 'Исполнитель коммунальных услуг (ИКУ)';
      default: return 'Значение';
    }
  };

  return (
    <div className="table-wrapper">
      <table className="rating-table">
        <thead>
          <tr>
            <th>Место</th>
            <th>Филиал</th>
            <th>{getColumnName()}</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr
              key={item.filial_id}
              onMouseEnter={() => setHoveredId(item.filial_id)}
              onMouseLeave={() => setHoveredId(null)}
              style={{ position: 'relative' }}
            >
              <td>{item.rank}</td>
              <td>{item.filial_name}</td>
              <td>{getDisplayValue(item)?.toFixed(2)}</td>
              {hoveredId === item.filial_id && (
                <div className="table-tooltip">
                  <div>НУР: {item.kpi1?.toFixed(2)}</div>
                  <div>Оценка доли ПЗ {item.kpi2?.toFixed(2)}</div>
                  <div>Доля задолженности: {item.kpi3?.toFixed(2)}</div>
                </div>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default RatingTable;