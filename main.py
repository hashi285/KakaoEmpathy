import os
import re
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# 서버 이름 설정
mcp = FastMCP("KakaoEmpathy", host="0.0.0.0")

HISTORY_FILE = "game_history.txt"
GAME_LIMIT = 100

# 게임 상태 관리
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
    """게임 참여 방식을 선택할 수 있는 메뉴를 출력합니다."""
    welcome_message = (
        "🎮 **스토리 빌딩 게임에 오신 것을 환영합니다!**\n\n"
        "어떤 방식으로 참여하시겠어요? 원하시는 번호나 내용을 말씀해주세요.\n\n"
        "1️⃣ **새로운 이야기 시작**\n"
        "   - '옛날 아주 먼 옛날,' 구절부터 새롭게 시작합니다.\n\n"
        "2️⃣ **직전 문장 이어서 하기**\n"
        f"   - 최근 완성된 [ {game_state['last_sentence']} ] 뒤에 내용을 잇습니다.\n\n"
        "3️⃣ **과거 기록 선택해서 잇기**\n"
        "   - '기록 보여줘'라고 입력해 회차 번호를 확인하고 선택하세요!\n\n"
        f"📊 **시즌 진행도**: {game_state['current_game_count']}/{GAME_LIMIT}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 **규칙**: 한 마디 구절을 입력하면 문장이 완성되며, 금지어(그리고, 하지만)는 피해주세요!"
    )
    return welcome_message


@mcp.tool()
def start_new_story() -> str:
    """[선택 1] 새로운 게임을 '옛날 아주 먼 옛날,' 구절로 시작합니다."""
    game_state["is_active"] = True
    game_state["story"] = ["옛날 아주 먼 옛날,"]
    game_state["participants"] = set()
    return "🚀 **새로운 이야기가 시작되었습니다!**\n\n문구: '옛날 아주 먼 옛날,'\n이 뒤에 이어질 마디를 알려주세요!"


@mcp.tool()
def start_continue_last() -> str:
    """[선택 2] 가장 최근에 완성된 문장을 불러와 즉시 시작합니다."""
    if game_state["last_sentence"] == "아직 완성된 문장이 없습니다.":
        return "❌ 이어갈 기록이 없습니다. '1번 새로운 이야기'를 선택해 주세요!"

    game_state["is_active"] = True
    game_state["story"] = [game_state["last_sentence"]]
    game_state["participants"] = set()

    return (
        "🔄 **최근 문장을 불러왔습니다!**\n\n"
        f"현재 문장: **'{game_state['last_sentence']}'**\n"
        "이 뒤에 내용을 이어서 문장을 완성해주세요! ✨"
    )


@mcp.tool()
def start_game_with_history(game_round: int) -> str:
    """[선택 3] 사용자가 선택한 특정 회차의 문장을 불러와 게임을 시작합니다."""
    if not os.path.exists(HISTORY_FILE):
        return "📜 아직 저장된 기록이 없습니다."

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = rf"게임 {game_round}회차\n📝 완성 문장: (.*?)\n"
        match = re.search(pattern, content)

        if match:
            saved_sentence = match.group(1)
            game_state["is_active"] = True
            game_state["story"] = [saved_sentence]
            game_state["participants"] = set()

            return (
                f"📂 **{game_round}회차 문장을 불러왔습니다!**\n\n"
                f"📜 **선택된 문장**:\n> {saved_sentence}\n\n"
                f"이 문장 뒤에 이어질 다음 마디를 말씀해주세요!"
            )
        else:
            return f"❌ {game_round}회차 기록을 찾을 수 없습니다."
    except Exception as e:
        return f"❌ 오류 발생: {str(e)}"


@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    """사용자의 구절을 더해 문장을 완성하고 시즌 진행도를 체크합니다."""
    if not game_state["is_active"]:
        return "진행 중인 게임이 없습니다. 먼저 참여 방식을 선택해 주세요!"

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
        f"📊 **시즌 진행도**: {game_state['current_game_count']}/{GAME_LIMIT}\n"
    )

    if game_state["current_game_count"] >= GAME_LIMIT:
        game_state["current_game_count"] = 0
        game_state["last_sentence"] = "새로운 시즌이 시작되었습니다!"
        res += "\n🎊 100회 달성! 이번 시즌이 종료되었습니다. 다시 시작해 보세요!"
    else:
        res += "\n💾 저장 완료! 다음 게임을 시작하거나 다른 회차를 불러와 보세요."

    return res


@mcp.tool()
def view_history() -> str:
    """과거 기록을 카카오톡 가독성에 맞춰 출력합니다."""
    if not os.path.exists(HISTORY_FILE):
        return "📜 아직 저장된 기록이 없습니다."

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history_text = f.read()

        return (
            "📚 **[우리들의 이야기 보관함]**\n"
            "이어서 하고 싶은 회차 번호가 있나요?\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{history_text}"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "예: '3회차 문장으로 할래' 라고 요청해 주세요! ✨"
        )
    except Exception as e:
        return f"❌ 기록 불러오기 실패: {str(e)}"


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()