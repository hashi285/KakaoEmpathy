import json
import re
from mcp.server.fastmcp import FastMCP
# parrot_data 모듈이 같은 경로에 있다고 가정합니다.
import parrot_data

mcp = FastMCP("KakaoEmpathy")

user_identity = {"me": None}


@mcp.resource("parrot://style_guide")
def get_style_guide() -> str:
    return json.dumps(parrot_data.PARROT_STYLES, ensure_ascii=False, indent=2)


@mcp.tool()
def identify_participants(chat_logs: str) -> str:
    # 중복 제거 및 이름만 깔끔하게 추출
    pattern = r"\[(.*?)\]"
    participants = sorted(list(set(re.findall(pattern, chat_logs))))
    if not participants:
        return "참여자를 찾을 수 없습니다. [이름] [시간] 메시지 형식인지 확인해주세요."
    return f"발견된 참여자: {', '.join(participants)}\n이 중 본인의 이름은 무엇인가요? 'set_my_name' 도구로 알려주세요."


@mcp.tool()
def set_my_name(name: str) -> str:
    user_identity["me"] = name
    return f"확인되었습니다. 이제부터 '{name}'님의 말투를 분석하여 답장을 생성합니다."


@mcp.tool()
def generate_reply_for_me(chat_logs: str, target_person: str, user_intent: str) -> str:
    my_name = user_identity.get("me")
    if not my_name:
        return "먼저 'set_my_name' 도구를 사용하여 본인이 누구인지 설정해주세요."

    # 1. 데이터 파싱 (안정성 강화)
    parsed_data = []
    lines = chat_logs.strip().split('\n')
    for line in lines:
        match = re.match(r"^\[(.*?)\]\s*\[(.*?)\]\s*(.*)$", line)
        if match:
            sender, _, message = match.groups()
            parsed_data.append({"sender": sender, "message": message})

    # 2. 내 말투 샘플 추출 (상대방과의 대화 우선, 없으면 전체에서 추출)
    relevant_chat = [d for d in parsed_data if d['sender'] in [my_name, target_person]]
    my_style = [d['message'] for d in relevant_chat if d['sender'] == my_name][-20:]

    if not my_style:
        my_style = [d['message'] for d in parsed_data if d['sender'] == my_name][-20:]

    if not my_style:
        return f"'{my_name}'님의 대화 내역을 찾을 수 없습니다. 이름이 정확한지 확인해주세요."

    # 3. 자동 카테고리 판단
    detected_cat = parrot_data.auto_select_category(my_style)
    optimized_guide = parrot_data.get_optimized_dataset_text(detected_cat)

    # 4. 상대방의 마지막 메시지
    last_msg = next((d['message'] for d in reversed(relevant_chat) if d['sender'] == target_person), "없음")

    # 5. 프롬프트 생성 (LLM에게 전달될 최종 지시문)
    prompt = f"""
당신은 '{my_name}'의 페르소나를 복제한 대화 어시스턴트입니다.
분석된 스타일: {detected_cat}

[말투 DNA 가이드라인]
{optimized_guide}

[실제 말투 샘플]
{chr(10).join(my_style)}

[상황]
- 대상: {target_person}
- 상대의 마지막 말: "{last_msg}"
- 나의 의도: "{user_intent}"

[출력 요구사항]
1. 말투 카테고리 확정 및 이유
2. 대화 분위기 요약 (친밀도, 주도권 등)
3. '나의 의도'를 반영한 답장 후보 5개 (샘플의 종결어미, 초성 사용 습관 엄수)
"""
    return prompt


if __name__ == "__main__":
    mcp.run()