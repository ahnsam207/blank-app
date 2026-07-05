import base64
import io
import math
import random
import time
import wave

import pandas as pd
import streamlit as st

st.set_page_config(page_title="영어 단어 뜻 맞추기 게임", layout="centered")

PASTEL_BG = "#f8eefb"
CARD_BG = "#fff7fd"
BUTTON_BG = "#f1d9ff"
TEXT_COLOR = "#5c3a72"

STYLE = f"""
<style>
body {{ background: {PASTEL_BG}; }}
section.main {{ background: transparent; }}
.game-header {{ background: {CARD_BG}; border: 2px dashed #f5d2ff; border-radius: 28px; padding: 22px; text-align: center; color: {TEXT_COLOR}; margin-bottom: 18px; }}
.word-card {{ background: #fff2fd; border-radius: 30px; border: 2px solid #fad6ff; padding: 28px; margin: 16px 0; box-shadow: 0 16px 28px rgba(126, 63, 155, 0.08); }}
.falling-board {{ background: #fff4fc; border: 2px dashed #f5d2ff; border-radius: 32px; padding: 18px; min-height: 260px; position: relative; overflow: hidden; }}
.falling-word {{ background: #ffe9fb; border: 1px dashed #f7c8ff; border-radius: 999px; color: {TEXT_COLOR}; padding: 14px 22px; margin: 10px 0; display: inline-block; font-weight: 800; letter-spacing: 0.03em; animation: drop 5s linear forwards; }}
@keyframes drop {{
  0% {{ transform: translateY(0); opacity: 1; }}
  100% {{ transform: translateY(260px); opacity: 0; }}
}}
.success-box {{ background: #dff8f2; border-radius: 20px; padding: 16px; color: #1f644d; font-weight: 700; border: 1px solid #c9f0e0; margin-top: 12px; }}
.failure-box {{ background: #ffe5eb; border-radius: 20px; padding: 16px; color: #8d2740; font-weight: 700; border: 1px solid #ffccd7; margin-top: 12px; }}
.combo-message {{ background: #fff6d8; border-radius: 20px; padding: 16px; color: #8a5c2b; font-weight: 700; border: 1px solid #ffe8a8; margin-top: 14px; }}
</style>
"""

st.markdown(STYLE, unsafe_allow_html=True)


def generate_tone(frequency=440, duration=0.2, volume=0.35, sample_rate=44100):
    frame_count = int(sample_rate * duration)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for i in range(frame_count):
            value = int(volume * 32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
            wav_file.writeframesraw(value.to_bytes(2, byteorder="little", signed=True))
    return buf.getvalue()


def generate_fanfare():
    notes = [660, 740, 880]
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(44100)
        for freq in notes:
            duration = 0.16
            frame_count = int(44100 * duration)
            for i in range(frame_count):
                value = int(0.33 * 32767.0 * math.sin(2.0 * math.pi * freq * i / 44100))
                wav_file.writeframesraw(value.to_bytes(2, byteorder="little", signed=True))
    return buf.getvalue()


def play_audio(sound_bytes):
    sound_b64 = base64.b64encode(sound_bytes).decode()
    st.markdown(
        f"<audio autoplay><source src=\"data:audio/wav;base64,{sound_b64}\" type=\"audio/wav\" /></audio>",
        unsafe_allow_html=True,
    )


def load_wordbook(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, header=None, engine="openpyxl")
    except Exception:
        return []

    entries = []
    for _, row in df.iterrows():
        word = str(row.iloc[0]).strip() if not pd.isna(row.iloc[0]) else ""
        if not word:
            continue
        meanings = [str(val).strip() for val in row.iloc[1:] if not pd.isna(val) and str(val).strip()]
        if not meanings:
            continue
        entries.append({"word": word, "meanings": meanings})
    return entries


def init_game(entries):
    questions = []
    for entry in entries:
        questions.append({
            "word": entry["word"],
            "meaning": random.choice(entry["meanings"]),
        })
    random.shuffle(questions)
    st.session_state.questions = questions
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.failures = 0
    st.session_state.combo = 0
    st.session_state.question_done = False
    st.session_state.feedback = ""
    st.session_state.combo_message = ""
    st.session_state.combo_time = 0
    st.session_state.start_time = time.time()
    st.session_state.question_start = time.time()
    st.session_state.finished = False
    st.session_state.total_time = len(questions) * 5
    st.session_state.fanfare_played = False
    st.session_state.penalty_played = False


def create_options(correct_word, entries):
    wrong_words = [entry["word"] for entry in entries if entry["word"] != correct_word]
    options = random.sample(wrong_words, min(3, len(wrong_words))) + [correct_word]
    random.shuffle(options)
    return options


uploaded_file = st.file_uploader("엑셀 영어 단어장 선택", type=["xlsx"])

if uploaded_file:
    if (
        "uploaded_name" not in st.session_state
        or st.session_state.uploaded_name != uploaded_file.name
        or "questions" not in st.session_state
    ):
        entries = load_wordbook(uploaded_file)
        if entries:
            st.session_state.uploaded_name = uploaded_file.name
            st.session_state.entries = entries
            init_game(entries)
        else:
            st.warning("단어장 파일을 읽을 수 없습니다. 첫 번째 열은 영어 단어, 두 번째 열 이후에는 한글 뜻이 있어야 합니다.")

if "questions" not in st.session_state or not st.session_state.questions:
    st.info("엑셀 파일을 선택해서 게임을 시작하세요. 1열은 영어 단어, 2열부터는 한글 뜻이 입력되어야 합니다.")
    st.stop()

if st.session_state.finished:
    st.header("게임 종료")
    st.subheader(f"최종 점수: {st.session_state.score}")
    st.write(f"오답 횟수: {st.session_state.failures} / 3")
    if st.button("다시 시작하기"):
        init_game(st.session_state.entries)
    st.stop()

elapsed_since_start = int(time.time() - st.session_state.start_time)
if elapsed_since_start >= st.session_state.total_time:
    st.session_state.finished = True
    st.experimental_rerun()

current_question = st.session_state.questions[st.session_state.current_index]
correct_word = current_question["word"]
current_meaning = current_question["meaning"]
options = create_options(correct_word, st.session_state.entries)
question_elapsed = time.time() - st.session_state.question_start

if not st.session_state.question_done and question_elapsed >= 5:
    st.session_state.score -= 1
    st.session_state.failures += 1
    st.session_state.combo = 0
    st.session_state.question_done = True
    st.session_state.feedback = f"⏰ 시간이 다 되었어요! 정답은 {correct_word} 입니다. -1점"
    if st.session_state.failures >= 3:
        st.session_state.finished = True
    st.experimental_rerun()

st.markdown(
    "<div class='game-header'><h1>영어 단어 뜻 맞추기 게임</h1><p>중앙에 보이는 한글 뜻에 맞는 영어 단어를 선택하세요.</p></div>",
    unsafe_allow_html=True,
)

cols = st.columns([1, 2, 1])
with cols[1]:
    st.markdown(
        f"<div class='word-card'><h2 style='margin:0;'>{current_meaning}</h2><p style='margin:2px 0 0 0; color:#8a5da1;'>아래 단어들이 5초 동안 내려옵니다.</p></div>",
        unsafe_allow_html=True,
    )

st.markdown("<div class='falling-board'>", unsafe_allow_html=True)
for word in options:
    st.markdown(f"<div class='falling-word'>{word}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

status_cols = st.columns(3)
status_cols[0].markdown(f"**점수**<br><span style='font-size:22px;'>{st.session_state.score}</span>")
status_cols[1].markdown(f"**연속 정답**<br><span style='font-size:22px;'>{st.session_state.combo}</span>")
status_cols[2].markdown(f"**남은 시간**<br><span style='font-size:22px;'>{max(0, st.session_state.total_time - elapsed_since_start)}초</span>")

if st.session_state.question_done:
    if "fanfare_played" not in st.session_state:
        st.session_state.fanfare_played = False
    if "penalty_played" not in st.session_state:
        st.session_state.penalty_played = False

    if "정답" in st.session_state.feedback and not st.session_state.fanfare_played:
        play_audio(generate_fanfare())
        st.session_state.fanfare_played = True
    if "-1점" in st.session_state.feedback and not st.session_state.penalty_played:
        play_audio(generate_tone(220, 0.28, 0.3))
        st.session_state.penalty_played = True

    if "정답" in st.session_state.feedback:
        st.markdown(f"<div class='success-box'>{st.session_state.feedback}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='failure-box'>{st.session_state.feedback}</div>", unsafe_allow_html=True)

    if st.session_state.combo_message and time.time() - st.session_state.combo_time < 2:
        st.markdown(f"<div class='combo-message'>{st.session_state.combo_message}</div>", unsafe_allow_html=True)
    elif time.time() - st.session_state.combo_time >= 2:
        st.session_state.combo_message = ""

    if st.session_state.failures >= 3:
        st.success("3번 틀려서 게임이 종료되었습니다.")
        if st.button("다시 시작하기"):
            init_game(st.session_state.entries)
    else:
        if st.button("다음 문제로"):
            st.session_state.current_index += 1
            st.session_state.question_done = False
            st.session_state.feedback = ""
            st.session_state.fanfare_played = False
            st.session_state.penalty_played = False
            st.session_state.question_start = time.time()
            if st.session_state.current_index >= len(st.session_state.questions):
                st.session_state.finished = True
            st.experimental_rerun()
else:
    btn_cols = st.columns(2)
    for idx, word in enumerate(options):
        if btn_cols[idx % 2].button(word, key=f"choice_{st.session_state.current_index}_{idx}", disabled=st.session_state.question_done):
            if word == correct_word:
                st.session_state.score += 1
                st.session_state.combo += 1
                st.session_state.feedback = f"🎉 정답입니다! +1점"
                st.session_state.question_done = True
                st.session_state.fanfare_played = False
                st.session_state.penalty_played = False
                if st.session_state.combo >= 5:
                    st.session_state.combo_message = random.choice(["Good Job", "Excellent", "You are Genius"])
                    st.session_state.combo_time = time.time()
                    st.session_state.combo = 0
            else:
                st.session_state.score -= 1
                st.session_state.failures += 1
                st.session_state.combo = 0
                st.session_state.feedback = f"❌ 오답입니다. 정답은 {correct_word} 입니다. -1점"
                st.session_state.question_done = True
                st.session_state.fanfare_played = False
                st.session_state.penalty_played = False
                if st.session_state.failures >= 3:
                    st.session_state.finished = True
            st.experimental_rerun()

if st.session_state.finished:
    st.success("게임이 종료되었습니다. 다시 시작하려면 버튼을 눌러주세요.")
    if st.button("다시 시작하기"):
        init_game(st.session_state.entries)
    st.stop()
