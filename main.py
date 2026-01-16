import os
import re
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("KakaoEmpathy", host="0.0.0.0")

HISTORY_FILE = "game_history.txt"
ALLOWED_ROUNDS = [1, 2, 3, 4, 5, 6, 7]

game_state = {
    "is_active": False,
    "current_round": None,
    "story": [],
    "forbidden_words": ["그리고", "하지만"],
    "participants": set()
}


@mcp.tool()
def start_story_game() -> str:
    """메뉴 안내"""
    return "지금은 1번부터 7번까지의 이야기만 이어갈 수 있습니다. '기록 보여줘'라고 입력해 현재 내용을 확인해보세요!"


@mcp.tool()
def view_history() -> str:
    """기록 목록 출력 (AI가 바로 읽기 좋게 형식 단순화)"""
    if not os.path.exists(HISTORY_FILE):
        return "아직 저장된 기록이 없네요."

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 단순 텍스트로 구성
    res = "[준비된 이야기 목록]\n\n"
    for r in ALLOWED_ROUNDS:
        pattern = rf"게임 {r}회차.*?완성 문장:\s*(.*?)\n"
        matches = re.findall(pattern, content, re.DOTALL)
        sentence = matches[-1].strip() if matches else "기록 없음"
        res += f"{r}번: {sentence}\n"

    res += "\n이어가고 싶은 번호를 말씀해주세요."
    return res


@mcp.tool()
def start_game_with_history(game_round: int) -> str:
    """특정 회차 불러오기"""
    if game_round not in ALLOWED_ROUNDS:
        return f"{game_round}번은 선택할 수 없습니다. 1~7번 사이를 골라주세요."

    try:
        if not os.path.exists(HISTORY_FILE):
            return "기록 파일이 없습니다."

        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = rf"게임 {game_round}회차.*?완성 문장:\s*(.*?)\n"
        matches = re.findall(pattern, content, re.DOTALL)

        if matches:
            saved_sentence = matches[-1].strip()
            game_state["is_active"] = True
            game_state["current_round"] = game_round
            game_state["story"] = [saved_sentence]
            return f"{game_round}번 문장 「{saved_sentence}」 뒤에 이어질 말을 입력해주세요."
        return f"{game_round}번 기록을 찾지 못했습니다."
    except:
        return "기록을 불러오는 중 오류가 발생했습니다."


@mcp.tool()
def add_word(user_name: str, word: str) -> str:
    """단어 추가"""
    if not game_state["is_active"]:
        return "먼저 이어갈 번호를 선택해주세요."

    if any(f in word for f in game_state["forbidden_words"]):
        return "금지어가 포함되어 있습니다. 다른 단어를 사용해주세요."

    game_state["story"].append(word.strip())
    game_state["participants"].add(user_name)
    final_sentence = " ".join(game_state["story"])

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"📅 [{timestamp}] 게임 {game_state['current_round']}회차\n📝 완성 문장: {final_sentence}\n👥 참여: {user_name}\n{'━' * 30}\n"
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except:
        pass

    game_state["is_active"] = False
    return f"완성되었습니다! 최종 문장: 「{final_sentence}」"


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()