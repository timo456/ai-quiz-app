import streamlit as st
import pandas as pd
import time
import json
import os
from datetime import datetime
import random

# 題庫載入
df = pd.read_csv('ai_questions_parsed.csv', encoding='utf-8-sig')
total_questions = len(df)

# 🔰 步驟 1: 讓使用者輸入暱稱（只跑一次）
if 'user_id' not in st.session_state:
    st.title("👤 請先輸入暱稱開始遊戲")
    name = st.text_input("請輸入你的暱稱：")
    if st.button("🎮 開始測驗") and name:
        st.session_state.user_id = name
        st.rerun()
    st.stop()

user_id = st.session_state.user_id
progress_file = f"quiz_progress_{user_id}.json"
wrong_file = f"quiz_wrong_{user_id}.json"

# 🔄 模式選擇：完整測驗 or 錯題複習
if 'mode' not in st.session_state:
    st.title("📚 請選擇模式")
    st.session_state.mode = st.radio("請選擇測驗模式：", ["完整測驗", "錯題複習"])
    if st.button("✅ 開始此模式"):
        st.rerun()
    st.stop()

# 🔰 步驟 2: 載入進度或初始化
if 'q_index' not in st.session_state:
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            st.session_state.update(data)
    else:
        # 決定題目來源
        if st.session_state.mode == "錯題複習" and os.path.exists(wrong_file):
            with open(wrong_file, 'r', encoding='utf-8') as f:
                wrong_ids = json.load(f)
            if wrong_ids:
                st.session_state.shuffled_indices = random.sample(wrong_ids, len(wrong_ids))
            else:
                st.warning("目前沒有錯題紀錄，將進入完整測驗模式。")
                st.session_state.shuffled_indices = random.sample(range(total_questions), total_questions)
        else:
            st.session_state.shuffled_indices = random.sample(range(total_questions), total_questions)

        st.session_state.score = 0
        st.session_state.q_index = 0
        st.session_state.answered = False
        st.session_state.selected_option = None
        st.session_state.answers = []
        st.session_state.start_time = time.time()

st.title(f"🧠 AI 考題小測驗遊戲（{st.session_state.mode}）")

if st.session_state.q_index < len(st.session_state.shuffled_indices):
    idx = st.session_state.shuffled_indices[st.session_state.q_index]
    row = df.iloc[idx]
    st.markdown(f"**第 {st.session_state.q_index + 1} 題 / {len(st.session_state.shuffled_indices)}**\n\n{row['question']}")

    if not st.session_state.answered:
        for opt in ['A', 'B', 'C', 'D']:
            if st.button(f"{opt}. {row[f'option_{opt}']}", key=opt):
                end_time = time.time()
                elapsed = round(end_time - st.session_state.start_time, 2)
                st.session_state.start_time = end_time

                is_correct = (opt == row['answer'])
                answer_key = row['answer']

                st.session_state.answers.append({
                    "題號": st.session_state.q_index + 1,
                    "題目": row['question'],
                    "你的答案": f"{opt}. {row[f'option_{opt}']}",
                    "正確答案": f"{answer_key}. {row[f'option_{answer_key}']}",
                    "是否正確": "✅ 正確" if is_correct else "❌ 錯誤",
                    "時間戳記": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "耗時（秒）": elapsed,
                    "題目索引": idx
                })

                if is_correct:
                    st.session_state.score += 1
                st.session_state.answered = True
                st.session_state.selected_option = opt

                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump(dict(st.session_state), f, ensure_ascii=False)

    else:
        if st.session_state.selected_option == row['answer']:
            st.success("✅ 答對了！")
        else:
            answer_key = row['answer']
            st.error(f"❌ 答錯了，正確答案是 {answer_key}. {row[f'option_{answer_key}']}")

        if st.button("➡ 下一題"):
            st.session_state.q_index += 1
            st.session_state.answered = False
            st.session_state.selected_option = None
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(dict(st.session_state), f, ensure_ascii=False)
            st.rerun()

else:
    st.balloons()
    st.subheader(f"🎉 測驗結束！你總共答對了 {st.session_state.score} / {len(st.session_state.shuffled_indices)} 題")

    st.markdown(f"## 🧾 {user_id} 的答題紀錄")
    df_result = pd.DataFrame(st.session_state.answers)
    st.dataframe(df_result, use_container_width=True)

    csv = df_result.to_csv(index=False, encoding='utf-8-sig')
    st.download_button("📥 下載作答紀錄 CSV", data=csv, file_name=f"{user_id}_quiz_result.csv", mime='text/csv')

    # ⛔ 錯題保存
    wrong_indices = [entry['題目索引'] for entry in st.session_state.answers if entry['是否正確'] == '❌ 錯誤']
    with open(wrong_file, 'w', encoding='utf-8') as f:
        json.dump(wrong_indices, f, ensure_ascii=False)

    if st.button("🔁 再玩一次"):
        if os.path.exists(progress_file):
            os.remove(progress_file)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
