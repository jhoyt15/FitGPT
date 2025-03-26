from mistralai.client import MistralClient
<<<<<<< HEAD
=======
from mistralai.models.chat_completion import ChatMessage
>>>>>>> 54da162c5a0fc308e9375bbfe9dc3432049ed872
import os

class MistralWorkoutAdvisor:
    def __init__(self):
        # Make sure to set MISTRAL_API_KEY in your environment variables
        self.client = MistralClient(api_key=os.getenv('MISTRAL_API_KEY'))
        
    def generate_advice(self, workout_data, research_findings):
        messages = [
<<<<<<< HEAD
            {
                "role": "system",
                "content": "You are a knowledgeable fitness coach. Provide evidence-based workout advice in a friendly manner. Keep responses concise and actionable."
            },
            {
                "role": "user",
                "content": self._create_prompt(workout_data, research_findings)
            }
        ]
        
        try:
            response = self.client.chat.complete(
=======
            ChatMessage(
                role="system",
                content="You are a knowledgeable fitness coach. Provide evidence-based workout advice in a friendly manner. Keep responses concise and actionable."
            ),
            ChatMessage(
                role="user",
                content=self._create_prompt(workout_data, research_findings)
            )
        ]
        
        try:
            response = self.client.chat(
>>>>>>> 54da162c5a0fc308e9375bbfe9dc3432049ed872
                model="mistral-tiny",
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            if not response or not response.choices:
                print("No response from Mistral API")
                return "Unable to generate AI recommendations at this time."
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating Mistral advice: {str(e)}")
            return "Unable to generate AI recommendations at this time."
        
    def _create_prompt(self, workout_data, research_findings):
        return f"""
        Based on this workout:
        Type: {workout_data.get('Type', 'N/A')}
        Body Part: {workout_data.get('BodyPart', 'N/A')}
        Equipment: {workout_data.get('Equipment', 'N/A')}
        Level: {workout_data.get('Level', 'N/A')}
        
        Description: {research_findings}
        
        Please provide:
        1. A brief form tip or safety advice
        2. One suggested modification or progression
        3. A quick recovery tip
        Keep the total response under 100 words.
        """ 