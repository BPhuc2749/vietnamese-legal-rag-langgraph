from google import genai

from app.config import settings


def main():

    client = genai.Client(
        api_key=settings.google_api_key,
    )

    print("=" * 80)
    print("AVAILABLE MODELS")
    print("=" * 80)

    models = client.models.list()

    for model in models:

        name = getattr(model, "name", "")

        # chỉ hiện Gemini
        if "gemini" not in name.lower():
            continue

        print(name)


if __name__ == "__main__":
    main()