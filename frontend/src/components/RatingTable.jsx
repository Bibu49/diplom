import React from 'react';

const RatingTable = ({ data }) => {
  return (
    <div className="table-wrapper">
      <table className="rating-table">
        <thead>
          <tr>
            <th>🏆 Место</th>
            <th>🏢 Филиал</th>
            <th>⭐ Интегральный балл</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={item.filial_id}>
              <td>{item.rank}</td>
              <td>{item.filial_name}</td>
              <td>{item.score.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default RatingTable;