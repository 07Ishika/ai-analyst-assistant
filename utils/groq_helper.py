from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask_groq(prompt, system_message="You are a helpful data analyst assistant.", temperature=0.3):
    
    models_to_try = [
        "openai/gpt-oss-120b",
        "qwen/qwen3.6-27b",
        "openai/gpt-oss-20b"
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
            if "not found" in str(e).lower() or "404" in str(e).lower() or "decommissioned" in str(e).lower():
                continue
            else:
                return f"AI Error: {str(e)}"
    
    return "AI Error: No available models found"