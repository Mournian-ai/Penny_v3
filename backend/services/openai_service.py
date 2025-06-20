import openai
from config import settings

openai.api_key = settings.OPENAI_API_KEY

async def query_openai(prompt: str, history=None, system_prompt=None) -> str:
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": prompt})

    try:
        response = await openai.ChatCompletion.acreate(
            model=getattr(settings, "OPENAI_MODEL", "gpt-4o"),
            messages=messages,
            temperature=0.85
        )
        return response.choices[0].message.content.strip()

    except openai.error.RateLimitError as e:
        print("[OpenAI] Rate limit exceeded.")
        return "I'm being throttled by the universe. Try again in a bit."
    except openai.error.Timeout as e:
        print("[OpenAI] Request timed out.")
        return "Too slow! Something took too long..."
    except openai.error.APIError as e:
        print("[OpenAI] API error.")
        return "Something broke while I was thinking. Try again?"
    except Exception as e:
        print(f"[OpenAI] Unexpected error: {e}")
        return "Sorry, I had a glitch in the sarcasm processor."
