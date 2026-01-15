import json
import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("KakaoEmpathy", host="0.0.0.0")

# 파일 저장 경로 설정
HISTORY_FILE = "game_history.txt"

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
    """게임 결과를 텍스트 파일에 저장합니다."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_sentence = " ".join(game_state["story"])
    participants_list = ", ".join(game_state["participants"])

    entry = (
        f"📅 일시: {timestamp}\n"
        f"📍 주제: {game_state['topic']}\n"
        f"📝 문장: {final_sentence}\n"
        f"👥 참여: {participants_list}\n"
        f"{'=' * 30}\n"
    )

    # 'a' (append) 모드로 열어서 기존 내용 뒤에 추가합니다.
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    """단어를 추가하고, 종료 시 파일에 저장합니다."""
    if not game_state["is_active"]:
        return "진행 중인 게임이 없습니다."

    # (중략: 기존 중복 체크 및 금지어 로직...)

    clean_word = word.strip().split()[0]
    game_state["story"].append(clean_word)
    game_state["last_player"] = user_name
    game_state["participants"].add(user_name)

    # 종료 조건 도달 시 저장 실행
    if len(game_state["story"]) >= game_state["word_limit"]:
        save_game_result()  # 파일 저장 함수 호출
        game_state["is_active"] = False
        res = f"🏁 스토리 완성 및 저장 완료!\n\"{' '.join(game_state['story'])}\""
        return res

    return f"✅ ({len(game_state['story'])}/{game_state['word_limit']}) 추가됨"


@mcp.tool()
def read_history() -> str:
    """저장된 게임 기록을 불러옵니다."""
    if not os.path.exists(HISTORY_FILE):
        return "아직 기록된 게임이 없습니다."

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return f.read()