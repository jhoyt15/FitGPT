import React, { useEffect, useState } from 'react';
import { auth } from '../firebase';

const WorkoutHistory = ({ user }) => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [clearing, setClearing] = useState(false);
    const [expandedWorkouts, setExpandedWorkouts] = useState({});

    const fetchHistory = async () => {
        if (!user) return;
        
        setLoading(true);
        try {
            const token = await auth.currentUser.getIdToken();
            const response = await fetch('http://localhost:5001/user/workout-history', {
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                credentials: 'include'
            });
            const data = await response.json();
            if (data.history) {
                setHistory(data.history);
                // Initialize all workouts as expanded
                const initialExpanded = data.history.reduce((acc, _, index) => {
                    acc[index] = true;
                    return acc;
                }, {});
                setExpandedWorkouts(initialExpanded);
            }
        } catch (error) {
            console.error('Failed to fetch workout history:', error);
            setError('Failed to load workout history');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, [user]);

    const toggleWorkout = (index) => {
        setExpandedWorkouts(prev => ({
            ...prev,
            [index]: !prev[index]
        }));
    };

    const clearHistory = async () => {
        if (!window.confirm('Are you sure you want to clear your workout history? This action cannot be undone.')) {
            return;
        }

        setClearing(true);
        try {
            const token = await auth.currentUser.getIdToken();
            const response = await fetch('http://localhost:5001/user/workout-history', {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                credentials: 'include'
            });
            const data = await response.json();
            if (response.ok) {
                setHistory([]);
                setExpandedWorkouts({});
                alert('Workout history cleared successfully!');
            } else {
                throw new Error(data.error || 'Failed to clear history');
            }
        } catch (error) {
            console.error('Failed to clear workout history:', error);
            alert('Failed to clear workout history. Please try again.');
        } finally {
            setClearing(false);
        }
    };

    if (!user) return null;
    if (loading) return <div className="loading">Loading workout history...</div>;
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="workout-history">
            <div className="history-header">
                <h2>Your Workout History</h2>
                {history.length > 0 && (
                    <button 
                        className="clear-history-button"
                        onClick={clearHistory}
                        disabled={clearing}
                    >
                        {clearing ? 'Clearing...' : 'Clear History'}
                    </button>
                )}
            </div>
            {history.length === 0 ? (
                <p>No previous workouts found.</p>
            ) : (
                <div className="history-list">
                    {history.map((item, index) => (
                        <div key={index} className="history-item">
                            <div className="history-header" onClick={() => toggleWorkout(index)}>
                                <div className="history-header-content">
                                    <h3>Workout from {new Date(item.created_at).toLocaleDateString()}</h3>
                                    <span className="workout-meta">
                                        {item.workout_plan.level} Level • {item.workout_plan.days_per_week} Days/Week
                                    </span>
                                </div>
                                <button className={`toggle-button ${expandedWorkouts[index] ? 'expanded' : ''}`}>
                                    ▼
                                </button>
                            </div>
                            <div className={`history-days ${expandedWorkouts[index] ? '' : 'collapsed'}`}>
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
                                                    {exercise.AI_Recommendations && (
                                                        <div className="ai-recommendations">
                                                            <h4>💡 AI Coach Tips</h4>
                                                            <p>{exercise.AI_Recommendations}</p>
                                                        </div>
                                                    )}
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