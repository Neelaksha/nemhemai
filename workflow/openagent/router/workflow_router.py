# current


# def choose_workflow(user_msg: str):
#     msg = user_msg.lower()

#     # 🔥 ADD THIS
#     if any(k in msg for k in ["email", "send mail", "send email"]):
#         return "insights"

#     if any(k in msg for k in ["insight", "trend", "analysis", "report"]):
#         return "insights"

#     return "chat"

def choose_workflow(user_input: str):

    text = user_input.lower()

    if "report" in text:
        return "report"
    elif "insight" in text:
        return "insights"
    else:
        return "chat"


# from openagent.services.llm_service import call_llm


# async def choose_workflow(user_msg: str) -> str:

#     prompt = f"""
# You are a routing agent.

# Decide which workflow to use:

# - "chat" → general conversation
# - "insights" → data analysis, reports, trends, or sending email

# Respond with ONLY one word:
# chat OR insights

# User message:
# {user_msg}
# """

#     response = await call_llm(prompt)

#     decision = response.strip().lower()

#     if "insight" in decision:
#         return "insights"

#     return "chat"