import os
import re
import time
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

class ResilientLLM:
    """
    A multi-provider resilient LLM wrapper that tries the primary LLM first.
    If a short-window rate limit occurs (e.g. Groq TPM window needing < 2s),
    it pauses and retries once before seamlessly falling back to the secondary LLM.
    """
    def __init__(self, primary_llm, fallback_llm=None):
        self.primary = primary_llm
        self.fallback = fallback_llm

    def invoke(self, messages, **kwargs):
        try:
            return self.primary.invoke(messages, **kwargs)
        except Exception as e:
            err_msg = str(e).lower()
            # If rate limit on tokens per minute (TPM) says "try again in X ms/s", wait briefly and retry primary
            if "rate limit" in err_msg or "429" in err_msg:
                try:
                    wait_sec = 2.0
                    match_s = re.search(r'try again in ([\d\.]+)s', err_msg)
                    if match_s:
                        wait_sec = float(match_s.group(1)) + 0.5
                    match_ms = re.search(r'try again in (\d+)ms', err_msg)
                    if match_ms:
                        wait_sec = (int(match_ms.group(1)) / 1000.0) + 0.5
                    
                    if wait_sec <= 5.0:
                        print(f"\n[ResilientLLM] Primary model requested brief rate-limit backoff ({wait_sec:.1f}s). Retrying...", flush=True)
                        time.sleep(wait_sec)
                        return self.primary.invoke(messages, **kwargs)
                except Exception as retry_err:
                    print(f"[ResilientLLM] Primary retry encountered: {retry_err}", flush=True)

            if self.fallback:
                print(f"\n[ResilientLLM] Primary model unavailable. Seamlessly switching to Fallback LLM...", flush=True)
                return self.fallback.invoke(messages, **kwargs)
            raise e

def get_llm(temperature: float = 0.2):
    """
    Returns a resilient LLM instance.
    Primary: Groq Cloud (open-source openai/gpt-oss-20b or configured GROQ_MODEL).
    Fallback: Google Gemini (gemini-1.5-flash with 1,000,000 TPM quota).
    """
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    provider = os.getenv("LLM_PROVIDER", "").lower().strip()

    # Create Gemini fallback instance
    from langchain_google_genai import ChatGoogleGenerativeAI
    gemini_model = os.getenv("LLM_MODEL", "gemini-3.6-flash")
    gemini_llm = ChatGoogleGenerativeAI(
        model=gemini_model,
        temperature=temperature,
        max_output_tokens=8192
    )

    if groq_api_key and groq_api_key != "your_groq_api_key_here" and provider != "gemini":
        try:
            from langchain_groq import ChatGroq
            groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
            print(f"[LLM Factory] Configured Primary: Groq ({groq_model}) | Fallback: Gemini ({gemini_model})", flush=True)
            groq_kwargs = {
                "model": groq_model,
                "temperature": temperature,
                "groq_api_key": groq_api_key,
                "max_tokens": 4096,
                "max_retries": 1
            }
            if "gpt-oss" in groq_model.lower():
                groq_kwargs["reasoning_effort"] = "low"

            groq_llm = ChatGroq(**groq_kwargs)
            return ResilientLLM(primary_llm=groq_llm, fallback_llm=gemini_llm)
        except Exception as e:
            print(f"[LLM Factory] Groq init failed: {e}. Defaulting to Gemini.", flush=True)

    print(f"[LLM Factory] Using Google Gemini ({gemini_model})", flush=True)
    return gemini_llm
