import json
import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# FastMCP 초기화
mcp = FastMCP("KakaoEmpathy", host="0.0.0.0")

# 저장 파일 이름 설정
HISTORY_FILE = "game_history.txt"

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


def save_game_result():
    """게임 결과를 텍스트 파일에 추가 기록합니다."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_sentence = " ".join(game_state["story"])
    participants_list = ", ".join(list(game_state["participants"]))

    entry = (
        f"📅 기록 일시: {timestamp}\n"
        f"📍 게임 주제: {game_state['topic']}\n"
        f"📝 완성 문장: {final_sentence}\n"
        f"👥 참여 인원: {participants_list}\n"
        f"{'━' * 30}\n"
    )

    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


@mcp.tool()
def get_game_info() -> str:
    """게임의 규칙과 참여 방법을 상세히 설명합니다."""
    return (
        "📖 **한 마디 스토리 빌딩 가이드**\n\n"
        "1. 참가자들이 돌아가며 문장의 **한 마디(어절이나 짧은 구)**씩 이어가며 문장을 만듭니다.\n"
        "   *(예: '옛날' 보다는 '옛날 아주 먼' 처럼 의미가 통하는 마디 단위가 좋아요!)*\n"
        "2. 같은 사람이 **연속으로 마디를 던질 수 없습니다.**\n"
        "3. 지정된 **금지어**를 피해서 자연스러운 문맥을 만들어 보세요.\n"
        "4. 참여 방법: `이름: 문장 마디` 형식으로 입력하세요.\n\n"
        "설명을 다 읽으셨다면, **어떤 주제로 게임을 시작할까요?** (예: 판타지, 신제품 기획 등)"
    )


@mcp.tool()
def analyze_and_trigger_game(chat_logs: str) -> str:
    """
    사용자의 게임 의사를 파악하여 먼저 가이드를 출력하도록 유도합니다.
    """
    trigger_keywords = ["게임", "스토리 빌딩", "워밍업", "단어 잇기", "심심해"]

    if any(kw in chat_logs for kw in trigger_keywords):
        # AI에게 먼저 가이드를 보여주라고 명시적인 지침을 전달
        return "TRIGGER_DETECTED: 사용자가 게임에 관심을 보였습니다. 먼저 'get_game_info'를 호출하여 규칙을 설명하고, 사용자에게 원하는 주제가 있는지 물어보세요."

    return "NO_TRIGGER"


@mcp.tool()
def get_current_board() -> str:
    """현재까지 만들어진 문장과 진행 상황을 보여줍니다."""
    if not game_state["is_active"] and not game_state["story"]:
        return "진행 중인 게임이 없습니다."

    story_text = " ".join(game_state["story"]) if game_state["story"] else "(시작 대기 중)"
    count = len(game_state["story"])
    limit = game_state["word_limit"]
    progress = "▓" * count + "░" * (limit - count)

    status = (
        f"🎮 **STORY BUILDING BOARD**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 주제: {game_state['topic']}\n"
        f"📝 문장: {story_text}\n"
        f"📊 진행: {progress} ({count}/{limit})\n"
        f"👤 마지막: {game_state['last_player'] if game_state['last_player'] else '-'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    return status


@mcp.tool()
def start_game(topic: str = "자유 주제", limit: int = 15, forbidden: str = "그리고,하지만") -> str:
    """게임을 초기화하고 시작합니다."""
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
    """문장 마디를 추가하고 현황판을 업데이트합니다."""
    if not game_state["is_active"]:
        return "게임이 활성화되어 있지 않습니다. 'start_game'으로 시작해주세요."

    if user_name == game_state["last_player"]:
        return f"🚫 **{user_name}**님은 방금 입력하셨습니다! 순서를 기다려주세요."

    # '단어'가 아닌 '마디'를 위해 최대 3어절까지 허용하도록 유연하게 처리
    clean_segment = " ".join(word.strip().split()[:3])

    if any(forbidden in clean_segment for forbidden in game_state["forbidden_words"]):
        return f"❌ 마디 안에 금지어({game_state['forbidden_words']})가 포함되어 있습니다!"

    game_state["story"].append(clean_segment)
    game_state["last_player"] = user_name
    game_state["participants"].add(user_name)

    if len(game_state["story"]) >= game_state["word_limit"]:
        save_game_result()
        game_state["is_active"] = False
        final_board = get_current_board()
        return f"{final_board}\n✅ 목표 마디 달성! 결과가 `{HISTORY_FILE}`에 저장되었습니다."

    return get_current_board()


@mcp.tool()
def view_history() -> str:
    """저장된 텍스트 파일의 내용을 읽어옵니다."""
    if not os.path.exists(HISTORY_FILE):
        return "아직 저장된 기록이 없습니다."
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return f.read()


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()