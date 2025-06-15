import pandas as pd
import re

with open("raw_questions.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

questions = []
current = {}
option_map = {'A': 'option_A', 'B': 'option_B', 'C': 'option_C', 'D': 'option_D', 'E': 'option_E', 'F': 'option_F'}

for line in lines:
    line = line.strip()

    # 題目起始
    q_match = re.match(r"^(\d+)\.\s*\(\s*([A-F](?:,[A-F])*)\s*\)\s*(.*)", line)
    if q_match:
        if current:  # 上一題存起來
            questions.append(current)
        qid, ans_raw, qtext = q_match.groups()
        current = {
            "id": int(qid),
            "question": qtext.strip(),
            "answer": ans_raw.strip(),
            "type": "multiple" if "," in ans_raw else "single",
            "option_A": "", "option_B": "", "option_C": "",
            "option_D": "", "option_E": "", "option_F": ""
        }
        continue

    # 選項行
    opt_match = re.match(r"^([A-F])\.\s*(.+)", line)
    if opt_match and current:
        key, text = opt_match.groups()
        if key in option_map:
            current[option_map[key]] = text.strip()

# 最後一題也要存入
if current:
    questions.append(current)

# 存成 CSV
df = pd.DataFrame(questions)
df.to_csv("ai_questions_fixed.csv", index=False, encoding="utf-8-sig")
print(f"✅ 完成解析，共 {len(df)} 題，儲存為 ai_questions_fixed.csv")
