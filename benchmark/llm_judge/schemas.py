from pydantic import BaseModel, Field


class JudgeScore(BaseModel):

    faithfulness: float = Field(
        description=(
            "Mức độ câu trả lời được hỗ trợ bởi Retrieved Contexts. "
            "Giá trị trong khoảng từ 0.0 đến 1.0."
        ),
        ge=0.0,
        le=1.0,
    )

    answer_correctness: float = Field(
        description=(
            "Mức độ chính xác của câu trả lời so với Ground Truth. "
            "Giá trị trong khoảng từ 0.0 đến 1.0."
        ),
        ge=0.0,
        le=1.0,
    )