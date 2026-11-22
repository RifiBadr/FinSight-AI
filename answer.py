import json
from openai import OpenAI
import config

client = OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)

SYSTEM_PROMPT = """You are a financial analyst assistant.
Answer the question using ONLY the sources, which come from a company's annual report.
- After every fact, cite the source like [Source 2].
- You MUST call the calculator tool for every calculation. Never write a calculated number that did not come from the calculator.
- If the sources do not contain the answer, say "I could not find this in the report."
- Keep the answer short."""

CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Calculate a maths expression, e.g. '1577 / 32765 * 100'",
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    },
}


def calculator(expression):
    expression = expression.replace(",", "")
    # only allow numbers and maths symbols, so the llm can't run other python code
    if not all(ch in "0123456789+-*/(). " for ch in expression):
        return "Error: only numbers and + - * / ( ) are allowed"
    try:
        return round(eval(expression, {"__builtins__": {}}), 4)
    except Exception as e:
        return f"Error: {e}"


def make_search_queries(question):
    # split the question into one search query per fact we need
    prompt = (
        "Split this financial question into 1 to 3 short search queries, one for each fact needed.\n"
        "Use the wording an annual report would use and name the statement where the fact is. Examples:\n"
        "revenue -> 'net sales 2018 income statement'\n"
        "capex -> 'purchases of property plant and equipment 2018 cash flow statement'\n"
        "Write one query per line and nothing else.\n\n"
        "Question: " + question
    )
    response = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    lines = response.choices[0].message.content.strip().split("\n")
    return [line.strip("-* ") for line in lines if line.strip()][:3]


def find_chunks(question, searcher, doc=None):
    queries = [question] + make_search_queries(question)
    chunks = []
    for query in queries:
        for chunk in searcher.search(query, k=3, doc=doc):
            if chunk not in chunks:
                chunks.append(chunk)
    return chunks, queries


def answer_question(question, searcher, doc=None):
    chunks, queries = find_chunks(question, searcher, doc)
    print("search queries:", queries)

    sources = ""
    for i, c in enumerate(chunks, start=1):
        sources += f"[Source {i}] ({c['doc']}, page {c['page']})\n{c['text']}\n\n"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Sources:\n" + sources + "Question: " + question},
    ]

    calculations = []

    # the llm can call the calculator a few times before it answers
    for _ in range(5):
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            tools=[CALCULATOR_TOOL],
            temperature=0,
        )
        message = response.choices[0].message
        if not message.tool_calls:
            break

        messages.append(message)
        for call in message.tool_calls:
            expression = json.loads(call.function.arguments)["expression"]
            result = calculator(expression)
            print(f"calculator: {expression} = {result}")
            calculations.append(f"{expression} = {result}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": str(result)})

    answer = message.content.replace("【", "[").replace("】", "]")
    source_list = [
        {"source": i, "doc": c["doc"], "page": c["page"], "text": c["text"]}
        for i, c in enumerate(chunks, start=1)
    ]
    return {"answer": answer, "sources": source_list, "queries": queries, "calculations": calculations}


if __name__ == "__main__":
    from search import HybridSearch

    searcher = HybridSearch()
    question = "What is 3M's FY2018 capital expenditure as a percentage of its FY2018 revenue?"
    result = answer_question(question, searcher, doc="3M_2018_10K")

    print("\nQ:", question)
    print("A:", result["answer"])
    print("\nsources:")
    for s in result["sources"]:
        print(f"  [Source {s['source']}] {s['doc']}, page {s['page']}")