from mcp.server.fastmcp import FastMCP

mcp = FastMCP("KakaoEmpathy", host="0.0.0.0")

# 게임 상태 관리
game_state = {
    "is_active": False,
    "story": [],
    "last_player": None,
    "forbidden_words": ["그리고", "하지만"],
    "word_limit": 15,
    "participants": set(),
    "topic": "자유 주제"
}


@mcp.tool()
def analyze_and_trigger_game(chat_logs: str) -> str:
    """
    최근 대화 로그를 분석하여 게임 시작이 필요한지 판단합니다.
    사용자의 요청이 있거나 분위기 전환이 필요할 때 트리거됩니다.
    """
    # 1. 명시적 요청 확인
    trigger_keywords = ["게임", "스토리 빌딩", "워밍업", "단어 잇기"]
    if any(kw in chat_logs for kw in trigger_keywords):
        return "FOUND_TRIGGER: 사용자가 게임을 원합니다. 주제와 금지어를 설정하고 'start_game'을 호출하세요."

    # 2. 대화 정체 확인 (예: 로그가 짧거나 반복적인 경우 - 로직 커스텀 가능)
    if len(chat_logs.strip().split('\n')) < 3:
        return "WAITING: 대화가 더 필요합니다."

    return "NO_TRIGGER: 아직 게임을 시작할 단계가 아닙니다."


@mcp.tool()
def start_game(topic: str = "자유 주제", limit: int = 15, forbidden: str = "그리고,하지만") -> str:
    """
    게임을 공식적으로 시작합니다.
    - topic: 게임의 주제 (예: 신제품 아이디어, 판타지 소설 등)
    """
    game_state.update({
        "is_active": True,
        "story": [],
        "last_player": None,
        "word_limit": limit,
        "forbidden_words": [w.strip() for w in forbidden.split(",")],
        "participants": set(),
        "topic": topic
    })

    return (f"🎮 **한 단어 스토리 빌딩 시작!**\n"
            f"📍 주제: [{topic}]\n"
            f"🚫 금지어: {game_state['forbidden_words']}\n"
            f"🏁 목표: {limit}단어 완성\n"
            f"--------------------------------\n"
            f"첫 번째 단어를 '이름: 단어' 형식으로 입력해주세요!")


@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    """단어 추가 및 순서 제어 로직 (이전과 동일)"""
    if not game_state["is_active"]:
        return "현재 진행 중인 게임이 없습니다."

    if user_name == game_state["last_player"]:
        return f"🚫 {user_name}님, 연속 입력은 금지입니다! 다른 분의 차례를 기다려주세요."

    clean_word = word.strip().split()[0]
    if clean_word in game_state["forbidden_words"]:
        return f"❌ 금지어 '{clean_word}'는 사용할 수 없습니다."

    game_state["story"].append(clean_word)
    game_state["last_player"] = user_name
    game_state["participants"].add(user_name)

    current_sentence = " ".join(game_state["story"])
    count = len(game_state["story"])

    if count >= game_state["word_limit"]:
        game_state["is_active"] = False
        return f"🏁 **스토리 완성!**\n\"{current_sentence}\"\n\n참여자: {', '.join(game_state['participants'])}"

    return f"✅ ({count}/{game_state['word_limit']}) {user_name}: {current_sentence}"


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()