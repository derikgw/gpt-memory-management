import openai
from openai import OpenAI, OpenAIError

def send_gpt_request(api_key, model, prompt, max_tokens=100):
    # Set up the OpenAI client with the provided API key
    client = OpenAI()
    client.api_key = api_key
    response = client.chat.completions.create(
        model="gpt-4o-2024-05-13",
        messages=[{"role": "user", "content": f"{prompt}: "}],
        stream=True  # Stream responses to process them as they arrive
    )

    try:
        buffered_response = ""
        # Process each chunk of the response
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                buffered_response += chunk.choices[0].delta.content
        # Yield any remaining content in the buffer
        return buffered_response
    except OpenAIError as e:
        # Handle errors from the OpenAI API
        error_msg = e.args[0].text.strip()  # Extract and return the error message
        return error_msg
