import streamlit as st
import pandas as pd
import plotly.express as px
from app import generate_sql, run_query

st.set_page_config(page_title="AI SQL Assistant", layout="wide")

# ---------- STYLING ----------
st.markdown("""
<style>
.chat-user {
    background-color: #DCF8C6;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 10px;
}
.chat-assistant {
    background-color: #F1F0F0;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🚀 AI-Powered SQL Assistant")
st.markdown("Convert natural language to SQL and query your AWS data instantly")

# 💡 Optional hint (clean UX)
st.caption("💡 Example: total revenue by customer, top products, sales by country")

# ---------- SESSION ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- DISPLAY CHAT ----------
for i, msg in enumerate(st.session_state.messages):

    if msg["role"] == "user":
        st.markdown(
            f"<div class='chat-user'>💬 {msg['content']}</div>",
            unsafe_allow_html=True
        )

    else:
        st.markdown("<div class='chat-assistant'>", unsafe_allow_html=True)

        st.markdown("**🧠 Generated SQL (Editable)**")

        # Clean SQL display
        clean_sql = msg["sql"].replace("```sql", "").replace("```", "")

        edited_sql = st.text_area(
            label=f"Edit SQL {i}",
            value=clean_sql,
            height=100,
            key=f"sql_edit_{i}"
        )

        if st.button(f"▶️ Run Edited SQL {i}", key=f"run_sql_{i}"):
            result = run_query(edited_sql)
            msg["result"] = result
            msg["sql"] = edited_sql

        st.markdown("**📊 Result**")

        if isinstance(msg["result"], str):
            st.error(msg["result"])
        else:
            df = msg["result"]
            st.dataframe(df)

            # Download CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "⬇️ Download CSV",
                data=csv,
                file_name="query_result.csv",
                mime="text/csv",
                key=f"download_{i}"
            )

            # Chart
            if len(df.columns) >= 2:
                try:
                    x_col = df.columns[0]
                    y_col = df.columns[1]

                    chart_type = st.selectbox(
                        "Chart Type",
                        ["Bar", "Line", "Pie"],
                        key=f"chart_{i}"
                    )

                    if chart_type == "Bar":
                        fig = px.bar(df, x=x_col, y=y_col)
                    elif chart_type == "Line":
                        fig = px.line(df, x=x_col, y=y_col)
                    else:
                        fig = px.pie(df, names=x_col, values=y_col)

                    st.plotly_chart(fig, use_container_width=True)

                except:
                    pass

        st.markdown("</div>", unsafe_allow_html=True)

# ---------- INPUT ----------
question = st.chat_input("💬 Ask your data...")

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    # Build history for context
    history = []
    for m in st.session_state.messages:
        if m["role"] == "assistant":
            history.append({
                "question": m.get("question", ""),
                "sql": m.get("sql", "")
            })

    with st.spinner("Generating SQL and fetching results..."):
        sql = generate_sql(question, history)
        result = run_query(sql)

    st.session_state.messages.append({
        "role": "assistant",
        "sql": sql,
        "result": result,
        "question": question
    })

    st.rerun()

# ---------- CLEAR CHAT ----------
if st.button("🧹 Clear Chat"):
    st.session_state.messages = []