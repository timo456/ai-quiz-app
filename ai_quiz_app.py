import streamlit as st
import pandas as pd
import time
from datetime import datetime
import random
import json
import os

# 題庫載入（檔案需包含 answer、option_A~F）
df = pd.read_csv('ai_questions_fixed.csv', encoding='utf-8-sig')
total_questions = len(df)

# 初始化狀態
if 'mode' not in st.session_state:
    st.session_state.mode = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = ""

# 登入
if not st.session_state.user_id:
    st.title("🔐 請輸入暱稱開始測驗")
    nickname = st.text_input("請輸入你的暱稱：")
    if st.button("✅ 開始測驗") and nickname:
        st.session_state.user_id = nickname
        st.rerun()
    st.stop()

# 選擇模式
if not st.session_state.mode:
    st.title("📘 請選擇模式")
    if st.button("✅ 完整測驗"):
        st.session_state.mode = 'full'
        st.rerun()
    if os.path.exists(f"quiz_wrong_{st.session_state.user_id}.json"):
        if st.button("🧠 錯題複習"):
            st.session_state.mode = 'review'
            st.rerun()
    st.stop()

# 題目初始化
if 'shuffled_indices' not in st.session_state:
    if st.session_state.mode == 'full':
        st.session_state.shuffled_indices = random.sample(range(total_questions), total_questions)
    elif st.session_state.mode == 'review':
        with open(f"quiz_wrong_{st.session_state.user_id}.json", 'r', encoding='utf-8') as f:
            st.session_state.shuffled_indices = json.load(f)
        random.shuffle(st.session_state.shuffled_indices)

    st.session_state.q_index = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.selected_options = set()
    st.session_state.answers = []
    st.session_state.start_time = time.time()

# 測驗主畫面
st.title("🧠 AI 考題小測驗遊戲")
total = len(st.session_state.shuffled_indices)

if st.session_state.q_index < total:
    idx = st.session_state.shuffled_indices[st.session_state.q_index]
    row = df.iloc[idx]
    correct_answer_set = set(row['answer'].split(','))

    st.markdown(f"**第 {st.session_state.q_index + 1} 題 / {total}**\n\n{row['question']}")

    # 顯示選項 A~F
    options = [opt for opt in ['A', 'B', 'C', 'D', 'E', 'F'] if pd.notna(row.get(f'option_{opt}')) and row[f'option_{opt}']]
    multiselect_items = [f"{opt}. {row[f'option_{opt}']}" for opt in options]
    selected = st.multiselect("請選擇答案：", multiselect_items, key=f"q{idx}")

    if not st.session_state.answered:
        if st.button("✅ 確認答案"):
            elapsed = round(time.time() - st.session_state.start_time, 2)
            selected_keys = {opt.split('.')[0] for opt in selected}
            is_correct = selected_keys == correct_answer_set
            st.session_state.selected_options = selected_keys
            st.session_state.answered = True

            if is_correct:
                st.session_state.score += 1
                # 若為錯題複習，答對即移除
                if st.session_state.mode == 'review':
                    wrong_path = f"quiz_wrong_{st.session_state.user_id}.json"
                    if os.path.exists(wrong_path):
                        with open(wrong_path, 'r', encoding='utf-8') as f:
                            wrong_indices = json.load(f)
                        if idx in wrong_indices:
                            wrong_indices.remove(idx)
                            with open(wrong_path, 'w', encoding='utf-8') as f:
                                json.dump(wrong_indices, f, ensure_ascii=False)

            st.session_state.answers.append({
                "題號": st.session_state.q_index + 1,
                "題目": row['question'],
                "你的答案": "、".join(sorted(st.session_state.selected_options)),
                "正確答案": "、".join(sorted(correct_answer_set)),
                "是否正確": "✅ 正確" if is_correct else "❌ 錯誤",
                "時間戳記": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "耗時（秒）": elapsed
            })
    else:
        latest = st.session_state.answers[-1]
        if latest["是否正確"] == "✅ 正確":
            st.success("✅ 答對了！")
        else:
            st.error(f"❌ 答錯了，正確答案是：{latest['正確答案']}")

        if st.button("➡ 下一題"):
            st.session_state.q_index += 1
            st.session_state.answered = False
            st.session_state.selected_options = set()
            st.session_state.start_time = time.time()
            st.rerun()
else:
    st.balloons()
    st.subheader(f"🎉 測驗結束！你總共答對了 {st.session_state.score} / {total} 題")

    # 儲存錯題（僅完整測驗）
    if st.session_state.mode == 'full':
        wrong_indices = []
        for i, a in enumerate(st.session_state.answers):
            if a['是否正確'] != '✅ 正確':
                wrong_indices.append(st.session_state.shuffled_indices[i])
        with open(f"quiz_wrong_{st.session_state.user_id}.json", 'w', encoding='utf-8') as f:
            json.dump(wrong_indices, f, ensure_ascii=False)

    # 顯示紀錄與下載
    st.markdown(f"## 🧾 {st.session_state.user_id} 的答題紀錄")
    df_result = pd.DataFrame(st.session_state.answers)
    st.dataframe(df_result, use_container_width=True)

    csv = df_result.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 下載作答紀錄 CSV",
        data=csv,
        file_name=f"{st.session_state.user_id}_quiz_result.csv",
        mime='text/csv'
    )

    if st.button("🔁 再玩一次"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    if os.path.exists(f"quiz_wrong_{st.session_state.user_id}.json"):
        if st.button("🗑️ 清除錯題紀錄"):
            os.remove(f"quiz_wrong_{st.session_state.user_id}.json")
            st.success("✅ 錯題紀錄已刪除！")
            st.rerun()
