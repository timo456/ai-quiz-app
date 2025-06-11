import re
import pandas as pd

# 🔽 貼上你從 PDF 複製的文字（多題可連續貼）
with open("raw_questions.txt", "r", encoding="utf-8") as f:
    text = f.read()

# 正規表達式解析題號、答案、題目敘述與四個選項
pattern = re.compile(
    r"(\d+)\.\s*（\s*([1-4])\s*）\s*(.*?)"
    r"•\s*1\.\s*(.*?)"
    r"•\s*2\.\s*(.*?)"
    r"•\s*3\.\s*(.*?)"
    r"•\s*4\.\s*(.*?)(?=\n\d+\.|$)",
    re.DOTALL
)

questions = []
for match in pattern.finditer(text):
    q_id, answer_num, q_text, a, b, c, d, *_ = match.groups()
    questions.append({
        "id": int(q_id),
        "question": re.sub(r"\s+", " ", q_text.strip()),
        "option_A": a.strip(),
        "option_B": b.strip(),
        "option_C": c.strip(),
        "option_D": d.strip(),
        "answer": ['A', 'B', 'C', 'D'][int(answer_num) - 1]
    })

# 儲存為 CSV
df = pd.DataFrame(questions)
df.to_csv("ai_questions_parsed.csv", index=False, encoding="utf-8-sig")

print(f"✅ 解析完成，共 {len(df)} 題，已儲存為 ai_questions_parsed.csv")
