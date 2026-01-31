# extended_test_langchain_pipeline.py

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def main():
    # 1. Connect to your local LLM
    llm = ChatOpenAI(
        base_url="http://localhost:1234/v1",
        api_key="not-needed",
        model="qwen/qwen3-4b-2507"
    )

    # 2. Define prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a research assistant. Rewrite text into a clear, structured report."),
        ("user", "{input}")
    ])

    # 3. Build pipeline (prompt → llm → parser)
    parser = StrOutputParser()
    pipeline = prompt | llm | parser

    # 4. Test inputs
    test_inputs = [
        "This is a short test sentence.",
        "Here is a longer paragraph that should be rewritten in a more formal and structured style. It contains multiple sentences to check coherence."
    ]

    for i, text in enumerate(test_inputs, start=1):
        print(f"\n=== Test {i} Input ===")
        print(text)
        result = pipeline.invoke({"input": text})
        print("\n=== LLM Output ===")
        print(result)

    # 5. Multi-chunk simulation
    long_text = (
        "Section 1: Background of the study.\n"
        "This research explores the impact of AI pipelines.\n\n"
        "Section 2: Methodology.\n"
        "We used modular orchestration and provenance tracking.\n\n"
        "Section 3: Results.\n"
        "The pipeline produced reproducible and auditable outputs."
    )

    chunks = long_text.split("\n\n")
    rewritten_sections = [pipeline.invoke({"input": chunk}) for chunk in chunks]

    print("\n=== Multi-chunk Rewritten Report ===")
    print("\n".join(rewritten_sections))

if __name__ == "__main__":
    main()