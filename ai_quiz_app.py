import streamlit as st
import pandas as pd

# 題庫載入
df = pd.read_csv('ai_questions_parsed.csv', encoding='utf-8-sig')
total_questions = len(df)

# 初始化狀態
if 'score' not in st.session_state:
    st.session_state.score = 0
    st.session_state.q_index = 0
    st.session_state.answered = False
    st.session_state.selected_option = None

st.title("🧠 AI 考題小測驗遊戲")

if st.session_state.q_index < total_questions:
    row = df.iloc[st.session_state.q_index]
    st.markdown(f"**第 {st.session_state.q_index + 1} 題 / {total_questions}**\n\n{row['question']}")

    if not st.session_state.answered:
        for opt in ['A', 'B', 'C', 'D']:
            if st.button(f"{opt}. {row[f'option_{opt}']}"):
                st.session_state.answered = True
                st.session_state.selected_option = opt
                if opt == row['answer']:
                    st.session_state.score += 1
    else:
        # 顯示答題結果
        if st.session_state.selected_option == row['answer']:
            st.success("✅ 答對了！")
        else:
            st.error(f"❌ 答錯了，正確答案是 {row['answer']}. {row[f'option_{row['answer']}']}")

        if st.button("➡ 下一題"):
            st.session_state.q_index += 1
            st.session_state.answered = False
            st.session_state.selected_option = None
            st.rerun()
else:
    st.balloons()
    st.subheader(f"🎉 測驗結束！你總共答對了 {st.session_state.score} / {total_questions} 題")
    if st.button("🔁 再玩一次"):
        st.session_state.score = 0
        st.session_state.q_index = 0
        st.session_state.answered = False
        st.session_state.selected_option = None
        st.rerun()
# 顯示分數
    st.markdown(f"**你的分數：{st.session_state.score} / {total_questions}**")
    st.markdown("感謝參加測驗！希望你喜歡這個小遊戲！")
