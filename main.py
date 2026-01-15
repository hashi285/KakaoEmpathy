import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# 서버 이름 설정
mcp = FastMCP("KakaoEmpathy", host="0.0.0.0")

HISTORY_FILE = "game_history.txt"

# 게임 상태 관리
game_state = {
    "is_active": False,
    "story": ["옛날 아주 먼 옛날,"],  # 예시 시작 문구 (비워두셔도 됩니다)
    "last_player": None,
    "forbidden_words": ["그리고", "하지만"],
    "participants": set()
}


def save_game_result():
    """게임 결과를 텍스트 파일에 기록합니다."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_sentence = " ".join(game_state["story"])
        participants_list = ", ".join(list(game_state["participants"]))

        entry = (
            f"📅 기록 일시: {timestamp}\n"
            f"📝 완성 문장: {final_sentence}\n"
            f"👥 참여 인원: {participants_list}\n"
            f"{'━' * 30}\n"
        )

        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"Error saving file: {e}")


@mcp.tool()
def start_story_game() -> str:
    """게임을 시작하며 상세 룰을 안내합니다."""
    # 게임 상태 초기화
    game_state["is_active"] = True
    game_state["story"] = ["옛날 아주 먼 옛날,"]  # 시작 구절 설정
    game_state["participants"] = set()
    game_state["last_player"] = None

    rules = (
        "📖 **한 마디 스토리 빌딩 시작!**\n\n"
        "📜 **상세 규칙 안내**:\n"
        "1. 제가 먼저 시작 구절을 던집니다: **'옛날 아주 먼 옛날,'**\n"
        "2. 여러분은 이 뒤에 이어질 **멋진 한 마디(구절)**를 말씀해주세요.\n"
        "3. **주의**: '그리고', '하지만' 같은 금지어는 사용하실 수 없습니다.\n"
        "4. 여러분이 마디를 입력하면 즉시 문장이 완성되며 기록됩니다!\n\n"
        "자, 이 뒤에 어떤 일이 벌어질까요? 마디를 이어주세요!"
    )
    return rules


@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    """사용자의 구절을 더해 문장을 완성하고 게임을 종료합니다."""
    if not game_state["is_active"]:
        return "현재 진행 중인 게임이 없습니다. 'start_story_game'으로 먼저 시작해주세요!"

    # 금지어 확인
    clean_segment = word.strip()
    if any(forbidden in clean_segment for forbidden in game_state["forbidden_words"]):
        return f"❌ 금지어({', '.join(game_state['forbidden_words'])})가 포함되어 있어 저장할 수 없습니다. 다시 말씀해주세요!"

    # 문장 완성 및 데이터 업데이트
    game_state["story"].append(clean_segment)
    game_state["participants"].add(user_name)

    # 최종 결과물 생성
    final_sentence = " ".join(game_state["story"])

    # 기록 저장
    save_game_result()

    # 게임 종료 상태로 변경
    game_state["is_active"] = False

    res = (
        f"🏁 **문장이 완성되었습니다!**\n\n"
        f"📝 **최종 문장**: {final_sentence}\n\n"
        f"👤 **참여자**: {user_name}\n"
        f"💾 결과가 `game_history.txt`에 저장되었습니다. 게임을 종료합니다!"
    )
    return res


@mcp.tool()
def view_history() -> str:
    """과거 기록 보기"""
    if not os.path.exists(HISTORY_FILE):
        return "아직 저장된 기록이 없습니다."
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return f.read()


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()