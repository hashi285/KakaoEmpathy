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
def show_menu() -> str:
    """Show the start guide."""
    return (
        "상태: 메뉴 출력 완료.\n"
        "지시: 아래 내용을 사용자에게 다정한 한국어 말투로 전달하세요.\n"
        "내용: 1~7번 사이의 이야기를 선택할 수 있으며, '기록 보여줘'로 목록 확인이 가능함을 안내."
    )


@mcp.tool()
def fetch_history() -> str:
    """Retrieve logs for rounds 1-7."""
    if not os.path.exists(HISTORY_FILE):
        return "상태: 기록 없음. 사용자에게 아직 저장된 이야기가 없다고 한국어로 말하세요."

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    history_text = ""
    for r in ALLOWED_ROUNDS:
        pattern = rf"게임 {r}회차.*?완성 문장:\s*(.*?)\n"
        matches = re.findall(pattern, content, re.DOTALL)
        sentence = matches[-1].strip() if matches else "비어 있음"
        history_text += f"{r}번: {sentence}\n"

    return (
        f"상태: 기록 조회 성공.\n"
        f"지시: 아래 목록을 보여주며 이어서 하고 싶은 번호를 한국어로 물어보세요.\n"
        f"목록:\n{history_text}"
    )


@mcp.tool()
def load_game_round(game_round: int) -> str:
    """Load a specific story round."""
    if game_round not in ALLOWED_ROUNDS:
        return f"지시: {game_round}번은 안 된다고 한국어로 말하고 1~7번 중에서 다시 고르게 하세요."

    try:
        if not os.path.exists(HISTORY_FILE):
            return "상태: 파일 없음."

        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = rf"게임 {game_round}회차.*?완성 문장:\s*(.*?)\n"
        matches = re.findall(pattern, content, re.DOTALL)

        if matches:
            saved_sentence = matches[-1].strip()
            game_state["is_active"] = True
            game_state["current_round"] = game_round
            game_state["story"] = [saved_sentence]
            return (
                f"상태: {game_round}번 로드 성공.\n"
                f"지시: 현재 문장 '{saved_sentence}'를 알려주고, 이 뒤에 올 말을 한국어로 요청하세요."
            )
        return "상태: 해당 회차 기록 찾을 수 없음."
    except Exception as e:
        return f"상태: 에러 발생. 사용자에게 잠시 후 다시 시도해달라고 한국어로 말하세요."


@mcp.tool()
def append_phrase(user_name: str, phrase: str) -> str:
    """Saves the phrase and closes the session. AI responds in Korean."""
    if not game_state["is_active"]:
        return "Status: Inactive. Instruction: 게임이 시작되지 않았으니 번호를 먼저 골라달라고 한국어로 말하세요."

    if any(forbidden in phrase for forbidden in game_state["forbidden_words"]):
        return "Status: Forbidden word. Instruction: 금지어('그리고', '하지만')를 썼다고 한국어로 안내하고 다시 입력받으세요."

    game_state["story"].append(phrase.strip())
    game_state["participants"].add(user_name)
    final_sentence = " ".join(game_state["story"])

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (
            f"📅 [{timestamp}] 게임 {game_state['current_round']}회차\n"
            f"📝 완성 문장: {final_sentence}\n"
            f"👥 참여: {user_name}\n"
            f"{'━' * 30}\n"
        )
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry)

        current_round = game_state["current_round"]
        game_state["is_active"] = False  # 세션 종료

        return (
            f"Status: Success. Round {current_round} saved.\n"
            f"Result Sentence: {final_sentence}\n"
            "Instruction: 저장이 완료되었음을 한국어로 축하하고, 최종 문장을 보여준 뒤 "
            "'기록 보여줘'를 통해 다른 이야기를 할 수 있다고 친절하게 안내하며 대화를 마치세요."
        )
    except:
        return "Status: Save Error. Instruction: 저장 실패를 한국어로 알리세요."


def main():
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()