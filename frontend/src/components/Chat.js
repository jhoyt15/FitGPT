import { useState } from "react"
import '../Content.css'
import './Chat.css'



const Chat = () => {
    const [query,setQuery] = useState('')
    const [answer,setAnswer] = useState('')
    const [loading,setLoading] = useState(false)

    const answerQuestion = () => {
        fetch('/chat',{method:'POST',headers: {"Content-Type": "application/json"},credentials:'include',body:JSON.stringify({query:query,session_id:0})})
        .then(response => response.json())
        .then(data => {
            console.log(data.response)
            setAnswer(data.response) 
            setLoading(false)
        })
        .catch(() => setLoading(false))
    }

    const handleLoading = () => {
        setLoading(true);
    }

    return (
        <div>
            <h1>Ask Me Anything</h1>
            <div className="form-group">
                <input type = "search" className = "query-input" value = {query} onChange ={(e) => setQuery(e.target.value)} onKeyDown={(e) => {
                    if(e.key === "Enter") {
                        handleLoading()
                        answerQuestion()
                    }
                }}>
                </input>
                { loading ? <p> Thinking... </p> : (
                    <pre className="ai-response">
                    {answer}
                    </pre>
                    )
                }
            </div>
        </div>
    )
}

export default Chat