import { useState } from 'react'

const Content = () => {
    const [response, handleResponse] = useState([]) //ElasticSearch response state
    const [query,handleQuery] = useState("") //ElasticSearch Query

    const queryES = () => {
        fetch('/query',{method:'POST',headers: {"Content-Type": "application/json"},body:JSON.stringify({query:query})})
            .then(response => response.json())
            .then(data => handleResponse(data.response))
            .catch((e) => console.log(e))
    }

    return (
        <main> 
            <input type = "search" value={query} onChange={(e) => handleQuery(e.target.value)} onKeyDown = {(e) => {
                if(e.key === "Enter")
                    queryES()
            }}>
            </input>

            { response.length != 0 ? (   //Check if response has any items, if it doesn't display "No Results Found"
                <ul>
                    { response.map((workout) => 
                        <li className = "workout" key = {workout.id}>
                            {workout._source.Title}
                        </li> 
                    )}
                </ul>
            ) : (
                <p>No Results Found</p>   
            )}
        </main>
    )
}

export default Content