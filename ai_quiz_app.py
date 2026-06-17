import streamlit as st
import pandas as pd
import time
from datetime import datetime
import random
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "final_exam_questions_with_images.csv")

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
total_questions = len(df)


def parse_answer(answer: str, qtype: str):
    answer = (str(answer) if answer is not None else "").strip().upper()

    if qtype == "single":
        found = re.findall(r"[A-F]", answer)
        return found[0] if found else answer

    if qtype == "multiple":
        return set(re.findall(r"[A-F]", answer))

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
        return set(user_answer) == set(correct_key)

    return str(user_answer).strip() == str(correct_key).strip()


def format_correct_answer_for_show(correct_key, qtype):
    if qtype == "multiple":
        return "、".join(sorted(list(correct_key)))
    return str(correct_key)


def safe_load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def safe_save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def show_question_image(row):
    image_path = str(row.get("image_path", "")).strip()

    if not image_path or image_path.lower() == "nan":
        return

    full_path = os.path.join(BASE_DIR, image_path)

    if os.path.exists(full_path):
        st.image(full_path, use_container_width=True)
    else:
        st.warning(f"找不到圖片：{image_path}")


if "mode" not in st.session_state:
    st.session_state.mode = None
if "user_id" not in st.session_state:
    st.session_state.user_id = ""


# ====== 登入 ======
if not st.session_state.user_id:
    st.title("🔐 請輸入暱稱開始測驗")
    nickname = st.text_input("請輸入你的暱稱：")

    if st.button("✅ 開始測驗") and nickname.strip():
        st.session_state.user_id = nickname.strip()
        st.rerun()

    st.stop()


# ====== 完成進度 ======
done_path = os.path.join(BASE_DIR, f"quiz_done_{st.session_state.user_id}.json")
done_ids = set(map(str, safe_load_json(done_path, [])))

st.sidebar.info(f"📚 題庫完成進度：{len(done_ids)} / {len(df)} 題")


# ====== 選擇模式 ======
if not st.session_state.mode:
    st.title("📘 請選擇模式")

    if st.button("✅ 完整測驗"):
        st.session_state.mode = "full"
        st.rerun()

    wrong_path = os.path.join(BASE_DIR, f"quiz_wrong_{st.session_state.user_id}.json")
    if os.path.exists(wrong_path):
        if st.button("🧠 錯題複習"):
            st.session_state.mode = "review"
            st.rerun()

    if st.button("🏆 查看排行榜"):
        st.session_state.mode = "leaderboard"
        st.rerun()

    st.stop()


# ====== 排行榜 ======
if st.session_state.mode == "leaderboard":
    st.title("🏆 排行榜")

    leaderboard_path = os.path.join(BASE_DIR, "leaderboard.json")
    leaderboard = safe_load_json(leaderboard_path, [])

    if leaderboard:
        df_leaderboard = pd.DataFrame(leaderboard)
        df_leaderboard = df_leaderboard.sort_values(by="score", ascending=False).head(10)
        st.dataframe(df_leaderboard, use_container_width=True)
    else:
        st.info("目前還沒有任何人上榜，快來挑戰吧！")

    if st.button("🔙 回主畫面"):
        st.session_state.mode = None
        st.rerun()

    st.stop()


# ====== 初始化題目 ======
if "shuffled_indices" not in st.session_state:
    available_indices = [
        i for i in range(total_questions)
        if str(df.iloc[i]["id"]) not in done_ids
    ]

    if st.session_state.mode == "full":
        st.session_state.shuffled_indices = random.sample(
            available_indices,
            min(30, len(available_indices))
        )

    elif st.session_state.mode == "review":
        wrong_path = os.path.join(BASE_DIR, f"quiz_wrong_{st.session_state.user_id}.json")
        st.session_state.shuffled_indices = safe_load_json(wrong_path, [])
        random.shuffle(st.session_state.shuffled_indices)

    st.session_state.q_index = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.answers = []
    st.session_state.start_time = time.time()


# ====== 測驗畫面 ======
st.title("🧠 AI 考題小測驗遊戲")

total = len(st.session_state.shuffled_indices)

if total == 0:
    st.success("🎉 目前沒有可作答的題目。")
    if st.button("🔁 回主畫面"):
        st.session_state.clear()
        st.rerun()
    st.stop()


if st.session_state.q_index < total:
    idx = st.session_state.shuffled_indices[st.session_state.q_index]
    row = df.iloc[idx]

    qtype = str(row.get("type", "single")).strip().lower()
    correct_key = parse_answer(row.get("answer", ""), qtype)
    options = get_options(row)

    st.markdown(
        f"**第 {st.session_state.q_index + 1} 題 / {total}**\n\n"
        f"{row['question']}"
    )

    show_question_image(row)

    with st.sidebar:
        st.markdown("📊 測驗進度")
        progress = (st.session_state.q_index + 1) / total
        st.progress(progress)
        st.caption(f"📘 剩下 {total - st.session_state.q_index - 1} 題")

    user_answer = None

    if qtype == "single":
        for k, v in options.items():
            st.write(f"{k}. {v}")

        user_answer = st.radio(
            "請選擇答案：",
            list(options.keys()),
            key=f"single_{idx}"
        )

    elif qtype == "multiple":
        for k, v in options.items():
            st.write(f"{k}. {v}")

        user_answer = st.multiselect(
            "請選擇答案（可複選）：",
            list(options.keys()),
            key=f"multi_{idx}"
        )

    else:
        st.warning(f"⚠️ 未支援的題型：{qtype}，暫用文字輸入。")
        user_answer = st.text_input("請輸入答案：", key=f"other_{idx}")

    if not st.session_state.answered:
        if st.button("✅ 確認答案"):
            elapsed = round(time.time() - st.session_state.start_time, 2)
            correct = is_correct(user_answer, correct_key, qtype)

            st.session_state.answered = True

            done_ids.add(str(row["id"]))
            safe_save_json(done_path, sorted(list(done_ids)))

            if correct:
                st.session_state.score += 1

                if st.session_state.mode == "review":
                    wrong_path = os.path.join(BASE_DIR, f"quiz_wrong_{st.session_state.user_id}.json")
                    wrong_indices = safe_load_json(wrong_path, [])

                    if idx in wrong_indices:
                        wrong_indices.remove(idx)
                        safe_save_json(wrong_path, wrong_indices)

            st.session_state.answers.append({
                "題號": st.session_state.q_index + 1,
                "題型": qtype,
                "題目": row["question"],
                "你的答案": "、".join(user_answer) if isinstance(user_answer, list) else str(user_answer),
                "正確答案": format_correct_answer_for_show(correct_key, qtype),
                "是否正確": "✅ 正確" if correct else "❌ 錯誤",
                "時間戳記": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "耗時（秒）": elapsed
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

    if st.session_state.mode == "full":
        wrong_indices = []

        for i, a in enumerate(st.session_state.answers):
            if a["是否正確"] != "✅ 正確":
                wrong_indices.append(st.session_state.shuffled_indices[i])

        wrong_path = os.path.join(BASE_DIR, f"quiz_wrong_{st.session_state.user_id}.json")
        safe_save_json(wrong_path, wrong_indices)

        if len(done_ids) == len(df):
            leaderboard_path = os.path.join(BASE_DIR, "leaderboard.json")

            record = {
                "user": st.session_state.user_id,
                "score": st.session_state.score,
                "total": total,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            leaderboard = safe_load_json(leaderboard_path, [])
            leaderboard.append(record)
            safe_save_json(leaderboard_path, leaderboard)

        else:
            st.warning(f"⚠️ 尚未完成全部題庫（共 {len(df)} 題），完成後才會記入排行榜！")

    st.markdown(f"## 🧾 {st.session_state.user_id} 的答題紀錄")

    df_result = pd.DataFrame(st.session_state.answers)
    st.dataframe(df_result, use_container_width=True)

    csv = df_result.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 下載作答紀錄 CSV",
        data=csv,
        file_name=f"{st.session_state.user_id}_quiz_result.csv",
        mime="text/csv"
    )

    if st.button("🔁 再玩一次"):
        st.session_state.clear()
        st.rerun()

    wrong_path = os.path.join(BASE_DIR, f"quiz_wrong_{st.session_state.user_id}.json")
    if os.path.exists(wrong_path):
        if st.button("🗑️ 清除錯題紀錄"):
            os.remove(wrong_path)
            st.success("✅ 錯題紀錄已刪除！")
            st.rerun()
