import re
import pymupdf
import streamlit as st
import config
from search import HybridSearch
from answer import answer_question

st.set_page_config(page_title="FinSight AI", page_icon="📊", layout="wide")

EXAMPLE_QUESTIONS = [
    "What was the total revenue this year?",
    "What was the capital expenditure as a percentage of revenue?",
    "What are the main risks the company mentions?",
]


@st.cache_resource
def load_searcher():
    # only build the search index once, not every time the page reloads
    return HybridSearch()


@st.cache_data
def page_image(doc, page):
    # turn one pdf page into a png so we can show it next to the answer
    pdf = pymupdf.open(f"{config.PDF_FOLDER}/{doc}.pdf")
    image = pdf[page - 1].get_pixmap(dpi=110).tobytes("png")
    pdf.close()
    return image


def split_name(doc):
    # "JOHNSON_JOHNSON_2022_10K" -> ("JOHNSON JOHNSON", "2022 10K")
    match = re.match(r"(.+?)_(\d{4}.*)", doc)
    return match.group(1).replace("_", " "), match.group(2).replace("_", " ")


def escape(text):
    # streamlit reads $...$ as maths, so escape the dollar signs
    return text.replace("$", "\\$")


searcher = load_searcher()

# ---------- sidebar: choose a report ----------
with st.sidebar:
    st.title("📊 FinSight AI")
    st.caption("Ask questions about company annual reports. Every answer cites its page.")

    reports = {}
    for doc in searcher.list_documents():
        company, report = split_name(doc)
        reports.setdefault(company, {})[report] = doc

    company = st.selectbox("Company", sorted(reports))
    report = st.selectbox("Report", sorted(reports[company], reverse=True))
    doc = reports[company][report]

    st.divider()
    st.write("**Try an example:**")
    for example in EXAMPLE_QUESTIONS:
        if st.button(example, width="stretch"):
            st.session_state.pending_question = example

    st.divider()
    if st.button("Clear chat", width="stretch"):
        st.session_state.messages = []

    st.caption("Retrieval Hit@5 on FinanceBench: 44% → 55% with query expansion")

# ---------- chat ----------
st.header(f"{company} · {report}")

if "messages" not in st.session_state:
    st.session_state.messages = []


def show_answer(result):
    st.markdown(escape(result["answer"]))

    with st.expander("How I found this"):
        st.write("**Search queries:**")
        for q in result.get("queries", []):
            st.write("- " + escape(q))
        if result.get("calculations"):
            st.write("**Calculator:**")
            for c in result["calculations"]:
                st.code(c)

    # only show the sources the answer actually cites, e.g. [Source 4]
    cited = set(int(n) for n in re.findall(r"Source (\d+)", result["answer"]))
    sources = [s for s in result["sources"] if s["source"] in cited]
    if not sources:
        return

    st.write("**Sources**")
    tabs = st.tabs([f"Source {s['source']} · p.{s['page']}" for s in sources])
    for tab, s in zip(tabs, sources):
        with tab:
            left, right = st.columns([1, 1])
            with left:
                st.caption(f"{s['doc']}, page {s['page']}")
                st.write(escape(s.get("text", "")))
            with right:
                st.image(page_image(s["doc"], s["page"]), width="stretch")


# show the previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(escape(message["content"]))
        else:
            show_answer(message["content"])

# new question from the chat box or an example button
question = st.chat_input("Ask a question about this report")
if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(escape(question))

    with st.chat_message("assistant"):
        with st.spinner("Reading the report..."):
            try:
                result = answer_question(question, searcher, doc)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.stop()
        show_answer(result)

    st.session_state.messages.append({"role": "assistant", "content": result})