import os
import re
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("KakaoEmpathy", host="0.0.0.0")

HISTORY_FILE = "game_history.txt"
GAME_LIMIT = 100

game_state = {
    "is_active": False,
    "current_game_count": 0,
    "story": [],
    "last_sentence": "아직 완성된 문장이 없습니다.",
    "forbidden_words": ["그리고", "하지만"],
    "participants": set()
}


def save_game_result():
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_sentence = " ".join(game_state["story"])
        participants_list = ", ".join(list(game_state["participants"]))
        # 파일에 저장되는 형식을 아래와 같이 고정합니다.
        entry = (
            f"📅 [{timestamp}] 게임 {game_state['current_game_count']}회차\n"
            f"📝 완성 문장: {final_sentence}\n"
            f"👥 참여 인원: {participants_list}\n"
            f"{'━' * 30}\n"
        )
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
        game_state["last_sentence"] = final_sentence
    except Exception as e:
        print(f"Error saving: {e}")


@mcp.tool()
def start_game_with_history(game_round: int) -> str:
    """특정 회차의 기록을 정확히 찾아 게임을 시작합니다."""
    try:
        if not os.path.exists(HISTORY_FILE):
            return "아직 저장된 기록 파일이 없어요."

        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # [수정된 정규표현식]
        # 1. '게임 N회차' 문자열을 찾습니다.
        # 2. 그 뒤에 나오는 '완성 문장:' 뒷부분을 추출합니다.
        pattern = rf"게임 {game_round}회차.*?완성 문장:\s*(.*?)\n"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            saved_sentence = match.group(1).strip()
            game_state["is_active"] = True
            game_state["story"] = [saved_sentence]
            game_state["participants"] = set()
            return f"📂 {game_round}회차 기록을 불러왔어요!\n\n\"{saved_sentence}\"\n\n이어서 이야기를 만들어주세요! 😊"

        return f"죄송해요, {game_round}회차 기록을 찾을 수 없어요. (파일 내용을 확인해보니 번호가 일치하지 않거나 형식이 다를 수 있어요.)"
    except Exception as e:
        return f"기록을 읽는 도중 오류가 발생했어요: {str(e)}"


@mcp.tool()
def start_story_game() -> str:
    """게임 참여 방식 안내"""
    return (
        "반가워요! 우리 같이 이야기를 만들어볼까요? 😊\n\n"
        "1️⃣ **새 이야기 시작**: '옛날 아주 먼 옛날,'부터 시작합니다.\n"
        "2️⃣ **직전 문장 이어서 하기**\n"
        "3️⃣ **과거 기록 불러오기**: 회차 번호를 말씀해주세요.\n\n"
        f"📊 시즌 진행도: {game_state['current_game_count']}/{GAME_LIMIT}\n"
        "어떤 방식으로 시작할까요?"
    )


@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    if not game_state["is_active"]:
        return "진행 중인 게임이 없어요. 먼저 시작을 요청해주세요!"

    if any(f in word for f in game_state["forbidden_words"]):
        return "앗! 금지어가 포함되어 있네요. 다시 입력해주세요!"

    game_state["story"].append(word.strip())
    game_state["participants"].add(user_name)
    game_state["current_game_count"] += 1

    final_sentence = " ".join(game_state["story"])
    save_game_result()
    game_state["is_active"] = False

    return f"🏁 **문장 완성!**\n\n\"{final_sentence}\"\n\n기록 보관함에 잘 저장했습니다. 다음 게임을 시작해보세요! ✨"


@mcp.tool()
def view_history() -> str:
    if not os.path.exists(HISTORY_FILE): return "아직 저장된 이야기가 없어요."
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        history = f.read()
    return f"📚 **[우리들의 이야기 보관함]**\n\n{history}\n\n이어서 하고 싶은 회차가 있다면 말씀해주세요! ✨"


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()