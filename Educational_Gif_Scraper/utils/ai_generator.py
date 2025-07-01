import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def suggest_gif_description(topic):
    prompt = f"Explain the concept of '{topic}' in a way that could be illustrated as an educational GIF."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"No suggestion available: {e}"
