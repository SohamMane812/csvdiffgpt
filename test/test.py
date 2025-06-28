from csvdiffgpt import summarize
from dotenv import load_dotenv
import os
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

result = summarize(
    "./baseball.csv",
    question="What insights can you provide about this dataset?",
    api_key=API_KEY,
    provider="gemini",
    model='gemini-2.0-flash'
)
print(result)