import streamlit as st
import pandas as pd
import time
from datetime import datetime
import random
import json
import os
import re

# ====== 題庫載入 ======
# 你的 CSV 需要至少有：id, question, option_A~option_F, answer, type
# 如果你檔名不同，改這一行即可。
QUESTION_FILE = "final_exam_questions_ch1_2_3_10_15_17.csv"
df = pd.read_csv(QUESTION_FILE, encoding="utf-8-sig")
total_questions = len(df)

# ====== 工具函式 ======
def normalize_qtype(row):
    """避免 CSV type 大小寫或空白造成判斷錯誤。"""
    qtype = str(row.get("type", "single")).strip().lower()
    answer = str(row.get("answer", "")).strip().upper()

    if qtype in ["multi", "multiple", "多選"]:
        return "multiple"
    if qtype in ["single", "單選"]:
        # 保險：如果答案有兩個以上字母，就自動當多選
        letters = re.findall(r"[A-F]", answer)
        return "multiple" if len(letters) >= 2 else "single"
    if qtype in ["matching", "配對"]:
        return "matching"
    if qtype in ["ordering", "排序"]:
        return "ordering"

    letters = re.findall(r"[A-F]", answer)
    return "multiple" if len(letters) >= 2 else "single"


def parse_answer(answer: str, qtype: str):
    answer = (str(answer) if answer is not None else "").strip()

    if qtype == "single":
        letters = re.findall(r"[A-F]", answer.upper())
        return letters[0] if letters else answer

    if qtype == "multiple":
        # 支援 A,C,F / A、C、F / ACF
        return set(re.findall(r"[A-F]", answer.upper()))

    if qtype == "matching":
        pairs = {}
        for part in re.split(r"[;；]\s*", answer):
            if "->" in part:
                left, right = [x.strip() for x in part.split("->", 1)]
                if left and right:
                    pairs[left] = right
        return pairs

    if qtype == "ordering":
        return [x.strip() for x in answer.split("->") if x.strip()]

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
        if not isinstance(user_answer, dict) or not isinstance(correct_key, dict):
            return False
        for k, v in correct_key.items():
            if str(user_answer.get(k, "")).strip() != str(v).strip():
                return False
        return True

    if qtype == "ordering":
        if not isinstance(user_answer, list) or not isinstance(correct_key, list):
            return False
        ua = [str(x).strip() for x in user_answer if str(x).strip()]
        return ua == correct_key

    return str(user_answer).strip() == str(correct_key).strip()


def format_correct_answer_for_show(correct_key, qtype):
    if qtype == "single":
        return str(correct_key)
    if qtype == "multiple":
        return "、".join(sorted(list(correct_key)))
    if qtype == "matching":
        return "、".join([f"{k}->{v}" for k, v in correct_key.items()])
    if qtype == "ordering":
        return "->".join(correct_key)
    return str(correct_key)


def format_user_answer_for_show(user_answer, qtype):
    if qtype == "multiple":
        return "、".join(sorted(list(user_answer)))
    if qtype == "matching":
        return "、".join([f"{k}->{v}" for k, v in user_answer.items()])
    if qtype == "ordering":
        return "->".join(user_answer)
    return str(user_answer)


def row_id(row):
    return str(row["id"])


def reset_quiz_state(keep_user=True):
    user_id = st.session_state.get("user_id", "")
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    if keep_user:
        st.session_state.user_id = user_id
        st.session_state.mode = None


def show_question_content(row, show_answer=False):
    qtype = normalize_qtype(row)
    correct_key = parse_answer(row.get("answer", ""), qtype)
    options = get_options(row)

    st.markdown(str(row["question"]))

    # 如果你的 CSV 有 image_path 欄位，且圖片檔存在，就顯示圖片
    image_path = row.get("image_path")
    if pd.notna(image_path) and str(image_path).strip() and os.path.exists(str(image_path).strip()):
        st.image(str(image_path).strip(), use_container_width=True)

    for k, v in options.items():
        if show_answer:
            if qtype == "single" and k == correct_key:
                st.success(f"{k}. {v}")
            elif qtype == "multiple" and k in correct_key:
                st.success(f"{k}. {v}")
            else:
                st.write(f"{k}. {v}")
        else:
            st.write(f"{k}. {v}")

    if show_answer:
        st.info(f"✅ 正確答案：{format_correct_answer_for_show(correct_key, qtype)}")
        st.caption(f"題型：{qtype}")


# ====== 初始化狀態 ======
if "mode" not in st.session_state:
    st.session_state.mode = None
if "user_id" not in st.session_state:
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
    with open(done_path, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False)

with open(done_path, "r", encoding="utf-8") as f:
    done_ids = set(str(x) for x in json.load(f))

single_count = sum(normalize_qtype(df.iloc[i]) == "single" for i in range(total_questions))
multiple_count = sum(normalize_qtype(df.iloc[i]) == "multiple" for i in range(total_questions))

st.sidebar.info(f"📚 題庫完成進度：{len(done_ids)} / {len(df)} 題")
st.sidebar.caption(f"🔵 單選：{single_count} 題｜🟡 多選：{multiple_count} 題")

# ====== 選擇模式 ======
if not st.session_state.mode:
    st.title("📘 請選擇模式")
    st.caption("測驗模式現在不限制 30 題，會一次考完該模式全部題目。")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"📚 全部題目測驗（{len(df)} 題）", use_container_width=True):
            st.session_state.mode = "full"
            st.rerun()
        if st.button(f"🔵 單選題測驗（{single_count} 題）", use_container_width=True):
            st.session_state.mode = "single"
            st.rerun()
        if st.button(f"🟡 多選題測驗（{multiple_count} 題）", use_container_width=True):
            st.session_state.mode = "multiple"
            st.rerun()

    with col2:
        if st.button("📖 答案快速複習", use_container_width=True):
            st.session_state.mode = "study"
            st.rerun()
        if os.path.exists(f"quiz_wrong_{st.session_state.user_id}.json"):
            if st.button("🧠 錯題測驗", use_container_width=True):
                st.session_state.mode = "review"
                st.rerun()
            if st.button("📖 錯題答案複習", use_container_width=True):
                st.session_state.mode = "wrong_study"
                st.rerun()
        if st.button("🏆 查看排行榜", use_container_width=True):
            st.session_state.mode = "leaderboard"
            st.rerun()

    if st.button("🚪 更換暱稱"):
        reset_quiz_state(keep_user=False)
        st.rerun()

    st.stop()

# ====== 排行榜 ======
if st.session_state.mode == "leaderboard":
    st.title("🏆 排行榜")
    if os.path.exists("leaderboard.json"):
        with open("leaderboard.json", "r", encoding="utf-8") as f:
            leaderboard = json.load(f)
        df_leaderboard = pd.DataFrame(leaderboard)
        if len(df_leaderboard) > 0:
            df_leaderboard = df_leaderboard.sort_values(by="score", ascending=False).head(10)
            st.dataframe(df_leaderboard, use_container_width=True)
        else:
            st.info("目前還沒有任何人上榜，快來挑戰吧！")
    else:
        st.info("目前還沒有任何人上榜，快來挑戰吧！")

    if st.button("🔙 回主畫面"):
        st.session_state.mode = None
        st.rerun()
    st.stop()

# ====== 答案快速複習模式 ======
if st.session_state.mode in ["study", "wrong_study"]:
    if st.session_state.mode == "study":
        st.title("📖 全部題庫答案快速複習")
        study_indices = list(range(total_questions))
    else:
        st.title("📖 錯題答案快速複習")
        wrong_path = f"quiz_wrong_{st.session_state.user_id}.json"
        if os.path.exists(wrong_path):
            with open(wrong_path, "r", encoding="utf-8") as f:
                study_indices = json.load(f)
        else:
            study_indices = []

    if not study_indices:
        st.info("目前沒有可以複習的題目。")
    else:
        qtype_filter = st.radio(
            "篩選題型：",
            ["全部", "單選", "多選"],
            horizontal=True
        )
        keyword = st.text_input("搜尋題目關鍵字（可不填）：")

        for no, idx in enumerate(study_indices, 1):
            row = df.iloc[idx]
            qtype = normalize_qtype(row)

            if qtype_filter == "單選" and qtype != "single":
                continue
            if qtype_filter == "多選" and qtype != "multiple":
                continue
            if keyword and keyword.lower() not in str(row["question"]).lower():
                continue

            with st.expander(f"第 {idx + 1} 題｜{qtype}｜答案：{row.get('answer', '')}"):
                show_question_content(row, show_answer=True)

    if st.button("🔙 回主畫面"):
        st.session_state.mode = None
        st.rerun()
    st.stop()

# ====== 初始化測驗題目 ======
if "shuffled_indices" not in st.session_state:
    available_indices = [i for i in range(total_questions) if row_id(df.iloc[i]) not in done_ids]

    if st.session_state.mode == "full":
        st.session_state.shuffled_indices = available_indices

    elif st.session_state.mode == "single":
        st.session_state.shuffled_indices = [
            i for i in available_indices
            if normalize_qtype(df.iloc[i]) == "single"
        ]

    elif st.session_state.mode == "multiple":
        st.session_state.shuffled_indices = [
            i for i in available_indices
            if normalize_qtype(df.iloc[i]) == "multiple"
        ]

    elif st.session_state.mode == "review":
        wrong_path = f"quiz_wrong_{st.session_state.user_id}.json"
        if os.path.exists(wrong_path):
            with open(wrong_path, "r", encoding="utf-8") as f:
                st.session_state.shuffled_indices = json.load(f)
        else:
            st.session_state.shuffled_indices = []

    else:
        st.session_state.shuffled_indices = available_indices

    random.shuffle(st.session_state.shuffled_indices)

    st.session_state.q_index = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.answers = []
    st.session_state.start_time = time.time()

# ====== 測驗畫面 ======
mode_title = {
    "full": "📚 全部題目測驗",
    "single": "🔵 單選題測驗",
    "multiple": "🟡 多選題測驗",
    "review": "🧠 錯題測驗",
}.get(st.session_state.mode, "🧠 AI 考題小測驗遊戲")

st.title(mode_title)
total = len(st.session_state.shuffled_indices)

if total == 0:
    st.warning("這個模式目前沒有可考題目。可能你已經完成這類題目，或錯題本是空的。")
    if st.button("🔙 回主畫面"):
        st.session_state.mode = None
        if "shuffled_indices" in st.session_state:
            del st.session_state.shuffled_indices
        st.rerun()
    st.stop()

if st.session_state.q_index < total:
    idx = st.session_state.shuffled_indices[st.session_state.q_index]
    row = df.iloc[idx]

    qtype = normalize_qtype(row)
    correct_key = parse_answer(row.get("answer", ""), qtype)
    options = get_options(row)

    st.markdown(f"**第 {st.session_state.q_index + 1} 題 / {total}**")
    show_question_content(row, show_answer=False)

    with st.sidebar:
        st.markdown("📊 測驗進度")
        progress = (st.session_state.q_index + 1) / total
        st.progress(progress)
        st.caption(f"📘 剩下 {total - st.session_state.q_index - 1} 題")

    user_answer = None

    if qtype == "single":
        user_answer = st.radio("請選擇答案：", list(options.keys()), key=f"single_{idx}")

    elif qtype == "multiple":
        user_answer = st.multiselect("請選擇答案（可複選）：", list(options.keys()), key=f"multi_{idx}")

    elif qtype == "matching":
        st.info("配對題：請為每個左側項目選擇對應的右側答案。")
        left_keys = list(correct_key.keys())
        right_choices = sorted(list(set(correct_key.values())))
        user_map = {}
        for lk in left_keys:
            user_map[lk] = st.selectbox(f"{lk} 對應到：", [""] + right_choices, key=f"match_{idx}_{lk}")
        user_answer = user_map

    elif qtype == "ordering":
        st.info("排序題：請依順序選擇每一個位置的項目。")
        correct_seq = correct_key[:]
        user_seq = []
        for i in range(len(correct_seq)):
            pick = st.selectbox(f"第 {i + 1} 個：", [""] + correct_seq, key=f"order_{idx}_{i}")
            user_seq.append(pick)
        user_answer = user_seq

    else:
        st.warning(f"⚠️ 未支援的題型：{qtype}，暫用文字輸入。")
        user_answer = st.text_input("請輸入答案：", key=f"other_{idx}")

    if not st.session_state.answered:
        if st.button("✅ 確認答案"):
            elapsed = round(time.time() - st.session_state.start_time, 2)
            correct = is_correct(user_answer, correct_key, qtype)
            st.session_state.answered = True

            # 紀錄完成題號
            done_ids.add(row_id(row))
            with open(done_path, "w", encoding="utf-8") as f:
                json.dump(list(done_ids), f, ensure_ascii=False)

            if correct:
                st.session_state.score += 1
                if st.session_state.mode == "review":
                    wrong_path = f"quiz_wrong_{st.session_state.user_id}.json"
                    if os.path.exists(wrong_path):
                        with open(wrong_path, "r", encoding="utf-8") as f:
                            wrong_indices = json.load(f)
                        if idx in wrong_indices:
                            wrong_indices.remove(idx)
                            with open(wrong_path, "w", encoding="utf-8") as f:
                                json.dump(wrong_indices, f, ensure_ascii=False)

            st.session_state.answers.append({
                "題號": st.session_state.q_index + 1,
                "原始題號": row_id(row),
                "題型": qtype,
                "題目": row["question"],
                "你的答案": format_user_answer_for_show(user_answer, qtype),
                "正確答案": format_correct_answer_for_show(correct_key, qtype),
                "是否正確": "✅ 正確" if correct else "❌ 錯誤",
                "時間戳記": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "耗時（秒）": elapsed,
            })
            st.rerun()

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

    # full / single / multiple / review 都會更新錯題本
    wrong_indices = []
    for i, a in enumerate(st.session_state.answers):
        if a["是否正確"] != "✅ 正確":
            wrong_indices.append(st.session_state.shuffled_indices[i])

    wrong_path = f"quiz_wrong_{st.session_state.user_id}.json"
    if st.session_state.mode == "review":
        # review 模式中，答對的前面已移除；這裡把仍錯的補回
        if os.path.exists(wrong_path):
            with open(wrong_path, "r", encoding="utf-8") as f:
                old_wrong = json.load(f)
        else:
            old_wrong = []
        merged_wrong = sorted(list(set(old_wrong + wrong_indices)))
        with open(wrong_path, "w", encoding="utf-8") as f:
            json.dump(merged_wrong, f, ensure_ascii=False)
    else:
        with open(wrong_path, "w", encoding="utf-8") as f:
            json.dump(wrong_indices, f, ensure_ascii=False)

    # 完成整份題庫才記入排行榜
    if st.session_state.mode == "full" and len(done_ids) == len(df):
        leaderboard_path = "leaderboard.json"
        record = {
            "user": st.session_state.user_id,
            "score": st.session_state.score,
            "total": total,
            "mode": st.session_state.mode,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if os.path.exists(leaderboard_path):
            with open(leaderboard_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
        data.append(record)
        with open(leaderboard_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    elif st.session_state.mode == "full":
        st.warning(f"⚠️ 尚未完成全部題庫（共 {len(df)} 題），完成後才會記入排行榜！")

    st.markdown(f"## 🧾 {st.session_state.user_id} 的答題紀錄")
    df_result = pd.DataFrame(st.session_state.answers)
    st.dataframe(df_result, use_container_width=True)

    csv = df_result.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 下載作答紀錄 CSV",
        data=csv,
        file_name=f"{st.session_state.user_id}_quiz_result.csv",
        mime="text/csv",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 回主畫面"):
            st.session_state.mode = None
            for key in ["shuffled_indices", "q_index", "score", "answered", "answers", "start_time"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    with col2:
        if st.button("🔄 重新登入 / 再玩一次"):
            reset_quiz_state(keep_user=False)
            st.rerun()

    if os.path.exists(wrong_path):
        if st.button("🗑️ 清除錯題紀錄"):
            os.remove(wrong_path)
            st.success("✅ 錯題紀錄已刪除！")
            st.rerun()
