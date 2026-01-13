import json
import re
from mcp.server.fastmcp import FastMCP
import parrot_data


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
        my_name: str
) -> str:
    """
    사용자의 실제 말투를 분석하여 답장 후보를 생성합니다.
    - chat_logs: 카카오톡 대화 내용
    - target_person: 답장을 보낼 상대방 이름
    - user_intent: 답장에 담고 싶은 의도
    - my_name: 로그 속 본인의 이름 (필수)
    """
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

    # 상대방과의 직접 대화가 적을 경우 전체 로그에서 추출
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
너는 '{my_name}'의 카톡 대리인이야. 
사용자의 실제 대화 습관을 분석하여 가장 자연스러운 답장을 생성해.

**분석된 스타일 카테고리:** [{detected_cat or "일반"}]

**[말투 DNA 가이드라인 (참조용)]**
{optimized_guide}

**'{my_name}'의 실제 말투 샘플 (최우선 복제):**
{chr(10).join(my_style)}

**나의 의도:** "{user_intent}"
**상대방의 마지막 말:** "{last_msg}"

**지시:**
1. 샘플 우선 반영: 종결어미, 문장 부호 습관을 100% 복제할 것.
2. 결과 형식: 답장 후보 5개를 제안할 것.
"""

def main():
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()