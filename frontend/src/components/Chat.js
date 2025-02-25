import { useState } from "react"
import '../Content.css'



const Chat = () => {
    const [query,setQuery] = useState('')
    const [answer,setAnswer] = useState('')

    const answerQuestion = () => {
        fetch('/prompt-llm',{method:'POST',headers: {"Content-Type": "application/json"},body:JSON.stringify({query:query})})
        .then(response => response.json())
        .then(data => setAnswer(data.response))
    }

    return (
        <div className="form-group">
            <input type = "search" value = {query} onChange ={(e) => setQuery(e.target.value)} onKeyDown={(e) => {
                if(e.key === "Enter")
                    answerQuestion()
            }}>
            </input>
            <p>
                {answer}
            </p>
        </div>
    )
}

export default Chat