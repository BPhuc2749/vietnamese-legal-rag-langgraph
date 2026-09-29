import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from benchmark.llm_judge.schemas import JudgeScore

load_dotenv()


JUDGE_MODEL = "gemini-3.6-flash"


def get_judge():

    llm = ChatGoogleGenerativeAI(

        model=JUDGE_MODEL,

        api_key=os.getenv("GOOGLE_API_KEY"),

        temperature=0,

        timeout=300,

        max_retries=3,

    )

    return llm.with_structured_output(JudgeScore)