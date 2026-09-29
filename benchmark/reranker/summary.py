import json
from tabulate import tabulate


# =========================
# Config path
# =========================

LLM_EVALUATION_PATH = (
    r"D:\legal-technology-agentic-rag\benchmark\reranker\results\llm_evaluation.json"
)

RERANK_RESULT_PATH = (
    r"D:\legal-technology-agentic-rag\benchmark\reranker\results\answer_benchmark_reranker.json"
)



# =========================
# Load JSON
# =========================

def load_json(path):

    with open(path, "r", encoding="utf-8") as f:

        return json.load(f)



# =========================
# Average function
# =========================

def average(values):

    if len(values) == 0:
        return 0

    return sum(values) / len(values)



# =========================
# Summarize LLM Evaluation
# =========================

def summarize_llm_scores(data):

    no_rerank_faithfulness = []
    rerank_faithfulness = []

    no_rerank_correctness = []
    rerank_correctness = []


    for item in data:

        no_rerank = item.get("no_rerank", {})
        rerank = item.get("rerank", {})


        if "faithfulness" in no_rerank:
            no_rerank_faithfulness.append(
                float(no_rerank["faithfulness"])
            )


        if "faithfulness" in rerank:
            rerank_faithfulness.append(
                float(rerank["faithfulness"])
            )


        if "answer_correctness" in no_rerank:
            no_rerank_correctness.append(
                float(no_rerank["answer_correctness"])
            )


        if "answer_correctness" in rerank:
            rerank_correctness.append(
                float(rerank["answer_correctness"])
            )



    return {

        "Faithfulness": {

            "no_rerank":
                average(no_rerank_faithfulness),

            "rerank":
                average(rerank_faithfulness)

        },


        "Answer Correctness": {

            "no_rerank":
                average(no_rerank_correctness),

            "rerank":
                average(rerank_correctness)

        }

    }



# =========================
# Summarize rerank latency
# =========================

def summarize_latency(data):

    times = []


    for item in data:

        rerank = item.get("rerank", {})


        rerank_time = rerank.get("rerank_time")


        if rerank_time is None:
            continue


        try:

            times.append(
                float(rerank_time)
            )


        except ValueError:

            continue



    if len(times) == 0:

        raise ValueError(
            """
Không tìm thấy rerank_time trong field rerank.

Kiểm tra format:
item["rerank"]["rerank_time"]
"""
        )


    return {

        "Total rerank time (s)":
            sum(times),


        "Average rerank time/question (s)":
            sum(times) / len(times),


        "Min rerank time (s)":
            min(times),


        "Max rerank time (s)":
            max(times),


        "Number of measured questions":
            len(times)

    }



# =========================
# Print evaluation table
# =========================

def print_score_table(metrics):


    table = []


    for metric, values in metrics.items():


        no_rerank = values["no_rerank"]

        rerank = values["rerank"]


        absolute_improvement = (
            rerank - no_rerank
        )


        relative_improvement = (

            absolute_improvement
            /
            no_rerank
            *
            100

            if no_rerank != 0

            else 0
        )



        table.append(
            [

                metric,

                f"{no_rerank:.4f}",

                f"{rerank:.4f}",

                f"{absolute_improvement:+.4f}",

                f"{relative_improvement:+.2f}%"

            ]
        )



    headers = [

        "Metric",

        "No Rerank",

        "Rerank",

        "Absolute Improvement",

        "Relative Improvement"

    ]



    print("\n========== LLM Evaluation Score ==========\n")


    print(

        tabulate(

            table,

            headers=headers,

            tablefmt="grid"

        )

    )



# =========================
# Print latency table
# =========================

def print_latency_table(latency):


    table = []


    for key, value in latency.items():

        if isinstance(value, float):

            value = f"{value:.4f}"


        table.append(
            [
                key,
                value
            ]
        )



    print("\n========== Reranker Latency ==========\n")


    print(

        tabulate(

            table,

            headers=[
                "Metric",
                "Value"
            ],

            tablefmt="grid"

        )

    )



# =========================
# Main
# =========================

def main():

    print("Loading evaluation files...")


    llm_eval = load_json(
        LLM_EVALUATION_PATH
    )


    rerank_result = load_json(
        RERANK_RESULT_PATH
    )


    print(
        f"Total evaluation questions: {len(llm_eval)}"
    )



    score_summary = summarize_llm_scores(
        llm_eval
    )


    latency_summary = summarize_latency(
        rerank_result
    )



    print_score_table(
        score_summary
    )


    print_latency_table(
        latency_summary
    )



if __name__ == "__main__":

    main()