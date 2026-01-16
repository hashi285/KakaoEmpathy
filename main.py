import os
import re
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# 서버 이름 설정
mcp = FastMCP("KakaoEmpathy", host="0.0.0.0")

HISTORY_FILE = "game_history.txt"
# 사용 가능한 고정 회차 번호 리스트
ALLOWED_ROUNDS = [1, 2, 3, 4, 5, 6, 7]

game_state = {
    "is_active": False,
    "current_round": None,
    "story": [],
    "forbidden_words": ["그리고", "하지만"],
    "participants": set()
}

def save_game_result():
    """문장 수정 내용을 파일에 기록"""
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
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"Error saving: {e}")

@mcp.tool()
def start_story_game() -> str:
    """게임 참여 방식 안내"""
    return (
        "반가워요! 우리 같이 이야기를 만들어볼까요? 😊\n\n"
        "현재는 1회차부터 7회차까지의 이야기만 이어갈 수 있습니다.\n"
        "먼저 '기록 보여줘'라고 말씀하신 뒤, 원하는 번호를 골라보세요!"
    )

@mcp.tool()
def start_game_with_history(game_round: int) -> str:
    """지정된 회차를 불러와서 게임 시작"""
    if game_round not in ALLOWED_ROUNDS:
        return f"현재는 1번부터 7번까지만 선택 가능해요. 번호를 다시 확인해주세요!"

    try:
        if not os.path.exists(HISTORY_FILE):
            return "아직 저장된 기록이 없습니다."

        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # 해당 회차의 가장 최신 문장 검색
        pattern = rf"게임 {game_round}회차.*?완성 문장:\s*(.*?)\n"
        matches = re.findall(pattern, content, re.DOTALL)

        if matches:
            saved_sentence = matches[-1].strip()
            game_state["is_active"] = True
            game_state["current_round"] = game_round
            game_state["story"] = [saved_sentence]
            game_state["participants"] = set()
            return (
                f"{game_round}회차 이야기를 불러왔습니다.\n\n"
                f"현재 문장: \"{saved_sentence}\"\n\n"
                "이 뒤에 이어질 한 마디를 알려주세요!"
            )
        else:
            return f"{game_round}회차 기록을 찾을 수 없습니다."
    except Exception as e:
        return f"기록을 읽는 중 오류가 발생했습니다."

@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    """단어 추가 및 저장"""
    if not game_state["is_active"]:
        return "진행 중인 게임이 없어요. 먼저 회차 번호(1~7)를 선택해주세요!"

    if any(f in word for f in game_state["forbidden_words"]):
        return "앗, 금지어('그리고', '하지만')가 포함되어 있어요. 다른 단어를 써주세요!"

    game_state["story"].append(word.strip())
    game_state["participants"].add(user_name)

    final_sentence = " ".join(game_state["story"])
    save_game_result()
    game_state["is_active"] = False

    return (
        f"문장이 성공적으로 업데이트되었습니다!\n\n"
        f"수정된 문장: \"{final_sentence}\"\n\n"
        "기록에 저장되었습니다. 다른 회차도 구경해보시겠어요?"
    )

@mcp.tool()
def view_history() -> str:
    """7개 목록 요약 출력"""
    if not os.path.exists(HISTORY_FILE):
        return "아직 기록이 없습니다."

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    summary = "📚 **플레이 가능한 7개의 이야기 목록**\n\n"
    for r in ALLOWED_ROUNDS:
        pattern = rf"게임 {r}회차.*?완성 문장:\s*(.*?)\n"
        matches = re.findall(pattern, content, re.DOTALL)
        sentence = matches[-1].strip() if matches else "기록 없음"
        summary += f"{r}번: {sentence}\n"

    summary += "\n이어서 하고 싶은 번호를 말씀해주세요!"
    return summary

def main():
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()