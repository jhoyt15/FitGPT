import { useState } from "react"
import '../Content.css'



const Chat = () => {
    const [query,setQuery] = useState('')
    const [answer,setAnswer] = useState('')
    const [loading,setLoading] = useState(false)

    const answerQuestion = () => {
        fetch('/chat',{method:'POST',headers: {"Content-Type": "application/json"},credentials:'include',body:JSON.stringify({query:query,session_id:0})})
        .then(response => response.json())
        .then(data => {
            setAnswer(data.response) 
            setLoading(false)
        })
        .catch(() => setLoading(false))
    }

    const handleLoading = () => {
        setLoading(true);
    }

    return (
        <div className="form-group">
            <input type = "search" value = {query} onChange ={(e) => setQuery(e.target.value)} onKeyDown={(e) => {
                if(e.key === "Enter") {
                    handleLoading()
                    answerQuestion()
                }
            }}>
            </input>
            { loading ? <p> Thinking... </p> : (
                <p>
                {answer}
                </p>
                )
            }
        </div>
    )
}

export default Chat