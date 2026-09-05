from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask_groq(prompt, system_message="You are a helpful data analyst assistant.", temperature=0.3):
    # Try primary model first, fallback if not available
    models_to_try = [
        "llama-3.3-70b-versatile",
        "llama3-70b-8192",
        "mixtral-8x7b-32768"
    ]
    
    for model in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                continue
            else:
                return f"AI Error: {str(e)}"
    
    return "AI Error: No available models found"