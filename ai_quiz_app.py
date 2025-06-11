import streamlit as st
import pandas as pd
import random


# 題庫載入
df = pd.read_csv('ai_questions_parsed.csv' , encoding='utf-8-sig')

# 初始化狀態
if 'score' not in st.session_state:
    st.session_state.score = 0
    st.session_state.q_index = 0
    st.session_state.selected_ids = random.sample(range(len(df)), 10)

st.title("🧠 AI 考題小測驗遊戲")

if st.session_state.q_index < 10:
    idx = st.session_state.selected_ids[st.session_state.q_index]
    row = df.iloc[idx]
    st.markdown(f"**第 {st.session_state.q_index + 1} 題**: {row['question']}")

    for opt in ['A', 'B', 'C', 'D']:
        if st.button(f"{opt}. {row[f'option_{opt}']}"):
            if opt == row['answer']:
                st.success("✅ 答對了！")
                st.session_state.score += 1
            else:
                st.error(f"❌ 答錯了，正確答案是 {row['answer']}")
            st.session_state.q_index += 1
            st.experimental_rerun()
else:
    st.subheader(f"🎉 測驗結束！你答對了 {st.session_state.score} / 10 題")
    if st.button("🔁 再玩一次"):
        st.session_state.score = 0
        st.session_state.q_index = 0
        st.session_state.selected_ids = random.sample(range(len(df)), 10)
