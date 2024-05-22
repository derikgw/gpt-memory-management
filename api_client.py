
import openai

def send_gpt_request(api_key, model, prompt, max_tokens=100):
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
    return response.choices[0].message["content"]
