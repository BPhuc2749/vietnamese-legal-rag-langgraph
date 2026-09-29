from langchain_core.prompts import ChatPromptTemplate

from app.prompts.loader import load_prompt
from app.schemas.planning import PlanningOutput
from app.state.state import AgentState
from app.models.model_manager import model_manager

PLANNING_PROMPT = load_prompt("planning.md")


async def planning_node(
    state: AgentState
) -> AgentState:
    llm = model_manager.get_llm()
    # --- LOGIC SLIDING WINDOW MEMORY ---
    # Lấy 6 messages cuối cùng (tương đương 3 cặp User-AI)
    full_history = state.get("chat_history", [])
    windowed_history = full_history[-6:] if len(full_history) > 6 else full_history
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                PLANNING_PROMPT,
            ),
            (
                "human",
                """
User Query:
{user_query}

Chat History:
{chat_history}
""",
            ),
        ]
    )

    structured_llm = llm.with_structured_output(PlanningOutput)

    chain = prompt | structured_llm

    result = await chain.ainvoke(
        {
            "user_query": state["user_query"],
            "chat_history": windowed_history,
        }
    )

    state["intent"] = result.intent
    state["search_mode"] = result.search_mode
    state["evidence_plan"] = result.evidence_plan

    return state