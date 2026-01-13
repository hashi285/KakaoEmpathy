import json
import re
from mcp.server.fastmcp import FastMCP
from mangum import Mangum
import parrot_data

# 1. FastMCP 초기화
mcp = FastMCP("KakaoEmpathy")

@mcp.resource("parrot://style_guide")
def get_style_guide() -> str:
    """전체 데이터셋을 조회합니다."""
    return json.dumps(parrot_data.PARROT_STYLES, ensure_ascii=False, indent=2)

@mcp.tool()
def identify_participants(chat_logs: str) -> str:
    """카톡 로그에서 참여자를 추출합니다."""
    pattern = r"\[(.*?)\]"
    participants = list(set(re.findall(pattern, chat_logs)))
    if not participants:
        return "참여자를 찾을 수 없습니다. 카톡 형식을 확인해주세요."
    return f"대화에서 다음 인물들이 발견되었습니다: [{', '.join(participants)}]. 이 중 본인의 이름은 무엇인가요?"

@mcp.tool()
def generate_reply_for_me(
        chat_logs: str,
        target_person: str,
        user_intent: str,
        my_name: str,
        relationship: str = "자동 분석"
) -> str:
    """사용자의 실제 말투를 분석하여 답장 후보를 생성합니다."""
    if not my_name:
        return "본인의 이름(my_name)을 입력해야 말투 분석이 가능합니다."

    # --- 1. 데이터 파싱 ---
    parsed_data = []
    pattern = r"\[(.*?)\] \[(.*?)\] (.*)"
    for line in chat_logs.strip().split('\n'):
        match = re.match(pattern, line)
        if match:
            sender, _, message = match.groups()
            parsed_data.append({"sender": sender, "message": message})

    # --- 2. 내 말투 샘플 추출 ---
    relevant_chat = [d for d in parsed_data if d['sender'] in [my_name, target_person]]
    my_style = [d['message'] for d in relevant_chat if d['sender'] == my_name][-20:]

    if not my_style:
        my_style = [d['message'] for d in parsed_data if d['sender'] == my_name][-20:]

    if not my_style:
        return f"로그에서 '{my_name}'님의 메시지를 찾을 수 없습니다. 이름을 확인해주세요."

    # --- 3. 자동 카테고리 판단 및 가이드 생성 ---
    detected_cat = parrot_data.auto_select_category(my_style)
    optimized_guide = parrot_data.get_optimized_dataset_text(detected_cat)

    # --- 4. 상대방의 마지막 메시지 확인 ---
    last_msg = "없음"
    for d in reversed(relevant_chat):
        if d['sender'] == target_person:
            last_msg = d['message']
            break

    # --- 5. 최종 프롬프트 구성 ---
    return f"""
당신은 '{my_name}'의 카톡 대리인입니다.
제공된 데이터와 관계를 바탕으로 가장 자연스러운 답장을 생성하세요.

<Context>
- 사용자 이름: {my_name}
- 상대방 이름: {target_person}
- 관계 설정: {relationship}
- 분석된 스타일 카테고리: {detected_cat or "일반"}
- 상대방의 마지막 말: "{last_msg}"
- 나의 답변 의도: "{user_intent}"
</Context>

<Guidelines_DNA>
{optimized_guide}
</Guidelines_DNA>

<Personal_Style_Samples>
{chr(10).join(my_style)}
</Personal_Style_Samples>

<Instructions>
1. 말투 복제: 샘플의 종결어미, 문장 부호 습관을 그대로 따르세요.
2. 결과 형식: [분석 리포트]와 [답장 후보] 5개를 출력하세요.
</Instructions>
"""

# ---------------------------------------------------------
# 2. AWS Lambda 배포용 핵심 설정
# lifespan="off"는 람다에서 발생하는 초기화 에러를 방지합니다.
# ---------------------------------------------------------
handler = Mangum(mcp, lifespan="off")

# 3. 로컬 테스트용 실행부
if __name__ == "__main__":
    import uvicorn
    # 로컬에서는 uvicorn을 통해 handler를 실행합니다.
    # 실행 명령어: python main.py
    uvicorn.run("main:handler", host="127.0.0.1", port=8000, reload=True)