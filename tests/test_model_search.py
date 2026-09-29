# import time

# from google import genai
# from google.genai import types

# from app.config import settings


# TEST_MODELS = [
#     "gemini-3.6-flash",
#     "gemini-3.5-flash",
#     "gemini-3.5-flash-lite",
#     "gemini-3.1-flash-lite",
#     "gemini-2.5-flash",
#     "gemini-2.5-flash-lite",
# ]


# QUERY = """
# Khái niệm dữ liệu cá nhân theo pháp luật Việt Nam
# """


# def main():

#     client = genai.Client(
#         api_key=settings.google_api_key,
#     )

#     print("=" * 100)
#     print("GOOGLE SEARCH TOOL TEST")
#     print("=" * 100)

#     for model_name in TEST_MODELS:

#         print(f"\nTesting: {model_name}")

#         start = time.time()

#         try:

#             response = client.models.generate_content(
#                 model=model_name,
#                 contents=QUERY,
#                 config=types.GenerateContentConfig(
#                     tools=[
#                         types.Tool(
#                             google_search=types.GoogleSearch(),
#                         )
#                     ]
#                 ),
#             )

#             elapsed = time.time() - start

#             print(f"Status      : SUCCESS")
#             print(f"Time        : {elapsed:.2f}s")

#             answer = response.text or ""

#             print(f"Answer Size : {len(answer)} chars")

#             metadata = getattr(
#                 response.candidates[0],
#                 "grounding_metadata",
#                 None,
#             )

#             if metadata is None:

#                 print("Grounding   : NONE")

#             else:

#                 chunks = getattr(
#                     metadata,
#                     "grounding_chunks",
#                     [],
#                 )

#                 print(
#                     f"Grounding   : {len(chunks)} citation(s)"
#                 )

#                 for idx, chunk in enumerate(chunks, start=1):

#                     web = getattr(chunk, "web", None)

#                     if web is None:
#                         continue

#                     print(
#                         f"  [{idx}] {web.title}"
#                     )

#                     print(
#                         f"      {web.uri}"
#                     )

#         except Exception as e:

#             elapsed = time.time() - start

#             print("Status      : FAILED")
#             print(f"Time        : {elapsed:.2f}s")
#             print(type(e).__name__)
#             print(e)

#         print("-" * 100)


# if __name__ == "__main__":
#     main()

from google import genai

from app.config import settings

client = genai.Client(
    api_key=settings.google_api_key,
)

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Xin chào"
)

print(response.text)