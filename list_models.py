import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY가 없습니다. .env를 확인하세요.")


client = genai.Client(
    api_key=api_key
)


print("=" * 80)
print("현재 API 키에서 조회 가능한 Gemini 모델 목록")
print("=" * 80)

try:
    models = client.models.list()

    found = False

    for model in models:
        name = getattr(model, "name", "")
        display_name = getattr(model, "display_name", "")
        supported_actions = getattr(model, "supported_actions", None)
        supported_generation_methods = getattr(
            model,
            "supported_generation_methods",
            None,
        )

        text = (
            f"{name} "
            f"{display_name} "
            f"{supported_actions} "
            f"{supported_generation_methods}"
        )

        if "generateContent" in text or "generate_content" in text:
            found = True

            print()
            print("-" * 80)
            print(f"name: {name}")
            print(f"display_name: {display_name}")
            print(f"supported_actions: {supported_actions}")
            print(f"supported_generation_methods: {supported_generation_methods}")

    if not found:
        print()
        print("generateContent 지원 모델을 필터링해서 찾지 못했습니다.")
        print("전체 모델을 그대로 출력합니다.")
        print()

        models = client.models.list()

        for model in models:
            print(model)

except Exception as error:
    print()
    print("모델 목록 조회 실패")
    print(f"오류 내용: {error}")
