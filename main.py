import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# 서버 이름 설정
mcp = FastMCP("KakaoEmpathy", host="0.0.0.0")

HISTORY_FILE = "game_history.txt"
GAME_LIMIT = 100  # 총 100회 참여 시 전체 게임 세션 종료

# 게임 상태 관리
game_state = {
    "is_active": False,
    "current_game_count": 0,  # 현재까지 진행된 게임 횟수 (최대 100)
    "story": [],
    "last_sentence": "아직 완성된 문장이 없습니다.",  # 직전에 완성된 문장 저장
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

        # 직전 문장 업데이트
        game_state["last_sentence"] = final_sentence
    except Exception as e:
        print(f"Error saving file: {e}")


@mcp.tool()
def start_story_game() -> str:
    """게임을 시작하며 규칙과 이전 문장을 안내합니다."""
    game_state["is_active"] = True
    game_state["story"] = ["옛날 아주 먼 옛날,"]
    game_state["participants"] = set()

    rules = (
        "📖 **한 마디 스토리 빌딩 시작!**\n\n"
        "📜 **상세 규칙 안내**:\n"
        "1. 제가 먼저 시작 구절을 던집니다: **'옛날 아주 먼 옛날,'**\n"
        "2. 여러분은 이 뒤에 이어질 **멋진 한 마디(구절)**를 말씀해주세요.\n"
        "3. **주의**: '그리고', '하지만' 같은 금지어는 사용하실 수 없습니다.\n"
        "4. 총 100번의 문장이 만들어지면 이번 시즌 게임이 완전히 종료됩니다.\n\n"
        f"💡 **직전에 완성된 문장**:\n> {game_state['last_sentence']}\n\n"
        f"📊 **현재 진행도**: {game_state['current_game_count']}/{GAME_LIMIT}\n\n"
        "자, '옛날 아주 먼 옛날,' 뒤에 이어질 마디를 보내주세요!"
    )
    return rules


@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    """구절을 받아 문장을 완성하고, 100회 달성 여부를 확인합니다."""
    if not game_state["is_active"]:
        return "진행 중인 게임이 없습니다. 'start_story_game'으로 먼저 시작해주세요!"

    clean_segment = word.strip()
    if any(forbidden in clean_segment for forbidden in game_state["forbidden_words"]):
        return f"❌ 금지어({', '.join(game_state['forbidden_words'])})가 포함되어 있습니다. 다시 입력해주세요!"

    # 문장 완성 및 횟수 증가
    game_state["story"].append(clean_segment)
    game_state["participants"].add(user_name)
    game_state["current_game_count"] += 1

    final_sentence = " ".join(game_state["story"])
    save_game_result()

    # 1회성 문장 완성 후 대기 상태로 전환 (다음 사람이 start_story_game을 할 수 있도록)
    game_state["is_active"] = False

    res = (
        f"🏁 **문장이 완성되었습니다!**\n\n"
        f"📝 **최종 문장**: {final_sentence}\n"
        f"👤 **참여자**: {user_name}\n"
        f"📊 **시즌 진행도**: {game_state['current_game_count']}/{GAME_LIMIT}\n\n"
    )

    # 100번 달성 시 전체 초기화 및 공지
    if game_state["current_game_count"] >= GAME_LIMIT:
        game_state["current_game_count"] = 0
        game_state["last_sentence"] = "새로운 시즌이 시작되었습니다!"
        res += "🎊 축하합니다! 100번째 문장이 완성되어 이번 시즌 게임이 종료되었습니다. 다음 게임으로 넘어갑니다!"
    else:
        res += "💾 결과가 기록되었습니다. 다음 게임을 시작하려면 '게임 시작'을 말해주세요!"

    return res


@mcp.tool()
def view_history() -> str:
    """이전 게임들의 문장 기록을 모두 호출하여 보여줍니다."""
    if not os.path.exists(HISTORY_FILE):
        return "아직 저장된 기록이 없습니다."

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        history = f.read()

    return f"📜 **지금까지 완성된 문장 기록입니다**:\n\n{history}"


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()