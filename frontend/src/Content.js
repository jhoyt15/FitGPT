import { useState } from 'react'

const Content = () => {
    const [response, setResponse] = useState('')

    const queryES = () => {
        setResponse('Hello World')
    }

    return (
        <main>
            <p>
                Hello, world!
            </p>
            <input type = "search" onKeyDown = {(e) => {
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