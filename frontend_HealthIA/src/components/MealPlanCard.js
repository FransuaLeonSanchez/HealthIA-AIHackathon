import React from 'react';
import { useNavigate } from 'react-router-dom';
import './../styles/MealPlanCard.css'; // Asegúrate de crear este archivo CSS

const MealPlanCard = ({ day, meals }) => {
  const navigate = useNavigate();

  const handleMealClick = (mealName) => {
    if (mealName) {
      navigate(`/nutrition/${mealName}`);
    }
  };

  // Mapeo de tipos de comida en español a inglés para buscar en meals
  const mealTypeMapping = {
    'Desayuno': 'breakfast',
    'Almuerzo': 'lunch',
    'Merienda': 'snack', // Asumiendo que Merienda se mapea a Snack
    'Cena': 'dinner'
  };

  return (
    <div className="meal-plan-card">
      <h3 className="meal-plan-day">Menú para {day}</h3>
      <div className="meal-plan-grid">
        {Object.entries(meals).map(([type, meal]) => {
          const mealKey = mealTypeMapping[type]; // Obtener la clave en inglés si es necesario
          if (!meal) return null; // Si no hay comida para este tipo, no renderizar nada

          return (
            <div
              key={meal.name}
              className="meal-plan-item"
              onClick={() => handleMealClick(meal.name)}
            >
              <img
                src={meal.image || 'https://via.placeholder.com/100'} // Placeholder si no hay imagen
                alt={meal.name}
                className="meal-plan-image"
              />
              <div className="meal-plan-info">
                <p className="meal-plan-type">{type}</p>
                <p className="meal-plan-name">{meal.name}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default MealPlanCard; 