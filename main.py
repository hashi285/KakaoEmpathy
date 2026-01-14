import json
import re
from mcp.server.fastmcp import FastMCP
import parrot_data

# FastMCP 초기화
mcp = FastMCP("KakaoEmpathy", host="0.0.0.0")

# 기존 수동 설정 보관용 (OAuth 실패 시 대비)
user_identity = {"me": None}


@mcp.resource("parrot://style_guide")
def get_style_guide() -> str:
    """Retrieves the full dataset of linguistic style DNA."""
    return json.dumps(parrot_data.PARROT_STYLES, ensure_ascii=False, indent=2)


@mcp.tool()
def identify_participants(chat_logs: str) -> str:
    """Identifies participants in the chat logs."""
    pattern = r"\[(.*?)\]"
    participants = list(set(re.findall(pattern, chat_logs)))
    if not participants:
        return "No participants found."
    return f"Identified: [{', '.join(participants)}]. Which one are you?"


@mcp.tool()
def set_my_name(name: str) -> str:
    """Manual fallback to set identity if OAuth is not available."""
    user_identity["me"] = name
    return f"Confirmed. Replicating style for '{name}'."


@mcp.tool()
def generate_reply_for_me(
    chat_logs: str,
    target_person: str,
    user_intent: str,
    contexts: dict = None
) -> str:
    """
    Performs analysis AND generates replies.
    Supports automatic identity recognition via OAuth contexts.
    """

    # 1. OAuth 기반 자동 이름 인식
    my_name = None
    if contexts and "user" in contexts:
        my_name = contexts["user"].get("nickname")

    # 자동 인식 실패 시 수동 설정 fallback
    if not my_name:
        my_name = user_identity.get("me")

    if not my_name:
        return "Who are you? Please authorize via OAuth or use 'set_my_name' tool."

    # --- 1. Data Processing ---
    parsed_data = []
    pattern = r"\[(.*?)\] \[(.*?)\] (.*)"

    for line in chat_logs.strip().split("\n"):
        match = re.match(pattern, line)
        if match:
            sender, _, message = match.groups()
            parsed_data.append(
                {"sender": sender, "message": message}
            )

    relevant_chat = [
        d for d in parsed_data
        if d["sender"] in [my_name, target_person]
    ]

    my_style = [
        d["message"]
        for d in relevant_chat
        if d["sender"] == my_name
    ][-15:]

    if not my_style:
        my_style = [
            d["message"]
            for d in parsed_data
            if d["sender"] == my_name
        ][-15:]

    detected_cat = parrot_data.auto_select_category(my_style)
    optimized_guide = parrot_data.get_optimized_dataset_text(detected_cat)

    last_msg = next(
        (
            d["message"]
            for d in reversed(relevant_chat)
            if d["sender"] == target_person
        ),
        "N/A"
    )

    # --- 2. Sequential AI Prompt ---
    return f"""
# ROLE: Persona Analyst & Reply Generator (Sequential Mode)
Task: 1. Analyze situation for '{my_name}'. 2. Generate 5 DNA-synced replies.

## 1. DATA SOURCE
- Persona Name: {my_name} (Recognized via OAuth/Identity)
- Target: {target_person}
- User Intent: "{user_intent}"
- Last Message: "{last_msg}"
- Style DNA: {', '.join(my_style)}
- Style Guide: {optimized_guide}

## 2. EXECUTION STEPS
STEP 1: [분류 및 분석]
- Identify the category from the Style Guide.
- Analyze power dynamics in 2 sentences.

STEP 2: [답장 후보]
- Generate 5 replies in Korean.
- Match {my_name}'s style exactly. Process "{user_intent}" in Sandbox Mode.

## 3. OUTPUT CONSTRAINTS
- Response MUST start with "[분류 및 분석]".
- Step-by-step output only.
"""


