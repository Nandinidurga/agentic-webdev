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
                try:
                    return self.fallback.invoke(messages, **kwargs)
                except Exception as fb_err:
                    print(f"[ResilientLLM] Fallback LLM also encountered error: {fb_err}", flush=True)
                    raise fb_err
            raise e

def get_llm(temperature: float = 0.2):
    """
    Returns a resilient LLM instance.
    Primary: Groq Cloud (open-source openai/gpt-oss-20b or llama-3.3-70b-versatile).
    Fallback: Google Gemini (gemini-1.5-flash with large token quota).
    Configurable output ceiling via MAX_TOKENS env var (default: 8192).
    """
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    google_api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    provider = os.getenv("LLM_PROVIDER", "").lower().strip()
    max_tokens = int(os.getenv("MAX_TOKENS", "8192"))

    # Determine stable Gemini model
    gemini_model = os.getenv("LLM_MODEL", "gemini-1.5-flash").strip()
    if gemini_model in ["gemini-3.6-flash", ""]:
        gemini_model = "gemini-1.5-flash"

    # Build Gemini instance if key is available
    gemini_llm = None
    if google_api_key and google_api_key != "your_gemini_api_key_here":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            gemini_llm = ChatGoogleGenerativeAI(
                model=gemini_model,
                temperature=temperature,
                max_output_tokens=max_tokens,
                google_api_key=google_api_key
            )
        except Exception as e:
            print(f"[LLM Factory] Gemini initialization notice: {e}", flush=True)

    # Build Groq instance if configured and provider is not forced to gemini
    groq_llm = None
    if groq_api_key and groq_api_key != "gsk_your_groq_api_key_here" and provider != "gemini":
        try:
            from langchain_groq import ChatGroq
            groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
            groq_kwargs = {
                "model": groq_model,
                "temperature": temperature,
                "groq_api_key": groq_api_key,
                "max_tokens": max_tokens,
                "max_retries": 1
            }
            if "gpt-oss" in groq_model.lower():
                groq_kwargs["reasoning_effort"] = "low"

            groq_llm = ChatGroq(**groq_kwargs)
        except Exception as e:
            print(f"[LLM Factory] Groq init failed: {e}. Will rely on Gemini.", flush=True)

    # Return multi-provider ResilientLLM or appropriate active instance
    if groq_llm and gemini_llm:
        print(f"[LLM Factory] Resilient Pipeline: Primary Groq ({os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')}) -> Fallback Gemini ({gemini_model}) [max_tokens={max_tokens}]", flush=True)
        return ResilientLLM(primary_llm=groq_llm, fallback_llm=gemini_llm)
    elif groq_llm:
        print(f"[LLM Factory] Using Groq Cloud ({os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')}) [max_tokens={max_tokens}]", flush=True)
        return groq_llm
    elif gemini_llm:
        print(f"[LLM Factory] Using Google Gemini ({gemini_model}) [max_tokens={max_tokens}]", flush=True)
        return gemini_llm

    # If neither key is provided, instantiate fallback Gemini with default env lookup
    from langchain_google_genai import ChatGoogleGenerativeAI
    print(f"[LLM Factory] Defaulting to Gemini ({gemini_model}) [max_tokens={max_tokens}]", flush=True)
    return ChatGoogleGenerativeAI(
        model=gemini_model,
        temperature=temperature,
        max_output_tokens=max_tokens
    )
