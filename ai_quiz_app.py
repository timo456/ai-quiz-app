import streamlit as st
import pandas as pd
import time
from datetime import datetime
import random
import json
import os
import re

# ====== 題庫載入（新版）======
df = pd.read_csv('ai_questions_refixed_new.csv', encoding='utf-8-sig')
total_questions = len(df)

# ====== 工具：解析答案 ======
def parse_answer(answer: str, qtype: str):
    answer = (str(answer) if answer is not None else "").strip()

    if qtype == "single":
        return answer  # "A"

    if qtype == "multiple":
        # "A,C,F"
        return set([x.strip() for x in answer.split(",") if x.strip()])

    if qtype == "matching":
        # "1->B;2->D;3->C;4->A"
        pairs = {}
        for part in re.split(r"[;；]\s*", answer):
            if "->" in part:
                left, right = [x.strip() for x in part.split("->", 1)]
                if left and right:
                    pairs[left] = right
        return pairs  # dict

    if qtype == "ordering":
        # "A->B->C->D->E"
        seq = [x.strip() for x in answer.split("->") if x.strip()]
        return seq  # list

    return answer

def get_options(row):
    opts = {}
    for opt in ["A", "B", "C", "D", "E", "F"]:
        v = row.get(f"option_{opt}")
        if pd.notna(v) and str(v).strip():
            opts[opt] = str(v).strip()
    return opts

def is_correct(user_answer, correct_key, qtype):
    if qtype == "single":
        return str(user_answer).strip() == str(correct_key).strip()

    if qtype == "multiple":
        return set(user_answer) == correct_key

    if qtype == "matching":
        # user_answer: dict
        if not isinstance(user_answer, dict) or not isinstance(correct_key, dict):
            return False
        # 必須每個 key 都答、且完全一致
        for k, v in correct_key.items():
            if str(user_answer.get(k, "")).strip() != str(v).strip():
                return False
        return True

    if qtype == "ordering":
        # user_answer: list
        if not isinstance(user_answer, list) or not isinstance(correct_key, list):
            return False
        ua = [x.strip() for x in user_answer if str(x).strip()]
        return ua == correct_key

    return str(user_answer).strip() == str(correct_key).strip()

def format_correct_answer_for_show(correct_key, qtype):
    if qtype == "single":
        return correct_key
    if qtype == "multiple":
        return "、".join(sorted(list(correct_key)))
    if qtype == "matching":
        # dict -> "1->B、2->D..."
        return "、".join([f"{k}->{v}" for k, v in correct_key.items()])
    if qtype == "ordering":
        return "->".join(correct_key)
    return str(correct_key)

# ====== 初始化狀態 ======
if 'mode' not in st.session_state:
    st.session_state.mode = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = ""

# ====== 登入 ======
if not st.session_state.user_id:
    st.title("🔐 請輸入暱稱開始測驗")
    nickname = st.text_input("請輸入你的暱稱：")
    if st.button("✅ 開始測驗") and nickname:
        st.session_state.user_id = nickname
        st.rerun()
    st.stop()

# ====== 完成進度 ======
done_path = f"quiz_done_{st.session_state.user_id}.json"
if not os.path.exists(done_path):
    with open(done_path, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False)

with open(done_path, 'r', encoding='utf-8') as f:
    done_ids = set(json.load(f))

st.sidebar.info(f"📚 題庫完成進度：{len(done_ids)} / {len(df)} 題")

# ====== 選擇模式 ======
if not st.session_state.mode:
    st.title("📘 請選擇模式")
    if st.button("✅ 完整測驗"):
        st.session_state.mode = 'full'
        st.rerun()

    if os.path.exists(f"quiz_wrong_{st.session_state.user_id}.json"):
        if st.button("🧠 錯題複習"):
            st.session_state.mode = 'review'
            st.rerun()

    if st.button("🏆 查看排行榜"):
        st.session_state.mode = 'leaderboard'
        st.rerun()

    st.stop()

# ====== 排行榜 ======
if st.session_state.mode == 'leaderboard':
    st.title("🏆 排行榜")
    if os.path.exists("leaderboard.json"):
        with open("leaderboard.json", "r", encoding="utf-8") as f:
            leaderboard = json.load(f)
        df_leaderboard = pd.DataFrame(leaderboard)
        if len(df_leaderboard) > 0:
            df_leaderboard = df_leaderboard.sort_values(by='score', ascending=False).head(10)
            st.dataframe(df_leaderboard, use_container_width=True)
        else:
            st.info("目前還沒有任何人上榜，快來挑戰吧！")
    else:
        st.info("目前還沒有任何人上榜，快來挑戰吧！")

    if st.button("🔙 回主畫面"):
        del st.session_state.mode
        st.rerun()
    st.stop()

# ====== 初始化題目 ======
if 'shuffled_indices' not in st.session_state:
    available_indices = [i for i in range(total_questions) if int(df.iloc[i]['id']) not in done_ids]

    if st.session_state.mode == 'full':
        st.session_state.shuffled_indices = random.sample(available_indices, min(30, len(available_indices)))

    elif st.session_state.mode == 'review':
        with open(f"quiz_wrong_{st.session_state.user_id}.json", 'r', encoding='utf-8') as f:
            st.session_state.shuffled_indices = json.load(f)
        random.shuffle(st.session_state.shuffled_indices)

    st.session_state.q_index = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.answers = []
    st.session_state.start_time = time.time()

# ====== 測驗畫面 ======
st.title("🧠 AI 考題小測驗遊戲")
total = len(st.session_state.shuffled_indices)

if st.session_state.q_index < total:
    idx = st.session_state.shuffled_indices[st.session_state.q_index]
    row = df.iloc[idx]

    qtype = str(row.get("type", "single")).strip()
    correct_key = parse_answer(row.get("answer", ""), qtype)
    options = get_options(row)

    st.markdown(f"**第 {st.session_state.q_index + 1} 題 / {total}**\n\n{row['question']}")

    with st.sidebar:
        st.markdown("📊 測驗進度")
        progress = (st.session_state.q_index + 1) / total
        st.progress(progress)
        st.caption(f"📘 剩下 {total - st.session_state.q_index - 1} 題")

    # ====== 依 type 顯示 UI ======
    user_answer = None

    if qtype == "single":
        # 顯示選項文字
        for k, v in options.items():
            st.write(f"{k}. {v}")
        user_answer = st.radio("請選擇答案：", list(options.keys()), key=f"single_{idx}")

    elif qtype == "multiple":
        for k, v in options.items():
            st.write(f"{k}. {v}")
        user_answer = st.multiselect("請選擇答案（可複選）：", list(options.keys()), key=f"multi_{idx}")

    elif qtype == "matching":
        # correct_key 是 dict，例如 {"1":"B","2":"D"...}
        st.info("配對題：請為每個左側項目選擇對應的右側答案（用下拉選單模擬拖曳配對）")
        left_keys = list(correct_key.keys())
        right_choices = sorted(list(set(correct_key.values())))

        user_map = {}
        for lk in left_keys:
            user_map[lk] = st.selectbox(f"{lk} 對應到：", [""] + right_choices, key=f"match_{idx}_{lk}")
        user_answer = user_map

    elif qtype == "ordering":
        st.info("排序題：請依順序選擇每一個位置的項目（用下拉選單模擬拖曳排序）")
        correct_seq = correct_key[:]  # list
        user_seq = []
        for i in range(len(correct_seq)):
            pick = st.selectbox(f"第 {i+1} 個：", [""] + correct_seq, key=f"order_{idx}_{i}")
            user_seq.append(pick)
        user_answer = user_seq

    else:
        st.warning(f"⚠️ 未支援的題型：{qtype}（暫用文字輸入）")
        user_answer = st.text_input("請輸入答案：", key=f"other_{idx}")

    # ====== 提交 ======
    if not st.session_state.answered:
        if st.button("✅ 確認答案"):
            elapsed = round(time.time() - st.session_state.start_time, 2)
            correct = is_correct(user_answer, correct_key, qtype)
            st.session_state.answered = True

            # ✅ 紀錄完成題號（依 id）
            done_ids.add(int(row['id']))
            with open(done_path, 'w', encoding='utf-8') as f:
                json.dump(list(done_ids), f, ensure_ascii=False)

            # ✅ 分數 / 錯題本
            if correct:
                st.session_state.score += 1
                if st.session_state.mode == 'review':
                    wrong_path = f"quiz_wrong_{st.session_state.user_id}.json"
                    if os.path.exists(wrong_path):
                        with open(wrong_path, 'r', encoding='utf-8') as f:
                            wrong_indices = json.load(f)
                        if idx in wrong_indices:
                            wrong_indices.remove(idx)
                            with open(wrong_path, 'w', encoding='utf-8') as f:
                                json.dump(wrong_indices, f, ensure_ascii=False)

            # 如果是 full 模式答錯，最後才會整理存 wrong；這裡照你原邏輯不立即寫

            st.session_state.answers.append({
                "題號": st.session_state.q_index + 1,
                "題型": qtype,
                "題目": row['question'],
                "你的答案": str(user_answer),
                "正確答案": format_correct_answer_for_show(correct_key, qtype),
                "是否正確": "✅ 正確" if correct else "❌ 錯誤",
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
            st.session_state.start_time = time.time()
            st.rerun()

else:
    st.balloons()
    st.subheader(f"🎉 測驗結束！你總共答對了 {st.session_state.score} / {total} 題")

    if st.session_state.mode == 'full':
        wrong_indices = []
        for i, a in enumerate(st.session_state.answers):
            if a['是否正確'] != '✅ 正確':
                wrong_indices.append(st.session_state.shuffled_indices[i])

        with open(f"quiz_wrong_{st.session_state.user_id}.json", 'w', encoding='utf-8') as f:
            json.dump(wrong_indices, f, ensure_ascii=False)

        # ✅ 完成題庫才記入排行榜（新版：len(df) 可能不只 94，直接用 len(df)）
        if len(done_ids) == len(df):
            leaderboard_path = "leaderboard.json"
            record = {
                "user": st.session_state.user_id,
                "score": st.session_state.score,
                "total": total,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            if os.path.exists(leaderboard_path):
                with open(leaderboard_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = []
            data.append(record)
            with open(leaderboard_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        else:
            st.warning(f"⚠️ 尚未完成全部題庫（共 {len(df)} 題），完成後才會記入排行榜！")

    # 顯示作答紀錄
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
