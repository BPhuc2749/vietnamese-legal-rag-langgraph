import json
import re

from benchmark.llm_judge.prompt import SYSTEM_PROMPT


MAX_RETRY = 1
RETRY_SLEEP = 5

def call_judge(
    llm,
    prompt,
):

    messages = [

        (
            "system",
            SYSTEM_PROMPT,
        ),

        (
            "human",
            prompt,
        ),

    ]

    result = llm.invoke(messages)

    return result.model_dump()