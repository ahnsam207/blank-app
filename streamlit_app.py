import random

import streamlit as st

st.set_page_config(page_title="영어 단어 맞추기 게임", layout="centered")

VOCABULARY = {
    "apple": "사과",
    "book": "책",
    "cat": "고양이",
    "dog": "강아지",
    "happy": "행복한",
    "water": "물",
    "school": "학교",
    "sun": "태양",
    "music": "음악",
    "friend": "친구",
}

if "questions" not in st.session_state:
    words = list(VOCABULARY.items())
    random.shuffle(words)
    st.session_state.questions = words
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.feedback = ""
    st.session_state.selected = None
    st.session_state.finished = False

st.title("🇬🇧 영어 단어 뜻 맞추기 게임")
st.write("영어 단어가 나옵니다. 가장 알맞은 한글 뜻을 골라보세요.")

if st.session_state.finished:
    st.success("게임 종료! 수고하셨어요.")
    st.write(f"최종 점수: **{st.session_state.score} / {len(st.session_state.questions)}**")
    if st.button("다시 시작하기"):
        st.session_state.questions = random.sample(list(VOCABULARY.items()), len(VOCABULARY))
        st.session_state.index = 0
        st.session_state.score = 0
        st.session_state.feedback = ""
        st.session_state.selected = None
        st.session_state.finished = False
    st.stop()

current_word, correct_meaning = st.session_state.questions[st.session_state.index]

options = [correct_meaning] + random.sample(
    [meaning for word, meaning in VOCABULARY.items() if meaning != correct_meaning], 3
)
random.shuffle(options)

st.markdown(f"### 문제 {st.session_state.index + 1} / {len(st.session_state.questions)}")
st.markdown(f"**{current_word}**")

st.session_state.selected = st.radio("뜻을 선택하세요", options, index=0)

if st.button("제출" ):
    if st.session_state.selected == correct_meaning:
        st.session_state.feedback = "✅ 정답입니다!"
        st.session_state.score += 1
    else:
        st.session_state.feedback = f"❌ 오답입니다. 정답은 **{correct_meaning}** 입니다."

    st.session_state.index += 1
    if st.session_state.index >= len(st.session_state.questions):
        st.session_state.finished = True
    else:
        st.experimental_rerun()

if st.session_state.feedback:
    st.info(st.session_state.feedback)
    st.write(f"현재 점수: **{st.session_state.score}**")
