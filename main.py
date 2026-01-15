import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# 1. MCP 서버 설정
mcp = FastMCP("KakaoEmpathy", host="0.0.0.0")

# 2. 파일 저장 경로 설정
HISTORY_FILE = "game_history.txt"

# 3. 게임 상태 관리 (초기값)
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
    participants_list = ", ".join(list(game_state["participants"]))  # set을 리스트로 변환

    entry = (
        f"📅 일시: {timestamp}\n"
        f"📍 주제: {game_state['topic']}\n"
        f"📝 문장: {final_sentence}\n"
        f"👥 참여: {participants_list}\n"
        f"{'=' * 30}\n"
    )

    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


@mcp.tool()
def start_game(topic: str = "자유 주제", limit: int = 15, forbidden: str = "그리고,하지만") -> str:
    """게임을 새로 시작합니다."""
    game_state.update({
        "is_active": True,
        "story": [],
        "last_player": None,
        "word_limit": limit,
        "forbidden_words": [w.strip() for w in forbidden.split(",")],
        "participants": set(),
        "topic": topic
    })
    return f"🎮 게임 시작! 주제: [{topic}] / 금지어: {game_state['forbidden_words']}"


@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    """단어를 추가하고, 종료 시 파일에 저장합니다."""
    if not game_state["is_active"]:
        return "현재 진행 중인 게임이 없습니다. 'start_game'으로 먼저 시작해주세요."

    if user_name == game_state["last_player"]:
        return f"🚫 {user_name}님, 연속 입력은 안 됩니다!"

    clean_word = word.strip().split()[0]

    if clean_word in game_state["forbidden_words"]:
        return f"❌ 금지어 '{clean_word}'는 사용할 수 없습니다."

    game_state["story"].append(clean_word)
    game_state["last_player"] = user_name
    game_state["participants"].add(user_name)

    # 종료 조건 도달 시 저장 실행
    if len(game_state["story"]) >= game_state["word_limit"]:
        save_game_result()
        game_state["is_active"] = False
        res = f"🏁 스토리 완성 및 저장 완료!\n결과: \"{' '.join(game_state['story'])}\""
        return res

    return f"✅ ({len(game_state['story'])}/{game_state['word_limit']}) {user_name}: {clean_word}"


@mcp.tool()
def read_history() -> str:
    """저장된 게임 기록을 불러옵니다."""
    if not os.path.exists(HISTORY_FILE):
        return "아직 기록된 게임이 없습니다."

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        # 최근 기록 20줄만 보여주기 (파일이 너무 커질 경우 대비)
        return "".join(lines[-20:])


# --- 핵심: 서버 실행부 추가 ---
def main():
    """서버를 실행하고 요청을 대기합니다."""
    print("🚀 KakaoEmpathy MCP 서버를 시작합니다...")
    # transport="streamable-http"가 설정되어야 웹 요청을 받을 수 있습니다.
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()