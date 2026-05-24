import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c43', '#d84c4c', '#4c72d8'];

const ChartComponent = ({ data, viewMode = 'total' }) => {
  const chartData = data.map(item => ({
    name: item.filial_name,
    value: viewMode === 'total' ? item.score :
            viewMode === 'kpi1' ? item.kpi1 :
            viewMode === 'kpi2' ? item.kpi2 : item.kpi3,
    full: item
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload.full;
      return (
        <div className="chart-tooltip">
          <p><strong>{item.filial_name}</strong></p>
          <p>НУР: {item.kpi1?.toFixed(2)}</p>
          <p>Оценка доли ПЗ: {item.kpi2?.toFixed(2)}</p>
          <p>Доля задолженности: {item.kpi3?.toFixed(2)}</p>
          <p>Интегральный: {item.score?.toFixed(2)}</p>
        </div>
      );
    }
    return null;
  };

  const getTitle = () => {
    switch(viewMode) {
      case 'total': return 'Интегральный балл';
      case 'kpi1': return 'НУР';
      case 'kpi2': return 'Оценка доли ПЗ';
      case 'kpi3': return 'Доля задолженности';
      default: return 'Значение';
    }
  };

  return (
    <div className="chart-container">
      <h3>Сравнение филиалов по {getTitle()}</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" angle={-15} textAnchor="end" height={80} interval={0} />
          <YAxis domain={[0, 100]} />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Bar dataKey="value" fill="#f97316" name={getTitle()}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ChartComponent;