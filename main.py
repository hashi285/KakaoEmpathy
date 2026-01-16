import os
import re
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("KakaoEmpathy", host="0.0.0.0")

HISTORY_FILE = "game_history.txt"
# 사용 가능한 고정 회차 번호 리스트
ALLOWED_ROUNDS = [1, 2, 3, 4, 5, 6, 7]

game_state = {
    "is_active": False,
    "current_round": None,  # 현재 진행 중인 회차 번호
    "story": [],
    "forbidden_words": ["그리고", "하지만"],
    "participants": set()
}


def save_game_result():
    """수정된 문장을 기록에 반영합니다. (기존 기록을 찾아 업데이트하거나 덧붙임)"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_sentence = " ".join(game_state["story"])
        participants_list = ", ".join(list(game_state["participants"]))

        entry = (
            f"📅 [{timestamp}] 게임 {game_state['current_round']}회차\n"
            f"📝 완성 문장: {final_sentence}\n"
            f"👥 참여 인원: {participants_list}\n"
            f"{'━' * 30}\n"
        )
        # 이어서 하기 형식이므로 계속 추가(append) 방식으로 기록합니다.
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"Error saving: {e}")


@mcp.tool()
def start_story_game() -> str:
    """게임 시작 메뉴 (지정된 7개 회차 중 선택 유도)"""
    return (
        "🎮 **지정된 7개의 이야기 중 하나를 선택해주세요!**\n\n"
        "현재는 새로운 이야기를 만들 수 없으며, 기존 7개 회차의 내용을 이어가는 것만 가능합니다.\n\n"
        "📜 **참여 방법**:\n"
        "1. '기록 보여줘'를 입력해 1~7회차 문장을 확인합니다.\n"
        "2. 'N회차 이어서 할래'라고 말씀해주세요.\n\n"
        "어떤 번호의 이야기를 완성해볼까요? 😊"
    )


@mcp.tool()
def start_game_with_history(game_round: int) -> str:
    """지정된 7개 회차 내에서만 게임을 불러옵니다."""
    if game_round not in ALLOWED_ROUNDS:
        return f"❌ 죄송합니다. 현재는 1회차부터 7회차 사이의 게임만 플레이하실 수 있습니다."

    try:
        if not os.path.exists(HISTORY_FILE):
            return "기록 파일이 존재하지 않습니다."

        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # 파일에서 해당 회차의 가장 최신 완성 문장을 찾음
        pattern = rf"게임 {game_round}회차.*?완성 문장:\s*(.*?)\n"
        matches = re.findall(pattern, content, re.DOTALL)

        if matches:
            saved_sentence = matches[-1].strip()  # 가장 마지막에 저장된(최신) 문장
            game_state["is_active"] = True
            game_state["current_round"] = game_round
            game_state["story"] = [saved_sentence]
            game_state["participants"] = set()
            return (
                f"📂 **{game_round}회차 이야기를 불러왔습니다!**\n\n"
                f"📜 현재 문장:\n\"{saved_sentence}\"\n\n"
                f"이 뒤에 이어질 마디를 말씀해주세요! ✨"
            )
        else:
            return f"❌ {game_round}회차의 기본 문장을 찾을 수 없습니다."
    except Exception as e:
        return f"오류 발생: {str(e)}"


@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    """불러온 7개 문장 뒤에 단어를 추가합니다."""
    if not game_state["is_active"]:
        return "진행 중인 게임이 없어요! 1~7회차 중 하나를 먼저 골라주세요."

    if any(f in word for f in game_state["forbidden_words"]):
        return f"❌ 금지어({', '.join(game_state['forbidden_words'])})는 사용할 수 없어요!"

    game_state["story"].append(word.strip())
    game_state["participants"].add(user_name)

    final_sentence = " ".join(game_state["story"])
    save_game_result()  # 변경된 내용을 기록에 추가
    game_state["is_active"] = False  # 한 마디 추가 후 즉시 종료

    return (
        f"🏁 **{game_state['current_round']}회차 문장 업데이트!**\n\n"
        f"📝 \"{final_sentence}\"\n\n"
        f"기록 보관함에 잘 저장되었습니다. 다른 회차를 골라보시겠어요? 😊"
    )


@mcp.tool()
def view_history() -> str:
    """7개 회차의 목록을 보여줍니다."""
    if not os.path.exists(HISTORY_FILE):
        return "기록이 없습니다."

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 각 회차별로 가장 최신 문장만 추출해서 요약본 만들기
    summary = "📚 **[플레이 가능한 7개의 이야기]**\n"
    for r in ALLOWED_ROUNDS:
        pattern = rf"게임 {r}회차.*?완성 문장:\s*(.*?)\n"
        matches = re.findall(pattern, content, re.DOTALL)
        sentence = matches[-1].strip() if matches else "문장을 찾을 수 없음"
        summary += f"🔹 {r}회차: {sentence}\n"

    summary += "\n이어서 하고 싶은 회차 번호를 말씀해주세요! ✨"
    return summary


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()