import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# 서버 이름 고정
mcp = FastMCP("KakaoEmpathy", host="0.0.0.0")

HISTORY_FILE = "game_history.txt"

game_state = {
    "is_active": False,
    "story": [],
    "last_player": None,  # 여기에 카카오톡 사용자 이름 또는 ID가 저장됨
    "forbidden_words": ["그리고", "하지만"],
    "word_limit": 15,
    "participants": set()
}


def save_game_result():
    """게임 결과를 안전하게 텍스트 파일에 기록합니다."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_sentence = " ".join(game_state["story"])
        # set을 list로 명확히 변환 후 문자열화 (오류 방지)
        participants_list = ", ".join(list(game_state["participants"]))

        entry = (
            f"📅 기록 일시: {timestamp}\n"
            f"📝 완성 문장: {final_sentence}\n"
            f"👥 참여 인원: {participants_list}\n"
            f"{'━' * 30}\n"
        )

        # 파일이 없으면 자동 생성 ('a' 모드)
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        # 로그를 통해 서버 측에서 오류 확인 가능
        print(f"Error saving file: {e}")


@mcp.tool()
def get_game_info() -> str:
    """카카오톡 사용자에게 게임 규칙 설명"""
    return (
        "📖 **한 마디 스토리 빌딩**\n\n"
        "카카오톡 친구들과 함께 문장을 완성해보세요!\n"
        "1. 한 마디씩 이어가기 (연속 입력 불가)\n"
        "2. 금지어: '그리고', '하지만'\n"
        "3. 로그인된 이름으로 자동 참여됩니다.\n\n"
        "지금 바로 단어를 던져서 시작하세요!"
    )


@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    """카카오톡에서 전달받은 user_name을 기반으로 단어 추가"""
    if not game_state["is_active"]:
        game_state["is_active"] = True
        game_state["story"] = []
        game_state["participants"] = set()

    # 중복 입력 방지 (카카오톡 고유 이름/ID 비교)
    if user_name == game_state["last_player"]:
        return f"🚫 {user_name}님, 다음 친구의 차례를 기다려주세요!"

    # 입력값 정제 (최대 3어절)
    clean_segment = " ".join(word.strip().split()[:3])

    # 금지어 확인
    if any(forbidden in clean_segment for forbidden in game_state["forbidden_words"]):
        return f"❌ 금지어가 포함되어 있어요! 다시 생각해보세요."

    # 데이터 업데이트
    game_state["story"].append(clean_segment)
    game_state["last_player"] = user_name
    game_state["participants"].add(user_name)

    # 목표 달성 시
    if len(game_state["story"]) >= game_state["word_limit"]:
        save_game_result()  # 여기서 이제 오류가 나지 않습니다.
        game_state["is_active"] = False
        res = (f"🏁 **문장 완성!**\n\n"
               f"📝 {' '.join(game_state['story'])}\n\n"
               f"💾 기록이 저장되었습니다.")
        return res

    return get_current_board()


@mcp.tool()
def get_current_board() -> str:
    """현황판 출력"""
    if not game_state["story"]:
        return "진행 중인 게임이 없습니다."

    count = len(game_state["story"])
    progress = "▓" * count + "░" * (game_state["word_limit"] - count)

    return (f"🎮 **STORY BOARD**\n"
            f"━━━━━━━━━━━━━━\n"
            f"📝: {' '.join(game_state['story'])}\n"
            f"📊: {progress} ({count}/{game_state['word_limit']})\n"
            f"👤 마지막: {game_state['last_player']}\n"
            f"━━━━━━━━━━━━━━")


@mcp.tool()
def view_history() -> str:
    """저장된 기록 보기"""
    if not os.path.exists(HISTORY_FILE):
        return "기록이 없습니다."
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return f.read()


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()