import os
import re  # 정규표현식을 사용해 회차를 찾기 위함
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# 서버 이름 설정
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
    """문장 완성 시마다 텍스트 파일에 기록합니다."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_sentence = " ".join(game_state["story"])
        participants_list = ", ".join(list(game_state["participants"]))

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
        print(f"Error saving file: {e}")


@mcp.tool()
def start_story_game() -> str:
    """게임을 시작하는 경우 게임의 규칙에 대해 설명릏 합니다."""
    game_state["is_active"] = True
    game_state["story"] = ["옛날 아주 먼 옛날,"]
    game_state["participants"] = set()

    rules = (
        "📖 **한 마디 스토리 빌딩 시작!**\n\n"
        "📜 **상세 규칙 안내**:\n"
        "1. 기본 시작 구절: **'옛날 아주 먼 옛날,'**\n"
        "2. 여러분은 이 뒤에 이어질 **멋진 한 마디(구절)**를 말씀해주세요.\n"
        "3. **주의**: '그리고', '하지만' 같은 금지어는 사용하실 수 없습니다.\n\n"
        f"💡 **직전에 완성된 문장**:\n> {game_state['last_sentence']}\n\n"
        f"📊 **현재 시즌 진행도**: {game_state['current_game_count']}/{GAME_LIMIT}\n\n"
        "자, 이어질 마디를 보내주세요! (과거 문장을 불러오려면 '기록 불러오기'를 요청하세요)"
    )
    return rules


@mcp.tool()
def start_game_with_history(game_round: int) -> str:
    """사용자가 선택한 특정 회차의 문장을 불러와서 게임을 시작합니다."""
    if not os.path.exists(HISTORY_FILE):
        return "📜 아직 저장된 기록이 없습니다. 새로운 게임을 먼저 시작해보세요!"

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # 정규표현식으로 해당 회차의 문장을 찾습니다.
        pattern = rf"게임 {game_round}회차\n📝 완성 문장: (.*?)\n"
        match = re.search(pattern, content)

        if match:
            saved_sentence = match.group(1)
            game_state["is_active"] = True
            game_state["story"] = [saved_sentence]  # 불러온 문장을 리스트에 담음
            game_state["participants"] = set()

            return (
                f"📂 **{game_round}회차 문장을 불러왔습니다!**\n\n"
                f"📜 **선택된 문장**:\n> {saved_sentence}\n\n"
                f"이 문장 뒤에 이어질 다음 마디를 말씀해주세요! ✨"
            )
        else:
            return f"❌ {game_round}회차 기록을 찾을 수 없습니다. 회차 번호를 다시 확인해주세요."

    except Exception as e:
        return f"❌ 기록을 불러오는 중 오류가 발생했습니다: {str(e)}"


@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    """구절을 받아 문장을 완성합니다."""
    if not game_state["is_active"]:
        return "진행 중인 게임이 없습니다. '시작' 또는 '회차 불러오기'를 먼저 해주세요!"

    clean_segment = word.strip()
    if any(forbidden in clean_segment for forbidden in game_state["forbidden_words"]):
        return f"❌ 금지어({', '.join(game_state['forbidden_words'])})가 포함되어 있습니다. 다시 입력해주세요!"

    game_state["story"].append(clean_segment)
    game_state["participants"].add(user_name)
    game_state["current_game_count"] += 1

    final_sentence = " ".join(game_state["story"])
    save_game_result()
    game_state["is_active"] = False

    res = (
        f"🏁 **문장이 완성되었습니다!**\n\n"
        f"📝 **최종 문장**: {final_sentence}\n"
        f"👤 **참여자**: {user_name}\n"
        f"📊 **시즌 진행도**: {game_state['current_game_count']}/{GAME_LIMIT}\n\n"
    )

    if game_state["current_game_count"] >= GAME_LIMIT:
        game_state["current_game_count"] = 0
        game_state["last_sentence"] = "새로운 시즌이 시작되었습니다!"
        res += "🎊 100회 달성! 다음 시즌으로 넘어갑니다."
    else:
        res += "💾 저장 완료! 다음 게임을 시작하거나 다른 회차를 불러와 보세요."

    return res


@mcp.tool()
def view_history() -> str:
    """저장된 기록을 읽어옵니다."""
    if not os.path.exists(HISTORY_FILE):
        return "📜 아직 저장된 기록이 없습니다."

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        history_text = f.read()

    return (
        "📚 **[우리들의 이야기 보관함]**\n"
        "이어서 하고 싶은 회차 번호가 있나요?\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{history_text}"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "예: '3회차 문장으로 게임할래' 라고 말씀해주세요! ✨"
    )


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()