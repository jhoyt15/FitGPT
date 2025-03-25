import { useState, useEffect } from 'react'
import { GoogleOAuthProvider } from '@react-oauth/google'
import Auth from './components/Auth'
import WorkoutHistory from './components/WorkoutHistory'
import TimeoutWarning from './components/TimeoutWarning'
import './Content.css'
import { auth } from './firebase'

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
    const [response, setResponse] = useState(null)
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
    const [aiCustomization, setAiCustomization] = useState("")
    const [showAiAssistant, setShowAiAssistant] = useState(false)
    const [aiSuggestions, setAiSuggestions] = useState([])
    const [showTimeoutWarning, setShowTimeoutWarning] = useState(false);
    const [timeLeft, setTimeLeft] = useState(60); // 60 seconds warning
    const [lastActivity, setLastActivity] = useState(Date.now());
    const TIMEOUT_DURATION = 5 * 60 * 1000; // 5 minutes
    const WARNING_DURATION = 60; // 60 seconds warning

    useEffect(() => {
        console.log('User state changed:', user);
    }, [user]);

    // AI assistant suggestions
    const predefinedSuggestions = [
        "Tailor this workout for swimming performance",
        "Modify for someone with lower back issues",
        "Focus more on functional movements",
        "Add more compound exercises",
        "Make this plan more cardio-focused",
        "Adjust for a busy professional with limited time",
        "Optimize for maximum fat loss"
    ]

    useEffect(() => {
        // Set initial suggestions
        setAiSuggestions(predefinedSuggestions)
    }, [])

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
        // Reset timeout warning state and timer
        setShowTimeoutWarning(false);
        setTimeLeft(WARNING_DURATION);
        setLastActivity(Date.now());
    };

    // Handle user activity
    const handleUserActivity = () => {
        if (!showTimeoutWarning) {
            setLastActivity(Date.now());
        }
    };

    // Add event listeners for user activity
    useEffect(() => {
        if (!user) return;

        const events = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart'];
        events.forEach(event => {
            window.addEventListener(event, handleUserActivity);
        });

        return () => {
            events.forEach(event => {
                window.removeEventListener(event, handleUserActivity);
            });
        };
    }, [user, showTimeoutWarning]);

    // Check for timeout
    useEffect(() => {
        if (!user) return;

        const checkTimeout = () => {
            const timeSinceLastActivity = Date.now() - lastActivity;
            
            if (timeSinceLastActivity >= TIMEOUT_DURATION && !showTimeoutWarning) {
                setShowTimeoutWarning(true);
                setTimeLeft(WARNING_DURATION);
            }
        };

        const interval = setInterval(checkTimeout, 1000);
        return () => clearInterval(interval);
    }, [user, lastActivity, showTimeoutWarning]);

    // Countdown timer for warning
    useEffect(() => {
        if (!showTimeoutWarning || !user) return;

        const timer = setInterval(() => {
            setTimeLeft(prev => {
                if (prev <= 1) {
                    clearInterval(timer);
                    handleLogout();
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => clearInterval(timer);
    }, [showTimeoutWarning, user]);

    const handleStayLoggedIn = () => {
        setShowTimeoutWarning(false);
        setLastActivity(Date.now());
        setTimeLeft(WARNING_DURATION);
    };

    const handleLogout = async () => {
        try {
            await auth.signOut();
            setUser(null);
        } catch (error) {
            console.error('Error logging out:', error);
        }
    };

    const generateWorkout = async () => {
        setLoading(true)
        setError(null)
        
        try {
            const token = await auth.currentUser.getIdToken();
            const prompt = `I am a ${userInput.fitnessLevel} looking to ${userInput.goal}. 
                I have access to ${userInput.equipment || 'basic equipment'} and 
                ${userInput.timeAvailable} minutes available for ${userInput.daysPerWeek} days per week. 
                Additional preferences: ${userInput.preferences}`

            // Add AI customization if present
            const finalPrompt = aiCustomization 
                ? `${prompt} And please: ${aiCustomization}`
                : prompt;

            const response = await fetch('http://localhost:5001/query', {
                method: 'POST',
                headers: { 
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                credentials: 'include',
                body: JSON.stringify({ query: finalPrompt })
            });

            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            setResponse(data.workout_plan);
            setLoading(false);
        } catch (error) {
            console.error('Error:', error);
            setError('Failed to generate workout');
            setLoading(false);
        }
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

                            <div className="ai-assistant-wrapper">
                                <button 
                                    type="button" 
                                    className="toggle-ai-assistant"
                                    onClick={() => setShowAiAssistant(!showAiAssistant)}
                                >
                                    {showAiAssistant ? "Hide AI Assistant" : "Show AI Assistant"}
                                </button>
                                
                                {showAiAssistant && (
                                    <div className="ai-assistant">
                                        <h3>AI Workout Assistant</h3>
                                        <p>Further customize your workout with natural language instructions:</p>
                                        
                                        <textarea
                                            className="ai-input"
                                            value={aiCustomization}
                                            onChange={(e) => setAiCustomization(e.target.value)}
                                            placeholder="e.g., Tailor this for a swimmer, focus on functional movements, etc."
                                            rows="3"
                                        />
                                        
                                        <div className="ai-suggestions">
                                            <h4>Try these suggestions:</h4>
                                            <div className="suggestion-chips">
                                                {aiSuggestions.map((suggestion, index) => (
                                                    <button 
                                                        key={index}
                                                        className="suggestion-chip"
                                                        onClick={() => setAiCustomization(suggestion)}
                                                    >
                                                        {suggestion}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                )}
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

                        {showTimeoutWarning && (
                            <TimeoutWarning
                                onStay={handleStayLoggedIn}
                                onLogout={handleLogout}
                                timeLeft={timeLeft}
                            />
                        )}
                    </div>
                )}
            </main>
        </GoogleOAuthProvider>
    )
}

export default Content