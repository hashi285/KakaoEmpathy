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
        # 파일 저장 형식을 고정 (나중에 읽기 편하도록)
        entry = (
            f"📅 [{timestamp}] 게임 {game_state['current_game_count']}회차\n"
            f"📝 문장: {final_sentence}\n"
            f"👥 참여: {participants_list}\n"
            f"{'━' * 20}\n"
        )
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
        game_state["last_sentence"] = final_sentence
    except Exception as e:
        print(f"Error saving: {e}")


@mcp.tool()
def start_story_game() -> str:
    """메인 메뉴 안내"""
    return (
        "반가워요! 우리 같이 이야기를 만들어볼까요? 😊\n\n"
        "1️⃣ **새 이야기 시작**: 처음부터 새로 시작해요.\n"
        "2️⃣ **직전 문장 잇기**: 가장 최근 이야기를 불러와요.\n"
        "3️⃣ **과거 기록 선택**: '기록 보여줘'라고 해서 번호를 골라보세요!\n\n"
        f"💡 최근 문장: \"{game_state['last_sentence']}\"\n"
        "어떤 방식으로 시작할까요?"
    )


@mcp.tool()
def start_game_with_history(game_round: int) -> str:
    """회차 기록을 더 정확하게 찾아 게임을 시작합니다."""
    try:
        if not os.path.exists(HISTORY_FILE):
            return "아직 저장된 기록이 없어요. 새 게임을 먼저 시작해보세요!"

        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # [수정 포인트] 정규표현식을 더 유연하게 변경 (공백이나 특수기호에 유연함)
        # 게임 N회차 이후 문장: 부분을 찾아 그 뒷내용을 추출
        pattern = rf"게임 {game_round}회차.*?📝 문장:\s*(.*?)\n"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            saved_sentence = match.group(1).strip()
            game_state["is_active"] = True
            game_state["story"] = [saved_sentence]
            game_state["participants"] = set()
            return f"📂 {game_round}회차 기록을 성공적으로 가져왔어요!\n\n\"{saved_sentence}\"\n\n이 뒤를 이어서 이야기를 완성해주세요! ✨"

        return f"죄송해요, {game_round}회차 기록은 아직 보관함에 없는 것 같아요. 번호를 다시 확인해주시겠어요?"
    except Exception as e:
        return f"기록을 읽는 도중 오류가 발생했어요: {str(e)}"


@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    """단어를 추가하고 기록"""
    if not game_state["is_active"]:
        return "진행 중인 게임이 없어요. '시작'을 먼저 말해주세요!"

    # 금지어 체크
    if any(f in word for f in game_state["forbidden_words"]):
        return "앗! 금지어가 포함되어 있네요. 다시 입력해주세요!"

    game_state["story"].append(word.strip())
    game_state["participants"].add(user_name)
    game_state["current_game_count"] += 1

    final_sentence = " ".join(game_state["story"])
    save_game_result()
    game_state["is_active"] = False

    return f"🏁 **문장 완성!**\n\n📝 \"{final_sentence}\"\n\n잘 저장되었습니다! 이어서 하거나 새로 시작해보세요. 😊"


@mcp.tool()
def view_history() -> str:
    """기록 보기"""
    if not os.path.exists(HISTORY_FILE): return "아직 저장된 이야기가 없어요."
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        history = f.read()
    return f"📚 **[우리들의 이야기 보관함]**\n\n{history}\n\n이어서 하고 싶은 회차가 있다면 말씀해주세요! ✨"


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()