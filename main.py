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

    # 'a' (append) 모드는 파일이 없으면 생성하고, 있으면 끝에 내용을 덧붙입니다.
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


@mcp.tool()
def get_game_info() -> str:
    """게임의 규칙과 참여 방법을 상세히 설명합니다."""
    return (
        "📖 **한 단어 스토리 빌딩 가이드**\n\n"
        "1. 참가자들이 돌아가며 **단어 하나씩** 말해 문장을 만듭니다.\n"
        "2. 같은 사람이 **연속으로 단어를 던질 수 없습니다.**\n"
        "3. 지정된 **금지어**를 피해서 문맥을 이어가세요.\n"
        "4. 참여 방법: `이름: 단어` 형식으로 입력하세요.\n\n"
        "준비되셨다면 '게임 시작'을 외쳐주세요!"
    )


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
    return f"🚀 게임 시작!\n\n{get_current_board()}"


@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    """단어를 추가하고, 목표 도달 시 파일에 저장합니다."""
    if not game_state["is_active"]:
        return "게임이 활성화되어 있지 않습니다."

    if user_name == game_state["last_player"]:
        return f"🚫 **{user_name}**님은 방금 입력하셨습니다! 순서를 기다려주세요."

    clean_word = word.strip().split()[0]
    if clean_word in game_state["forbidden_words"]:
        return f"❌ 금지어 **'{clean_word}'**는 사용할 수 없습니다!"

    game_state["story"].append(clean_word)
    game_state["last_player"] = user_name
    game_state["participants"].add(user_name)

    # 목표치 도달 시
    if len(game_state["story"]) >= game_state["word_limit"]:
        save_game_result()  # 파일 저장 실행
        game_state["is_active"] = False
        final_board = get_current_board()
        return f"{final_board}\n✅ 목표 단어 달성! 결과가 `{HISTORY_FILE}`에 저장되었습니다."

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