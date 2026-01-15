import json
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
def get_game_info() -> str:
    """게임의 규칙과 참여 방법을 상세히 설명합니다."""
    guide = (
        "📖 **한 단어 스토리 빌딩 게임 가이드**\n\n"
        "1. **방식**: 참가자들이 돌아가며 **단어 하나씩**만 말해 하나의 문장을 만듭니다.\n"
        "2. **규칙**: 문법이 조금 깨져도 멈추지 않고 이어가는 것이 포인트!\n"
        "3. **제한**: 지정된 '금지어'는 사용할 수 없으며, 같은 사람이 연속으로 단어를 던질 수 없습니다.\n"
        "4. **참여 방법**: `이름: 단어` 형식으로 메시지를 남기면 AI가 기록합니다.\n"
        "   *(예: [철수] 옛날, [영희] 호랑이가, [철수] 담배를...)*\n\n"
        "아이디어 워밍업이나 팀 빌딩에 아주 효과적이에요! 시작하려면 '게임 시작하자'라고 말해보세요."
    )
    return guide


@mcp.tool()
def get_current_board() -> str:
    """현재까지 만들어진 문장과 게임 진행 상황을 시각화하여 보여줍니다."""
    if not game_state["is_active"] and not game_state["story"]:
        return "현재 진행 중인 게임이 없습니다. `start_game`으로 시작해보세요!"

    story_text = " ".join(game_state["story"]) if game_state["story"] else "(아직 시작 전)"
    progress_bar = "▓" * len(game_state["story"]) + "░" * (game_state["word_limit"] - len(game_state["story"]))

    status = "🎮 **STORY BUILDING BOARD**\n"
    status += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    status += f"📍 **주제**: {game_state['topic']}\n"
    status += f"📝 **문장**: {story_text}\n"
    status += f"📊 **진행**: {progress_bar} ({len(game_state['story'])}/{game_state['word_limit']})\n"
    status += f"🚫 **금지**: {', '.join(game_state['forbidden_words'])}\n"
    status += f"👤 **마지막 발화자**: {game_state['last_player'] if game_state['last_player'] else '없음'}\n"
    status += f"━━━━━━━━━━━━━━━━━━━━━━\n"

    if game_state["is_active"]:
        status += "👉 다음 단어를 던져주세요!"
    else:
        status += "🏁 게임이 종료되었습니다."

    return status


@mcp.tool()
def analyze_and_trigger_game(chat_logs: str) -> str:
    """로그 분석 후 게임을 제안하거나 가이드를 출력합니다."""
    trigger_keywords = ["게임", "스토리 빌딩", "워밍업", "단어 잇기", "심심해"]

    if any(kw in chat_logs for kw in trigger_keywords):
        # 단순히 게임 요청이 오면 가이드를 먼저 보여주도록 AI에게 지시
        return "ACTION: 'get_game_info'를 호출하여 게임을 설명하고, 주제를 제안받아 'start_game'을 진행하세요."

    return "NO_TRIGGER"


@mcp.tool()
def start_game(topic: str = "자유 주제", limit: int = 15, forbidden: str = "그리고,하지만") -> str:
    """게임을 공식적으로 시작하고 현황판을 출력합니다."""
    game_state.update({
        "is_active": True,
        "story": [],
        "last_player": None,
        "word_limit": limit,
        "forbidden_words": [w.strip() for w in forbidden.split(",")],
        "participants": set(),
        "topic": topic
    })

    return f"🚀 게임이 생성되었습니다!\n\n{get_current_board()}"


@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    """단어를 추가하고 즉시 업데이트된 현황판을 보여줍니다."""
    if not game_state["is_active"]:
        return "게임이 활성화되어 있지 않습니다."

    if user_name == game_state["last_player"]:
        return f"🚫 **{user_name}**님은 방금 입력하셨습니다! 다른 분의 순서를 기다려주세요."

    clean_word = word.strip().split()[0]
    if clean_word in game_state["forbidden_words"]:
        return f"❌ 금지어 **'{clean_word}'**는 사용할 수 없습니다! 다른 단어를 생각해보세요."

    game_state["story"].append(clean_word)
    game_state["last_player"] = user_name
    game_state["participants"].add(user_name)

    # 단어를 추가할 때마다 보드를 새로 보여줌
    return get_current_board()


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()