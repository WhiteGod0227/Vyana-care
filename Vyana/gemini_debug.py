import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY", "")
genai.configure(api_key=key)
model = genai.GenerativeModel("models/gemini-2.0-flash")

prompt = "Return ONLY JSON: {\"x\":\"hi\"}"

resp = model.generate_content(prompt)
print("TEXT:", repr(getattr(resp, "text", None)))
print("RAW:", resp)
