import json

RESULT_PATH = (
    r"D:\legal-technology-agentic-rag\benchmark\results\chunking_results.json"
)

SUMMARY_PATH = (
    r"D:\legal-technology-agentic-rag\benchmark\results\chunking_summary.json"
)


def mean(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def improvement(old, new):
    if old == 0:
        return 0.0
    return (new - old) / old * 100


def main():

    with open(
        RESULT_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        results = json.load(f)

    total = len(results)

    fixed_precision = [
        x["fixed"]["context_precision"]
        for x in results
    ]

    fixed_recall = [
        x["fixed"]["context_recall"]
        for x in results
    ]

    metadata_precision = [
        x["metadata"]["context_precision"]
        for x in results
    ]

    metadata_recall = [
        x["metadata"]["context_recall"]
        for x in results
    ]

    summary = {

        "questions": total,

        "fixed": {

            "context_precision":
                mean(fixed_precision),

            "context_recall":
                mean(fixed_recall),

        },

        "metadata": {

            "context_precision":
                mean(metadata_precision),

            "context_recall":
                mean(metadata_recall),

        },

        "improvement": {

            "context_precision_%":

                improvement(
                    mean(fixed_precision),
                    mean(metadata_precision),
                ),

            "context_recall_%":

                improvement(
                    mean(fixed_recall),
                    mean(metadata_recall),
                ),

        }

    }

    with open(
        SUMMARY_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            summary,
            f,
            indent=4,
            ensure_ascii=False,
        )

    print()
    print("=" * 72)
    print("CHUNKING BENCHMARK SUMMARY")
    print("=" * 72)

    print(f"Total Questions: {total}")

    print()

    print(
        f"{'Method':<15}"
        f"{'Precision':>15}"
        f"{'Recall':>15}"
    )

    print("-" * 45)

    print(
        f"{'Fixed':<15}"
        f"{summary['fixed']['context_precision']:>15.4f}"
        f"{summary['fixed']['context_recall']:>15.4f}"
    )

    print(
        f"{'Metadata':<15}"
        f"{summary['metadata']['context_precision']:>15.4f}"
        f"{summary['metadata']['context_recall']:>15.4f}"
    )

    print("-" * 45)

    print(
        f"{'Improvement':<15}"
        f"{summary['improvement']['context_precision_%']:>14.2f}%"
        f"{summary['improvement']['context_recall_%']:>14.2f}%"
    )

    print("=" * 72)

    print(f"\nSaved summary -> {SUMMARY_PATH}")


if __name__ == "__main__":
    main()