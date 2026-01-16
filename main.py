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
        print(f"Error: {e}")

@mcp.tool()
def start_story_game() -> str:
    """게임 참여 방식을 안내합니다."""
    return (
        "반가워요! 우리 같이 이야기를 만들어볼까요? 😊\n\n"
        "1️⃣ **새 이야기 시작**: '옛날 아주 먼 옛날,'부터 시작해요.\n"
        "2️⃣ **직전 문장 잇기**: 가장 최근 이야기를 불러옵니다.\n"
        "3️⃣ **과거 기록 선택**: 예전 기록 중 하나를 골라 이어가요.\n\n"
        f"💡 최근 문장: \"{game_state['last_sentence']}\"\n"
        f"📊 시즌 진행도: {game_state['current_game_count']}/{GAME_LIMIT}\n\n"
        "어떤 방식으로 시작할까요? 말씀만 해주세요!"
    )

@mcp.tool()
def start_new_story() -> str:
    """새로운 게임을 시작합니다."""
    game_state["is_active"] = True
    game_state["story"] = ["옛날 아주 먼 옛날,"]
    game_state["participants"] = set()
    return "🚀 새로운 이야기가 시작됐어요! '옛날 아주 먼 옛날,' 뒤에 이어질 한 마디를 던져주세요!"

@mcp.tool()
def start_continue_last() -> str:
    """최근 문장을 불러옵니다."""
    if game_state["last_sentence"] == "아직 완성된 문장이 없습니다.":
        return "아직 이어갈 기록이 없네요. 1번을 선택해서 새 이야기를 시작해보는 건 어떨까요?"
    game_state["is_active"] = True
    game_state["story"] = [game_state["last_sentence"]]
    game_state["participants"] = set()
    return f"🔄 최근 문장인 \"{game_state['last_sentence']}\"를 가져왔어요! 이 뒤를 멋지게 이어주세요. ✨"

@mcp.tool()
def start_game_with_history(game_round: int) -> str:
    """선택한 회차를 불러옵니다."""
    try:
        if not os.path.exists(HISTORY_FILE): return "아직 저장된 기록이 없어요."
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        pattern = rf"게임 {game_round}회차\n📝 문장: (.*?)\n"
        match = re.search(pattern, content)
        if match:
            saved_sentence = match.group(1)
            game_state["is_active"] = True
            game_state["story"] = [saved_sentence]
            game_state["participants"] = set()
            return f"📂 {game_round}회차 문장을 찾았어요!\n\n\"{saved_sentence}\"\n\n이 문장 뒤에 어떤 이야기를 더해볼까요?"
        return f"죄송해요, {game_round}회차 기록은 찾을 수가 없네요. 번호를 다시 확인해주시겠어요?"
    except Exception as e:
        return "기록을 읽어오는 중에 문제가 생겼어요. 잠시 후 다시 시도해주세요."

@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    """구절을 추가하고 문장을 완성합니다."""
    if not game_state["is_active"]:
        return "현재 진행 중인 게임이 없어요. '시작'을 먼저 말해주세요!"
    if any(f in word for f in game_state["forbidden_words"]):
        return "앗! '그리고'나 '하지만'은 금지어예요. 다른 단어를 사용해볼까요?"

    game_state["story"].append(word.strip())
    game_state["participants"].add(user_name)
    game_state["current_game_count"] += 1
    final_sentence = " ".join(game_state["story"])
    save_game_result()
    game_state["is_active"] = False

    res = f"🏁 **문장 완성!**\n\n📝 \"{final_sentence}\"\n\n정말 멋진 문장이네요! {user_name}님이 기록 보관함에 잘 저장해두었답니다. 😊"
    if game_state["current_game_count"] >= GAME_LIMIT:
        game_state["current_game_count"] = 0
        game_state["last_sentence"] = "새 시즌 시작!"
        res += "\n\n🎊 와! 100번째 문장이 채워져서 이번 시즌이 끝났어요. 새로운 시즌을 시작해볼까요?"
    return res

@mcp.tool()
def view_history() -> str:
    """과거 기록을 보여줍니다."""
    if not os.path.exists(HISTORY_FILE): return "아직 완성된 이야기가 없어요. 첫 주인공이 되어보시겠어요?"
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        history = f.read()
    return f"📚 **[우리들의 이야기 보관함]**\n\n{history}\n\n이어서 하고 싶은 회차 번호가 있다면 'N회차로 할래'라고 말해주세요! ✨"

def main():
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()