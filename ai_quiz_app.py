import pandas as pd
import streamlit as st
import time
from datetime import datetime


# 題庫載入
df = pd.read_csv('ai_questions_parsed.csv', encoding='utf-8-sig')
total_questions = len(df)

# 初始化狀態
if 'score' not in st.session_state:
    st.session_state.score = 0
    st.session_state.q_index = 0
    st.session_state.answered = False
    st.session_state.selected_option = None
    st.session_state.answers = []  # 🆕 答題記錄清單
    st.session_state.start_time = time.time()
    st.session_state.user_id = f"User_{datetime.now().strftime('%H%M%S')}"  # 🆕 匿名 ID


# 主標題
st.title("🧠 AI 考題小測驗遊戲")
st.progress(st.session_state.q_index / total_questions)

# 題目顯示邏輯
if st.session_state.q_index < total_questions:
    row = df.iloc[st.session_state.q_index]
    
    # 題目卡片樣式
    with st.container():
        st.markdown(f"""
        <div style='border:1px solid #ccc; padding:20px; border-radius:10px; box-shadow:2px 2px 10px #eee'>
        <strong>第 {st.session_state.q_index + 1} 題 / {total_questions}</strong><br><br>
        {row['question']}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 選項按鈕
    if not st.session_state.answered:
        for opt in ['A', 'B', 'C', 'D']:
            if st.button(f"{opt}. {row[f'option_{opt}']}", key=opt):
                # 🧠 Step 1: 計算耗時
                end_time = time.time()
                elapsed = round(end_time - st.session_state.start_time, 2)
                st.session_state.start_time = end_time

                # 🧠 Step 2: 檢查對錯
                is_correct = (opt == row['answer'])

                # 🧠 Step 3: 記錄進 session_state.answers
                st.session_state.answers.append({
                    "題號": st.session_state.q_index + 1,
                    "題目": row['question'],
                    "你的答案": f"{opt}. {row[f'option_{opt}']}",
                    "正確答案": f"{row['answer']}. {row[f'option_{row['answer']}']}",
                    "是否正確": "✅ 正確" if is_correct else "❌ 錯誤",
                    "時間戳記": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "耗時（秒）": elapsed
                })

                # 加分與切換狀態
                if is_correct:
                    st.session_state.score += 1
                st.session_state.answered = True
                st.session_state.selected_option = opt


# 結果頁
else:
    st.balloons()
    score = st.session_state.score
    st.subheader(f"🎉 測驗結束！你總共答對了 {score} / {total_questions} 題")

    # 🎉 測驗結束
    st.balloons()
    st.subheader(f"🎉 測驗結束！你總共答對了 {st.session_state.score} / {total_questions} 題")

    # 🧾 顯示答題紀錄表格
    st.markdown(f"## 🧾 {st.session_state.user_id} 的答題紀錄")
    df_result = pd.DataFrame(st.session_state.answers)
    st.dataframe(df_result, use_container_width=True)

    # 📥 提供下載 CSV
    csv = df_result.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 下載作答紀錄 CSV",
        data=csv,
        file_name=f'{st.session_state.user_id}_quiz_result.csv',
        mime='text/csv'
    )

    # 分析評語
    if score >= 9:
        comment = "👑 你是 AI 大師！"
    elif score >= 6:
        comment = "👍 很棒，你對 AI 領域已有一定了解！"
    elif score >= 3:
        comment = "🧐 再接再厲，多多練習！"
    else:
        comment = "🤖 沒關係，再挑戰一次會更好喔！"

    st.markdown(f"### {comment}")
    st.markdown("---")
    st.markdown(f"**你的分數：{score} / {total_questions}**")
    st.markdown("感謝參加測驗！希望你喜歡這個小遊戲 ❤️")

    if st.button("🔁 再玩一次"):
        st.session_state.score = 0
        st.session_state.q_index = 0
        st.session_state.answered = False
        st.session_state.selected_option = None
        st.rerun()
