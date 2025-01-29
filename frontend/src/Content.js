import { useState } from 'react'

const Content = () => {
    const [response, setResponse] = useState('')
    const [query,setQuery] = useState('')

    const queryES = (query) => {
        setResponse('Hello World')
        fetch('/query',{method:"POST",body:JSON.stringify({query:query})})
            .then(response => response.json())
            .then(data => setResponse(data))
    }

    return (
        <main>
            <p>
                Hello, world!
            </p>
            <input type = "search" value={query} onChange={setQuery} onKeyDown = {(e) => {
                if(e.key === "Enter")
                    queryES()
            }}>
            </input>
            <p>
                {response}
            </p>
        </main>
    )
}

export default Content