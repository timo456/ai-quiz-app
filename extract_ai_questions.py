import re
import pandas as pd

# 載入題目文字檔
with open("raw_questions.txt", "r", encoding="utf-8") as f:
    text = f.read()

# 正規表達式：支援選項 A～F（最大六選）
pattern = re.compile(
    r"(\d+)\.\s*\(\s*([A-F](?:,[A-F])*)\s*\)\s*(.*?)\n"
    r"A\.\s*(.*?)\n"
    r"B\.\s*(.*?)\n"
    r"C\.\s*(.*?)\n"
    r"D\.\s*(.*?)\n"
    r"(?:E\.\s*(.*?)\n)?"     # 選項 E（可選）
    r"(?:F\.\s*(.*?))?(?=\n\d+\.|\Z)",  # 選項 F（可選）
    re.DOTALL
)

questions = []
for match in pattern.finditer(text):
    q_id, answer_str, q_text, a, b, c, d, e, f = match.groups()
    answers = [s.strip() for s in answer_str.split(',')]
    q_type = "multiple" if len(answers) > 1 else "single"

    questions.append({
        "id": int(q_id),
        "question": re.sub(r"\s+", " ", q_text.strip()),
        "option_A": a.strip(),
        "option_B": b.strip(),
        "option_C": c.strip(),
        "option_D": d.strip(),
        "option_E": e.strip() if e else "",
        "option_F": f.strip() if f else "",
        "answer": ",".join(answers),
        "type": q_type
    })

# 儲存為 CSV
df = pd.DataFrame(questions)
df.to_csv("ai_questions_fixed.csv", index=False, encoding="utf-8-sig")
print(f"✅ 完成！共 {len(df)} 題，已儲存為 ai_questions_fixed.csv（支援 A~F 並自動分類 single/multiple）")
