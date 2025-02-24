import { useState, useEffect } from 'react'
import { GoogleOAuthProvider } from '@react-oauth/google'
import Auth from './components/Auth'
import WorkoutHistory from './components/WorkoutHistory'
import './Content.css'

const WorkoutCard = ({ workout }) => {
    return (
        <div className="workout-card">
            <h3>{workout._source.Title}</h3>
            <div className="workout-details">
                <p><strong>Description:</strong> {workout._source.Description}</p>
                <p><strong>Type:</strong> {workout._source.Type}</p>
                <p><strong>Equipment:</strong> {workout._source.Equipment}</p>
                <p><strong>Level:</strong> {workout._source.Level}</p>
                <p><strong>Body Part:</strong> {workout._source.BodyPart}</p>
            </div>
            
            {workout._source.AI_Recommendations && (
                <div className="ai-recommendations">
                    <h4>🤖 AI Coach Tips:</h4>
                    <p>{workout._source.AI_Recommendations}</p>
                </div>
            )}
        </div>
    );
};

const Content = () => {
    console.log('API URL:', process.env.REACT_APP_API_URL);
    const [response, handleResponse] = useState([])
    const [user, setUser] = useState(null)
    const [userInput, setUserInput] = useState({
        fitnessLevel: "beginner",
        goal: "",
        equipment: "",
        timeAvailable: "30",
        preferences: "",
        daysPerWeek: "3"
    })
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        console.log('User state changed:', user);
    }, [user]);

    const handleInputChange = (e) => {
        const { name, value } = e.target
        setUserInput(prev => ({
            ...prev,
            [name]: value
        }))
    }

    const handleUserLogin = (userData) => {
        console.log('Setting user state:', userData);
        setUser(userData);
    };

    const generateWorkout = () => {
        setLoading(true)
        setError(null)
        
        const prompt = `I am a ${userInput.fitnessLevel} looking to ${userInput.goal}. 
            I have access to ${userInput.equipment || 'basic equipment'} and 
            ${userInput.timeAvailable} minutes available for ${userInput.daysPerWeek} days per week. 
            Additional preferences: ${userInput.preferences}`

        fetch('http://localhost:5001/query', {
            method: 'POST',
            headers: { 
                "Content-Type": "application/json"
            },
            credentials: 'include',
            body: JSON.stringify({ query: prompt })
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok')
            return response.json()
        })
        .then(data => {
            handleResponse(data.response)
            setLoading(false)
        })
        .catch((error) => {
            console.error('Error:', error)
            setError('Failed to generate workout')
            setLoading(false)
        })
    }

    return (
        <GoogleOAuthProvider clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}>
            <main className="main-container">
                {!user ? (
                    <div className="login-page">
                        <div className="login-container">
                            <h1>Welcome to FitGPT</h1>
                            <p>Sign in to create and track your personalized workout plans</p>
                            <Auth 
                                onLogin={handleUserLogin}
                                onLogout={() => setUser(null)}
                                user={user}
                            />
                        </div>
                    </div>
                ) : (
                    <div className="content-wrapper">
                        <div className="header">
                            <div className="header-content">
                                <h1>FitGPT</h1>
                                <div className="user-section">
                                    <Auth 
                                        onLogin={setUser}
                                        onLogout={() => setUser(null)}
                                        user={user}
                                    />
                                </div>
                            </div>
                        </div>
                        <div className="workout-form">
                            <h2>Generate Your Workout Plan</h2>
                            
                            <div className="form-group">
                                <label>Fitness Level</label>
                                <select
                                    name="fitnessLevel"
                                    value={userInput.fitnessLevel}
                                    onChange={handleInputChange}
                                >
                                    <option value="beginner">Beginner</option>
                                    <option value="intermediate">Intermediate</option>
                                    <option value="advanced">Advanced</option>
                                </select>
                            </div>

                            <div className="form-group">
                                <label>Days per Week</label>
                                <select
                                    name="daysPerWeek"
                                    value={userInput.daysPerWeek}
                                    onChange={handleInputChange}
                                >
                                    <option value="2">2 days</option>
                                    <option value="3">3 days</option>
                                    <option value="4">4 days</option>
                                    <option value="5">5 days</option>
                                    <option value="6">6 days</option>
                                </select>
                            </div>

                            <div className="form-group">
                                <label>Fitness Goal</label>
                                <input
                                    type="text"
                                    name="goal"
                                    value={userInput.goal}
                                    onChange={handleInputChange}
                                    placeholder="e.g., build muscle, lose weight, improve endurance"
                                />
                            </div>

                            <div className="form-group">
                                <label>Available Equipment</label>
                                <input
                                    type="text"
                                    name="equipment"
                                    value={userInput.equipment}
                                    onChange={handleInputChange}
                                    placeholder="e.g., dumbbells, resistance bands, no equipment"
                                />
                            </div>

                            <div className="form-group">
                                <label>Time Available (minutes)</label>
                                <input
                                    type="number"
                                    name="timeAvailable"
                                    value={userInput.timeAvailable}
                                    onChange={handleInputChange}
                                    min="10"
                                    max="120"
                                />
                            </div>

                            <div className="form-group">
                                <label>Additional Preferences</label>
                                <textarea
                                    name="preferences"
                                    value={userInput.preferences}
                                    onChange={handleInputChange}
                                    placeholder="Any specific preferences or limitations?"
                                    rows="3"
                                />
                            </div>

                            <button
                                onClick={generateWorkout}
                                disabled={loading}
                                className="generate-button"
                            >
                                {loading ? 'Generating...' : 'Generate Workout Plan'}
                            </button>
                        </div>

                        {error && (
                            <div className="error">
                                {error}
                            </div>
                        )}

                        {loading && (
                            <div className="loading">
                                Generating your personalized workout plan...
                            </div>
                        )}

                        {response && response.workout_days && (
                            <div className="workout-plan">
                                <div className="plan-overview">
                                    <h2>Workout Plan Overview</h2>
                                    <p>{response.plan_overview}</p>
                                    <div className="plan-metadata">
                                        <p>Level: {response.level}</p>
                                        <p>Days per week: {response.days_per_week}</p>
                                        <p>Minutes per session: {response.minutes_per_session}</p>
                                    </div>
                                </div>

                                {response.workout_days.map((day, index) => (
                                    <div key={index} className="workout-day">
                                        <h3>Day {day.day_number}</h3>
                                        <p className="day-overview">{day.overview}</p>
                                        
                                        <div className="exercises">
                                            {day.exercises.map((exercise, exIndex) => (
                                                <div key={exIndex} className="exercise-card">
                                                    <h4>{exercise.Title}</h4>
                                                    <p className="exercise-details">{exercise.Description}</p>
                                                    <div className="exercise-metadata">
                                                        <span>Type: {exercise.Type}</span>
                                                        <span>Equipment: {exercise.Equipment}</span>
                                                        <span>Body Part: {exercise.BodyPart}</span>
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
                        )}

                        {user && <WorkoutHistory user={user} />}
                    </div>
                )}
            </main>
        </GoogleOAuthProvider>
    )
}

export default Content