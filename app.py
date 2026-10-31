import streamlit as st
from schemas import IncomingTicket, Message, build_response

st.set_page_config(page_title="BomzhAI")
st.title("BomzhAI: разбор обращений")

kind = st.selectbox("Тип обращения", ["complaint", "report"])
text = st.text_area("Текст обращения игрока", height=160)
nick = st.text_input("Ник нарушителя (если известен)")
attachments = st.number_input("Количество вложений", min_value=0, value=0)

if st.button("Разобрать"):
    if not text.strip():
        st.error("Введите текст обращения")
    else:
        ticket = IncomingTicket(
            kind=kind,
            messages=[Message(role="player", text=text)],
            reported_nick=nick or None,
            images_count=int(attachments),
        )
        result = build_response(ticket)
        st.subheader("Черновик ответа")
        st.write(result.draft_reply.text)
        if result.needs_human:
            st.warning("Нужен человек: " + "; ".join(result.reasons))
        else:
            st.success("Можно отвечать автоматически")
        st.json(result.model_dump())
