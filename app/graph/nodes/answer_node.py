from langchain_core.prompts import ChatPromptTemplate

from app.prompts.loader import load_prompt
from app.schemas.answer import AnswerOutput
from app.state.state import AgentState
from app.models.model_manager import model_manager
ANSWER_PROMPT = load_prompt("answer.md")


async def answer_node(
    state: AgentState
) -> AgentState:
    llm = model_manager.get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                ANSWER_PROMPT,
            ),
            (
                "human",
                """
Intent:
{intent}

User Query:
{user_query}

Evidence Plan:
{evidence_plan}

RAG Results:
{rag_results}

Web Results:
{web_results}
""",
            ),
        ]
    )

    structured_llm = llm.with_structured_output(
        AnswerOutput
    )

    chain = prompt | structured_llm

    result = await chain.ainvoke(
        {
            "intent": state["intent"],
            "user_query": state["user_query"],
            "evidence_plan": state["evidence_plan"],
            "rag_results": state["rag_results"],
            "web_results": state["web_results"],
        }
    )

    state["final_answer"] = result.final_answer
    state["citations"] = result.citations

    return state