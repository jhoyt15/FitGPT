import { useState } from 'react'
import './Content.css'

const Content = () => {
    const [response, handleResponse] = useState([])
    const [userInput, setUserInput] = useState({
        fitnessLevel: "beginner",
        goal: "",
        equipment: "",
        timeAvailable: "30",
        preferences: ""
    })
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const handleInputChange = (e) => {
        const { name, value } = e.target
        setUserInput(prev => ({
            ...prev,
            [name]: value
        }))
    }

    const generateWorkout = () => {
        setLoading(true)
        setError(null)
        
        const prompt = `I am a ${userInput.fitnessLevel} looking to ${userInput.goal}. 
            I have access to ${userInput.equipment || 'basic equipment'} and 
            ${userInput.timeAvailable} minutes available. 
            Additional preferences: ${userInput.preferences}`

        fetch('/query', {
            method: 'POST',
            headers: { "Content-Type": "application/json" },
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
        <main className="main-container">
            <div className="workout-form">
                <h2>Generate Your Custom Workout</h2>
                
                <div className="form-group">
                    <label>Fitness Level:</label>
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
                    <label>Your Goal:</label>
                    <input
                        type="text"
                        name="goal"
                        placeholder="e.g., build muscle, lose weight, improve endurance"
                        value={userInput.goal}
                        onChange={handleInputChange}
                    />
                </div>

                <div className="form-group">
                    <label>Available Equipment:</label>
                    <input
                        type="text"
                        name="equipment"
                        placeholder="e.g., dumbbells, resistance bands, no equipment"
                        value={userInput.equipment}
                        onChange={handleInputChange}
                    />
                </div>

                <div className="form-group">
                    <label>Time Available (minutes):</label>
                    <input
                        type="number"
                        name="timeAvailable"
                        min="5"
                        max="120"
                        value={userInput.timeAvailable}
                        onChange={handleInputChange}
                    />
                </div>

                <div className="form-group">
                    <label>Additional Preferences:</label>
                    <textarea
                        name="preferences"
                        placeholder="e.g., prefer cardio, avoid jumping, focus on upper body"
                        value={userInput.preferences}
                        onChange={handleInputChange}
                        rows="3"
                    />
                </div>

                <button onClick={generateWorkout} className="generate-button">
                    Generate Workout
                </button>
            </div>

            {loading && <p className="loading-message">Generating your custom workout...</p>}
            {error && <p className="error-message">{error}</p>}
            
            {!loading && !error && response.length > 0 && (
                <div className="workout-plan">
                    <h3>Your Custom Workout Plan</h3>
                    <div className="workout-list">
                        {response.map((workout, index) => (
                            <div key={index} className="workout-card">
                                <h4 className="workout-title">{workout._source.Title.split(' -')[0]}</h4>
                                <p className="workout-description">{workout._source.Description}</p>
                                <div className="workout-meta">
                                    <span>Type: {workout._source.Type}</span>
                                    <span>Equipment: {workout._source.Equipment}</span>
                                    <span>Level: {workout._source.Level}</span>
                                    <span>Target: {workout._source.BodyPart}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </main>
    )
}

export default Content