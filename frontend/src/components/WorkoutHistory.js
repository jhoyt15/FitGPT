import React, { useEffect, useState } from 'react';

const WorkoutHistory = ({ user }) => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchHistory = async () => {
            if (!user) return;
            
            setLoading(true);
            try {
                const response = await fetch('http://localhost:5001/user/workout-history', {
                    credentials: 'include'
                });
                const data = await response.json();
                if (data.history) {
                    setHistory(data.history);
                }
            } catch (error) {
                console.error('Failed to fetch workout history:', error);
                setError('Failed to load workout history');
            } finally {
                setLoading(false);
            }
        };

        fetchHistory();
    }, [user]);

    if (!user) return null;
    if (loading) return <div className="loading">Loading workout history...</div>;
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="workout-history">
            <h2>Your Workout History</h2>
            {history.length === 0 ? (
                <p>No previous workouts found.</p>
            ) : (
                <div className="history-list">
                    {history.map((item, index) => (
                        <div key={index} className="history-item">
                            <div className="history-header">
                                <h3>Workout from {new Date(item.created_at).toLocaleDateString()}</h3>
                                <span className="workout-meta">
                                    {item.workout_plan.level} Level • {item.workout_plan.days_per_week} Days/Week
                                </span>
                            </div>
                            <div className="history-days">
                                {item.workout_plan.workout_days.map((day, dayIndex) => (
                                    <div key={dayIndex} className="history-day">
                                        <h4>Day {day.day_number}</h4>
                                        <p className="day-overview">{day.overview}</p>
                                        <div className="history-exercises">
                                            {day.exercises.map((exercise, exIndex) => (
                                                <div key={exIndex} className="history-exercise">
                                                    <h5>{exercise.Title}</h5>
                                                    <p>{exercise.Description}</p>
                                                    <div className="exercise-meta">
                                                        <span>{exercise.Type}</span>
                                                        <span>{exercise.Equipment}</span>
                                                        <span>{exercise.BodyPart}</span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default WorkoutHistory; 