from langchain.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate

_SYSTEM_MESSAGE = """Below is a history of the conversation so far, and a new question asked by the user that needs to be answered by searching in a knowledge base.
You have access to Azure Cognitive Search index with 100's of documents.
Generate a search query based on the conversation and the new question.
Do not include cited source filenames and document names e.g info.txt or doc.pdf in the search query terms.
Do not include any text inside [] or <<>> in the search query terms.
Do not include any special characters like '+'.
If the question is not in English, translate the question to English before generating the search query.
If you cannot generate a search query, return just the number 0."""

_PROMPT = "Generate search query for: {input}"

QUERY_GENERATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM_MESSAGE),
        FewShotChatMessagePromptTemplate(
            example_prompt=ChatPromptTemplate.from_messages([
                ("user", _PROMPT),
                ("assistant", "{output}"),
            ]),
            examples=[
                {"input": "What are my health plans?", "output": "Show available health plans"},
                {"input": "does my plan cover cardio?", "output": "Health plan cardio coverage"},
            ],
        ),
        ("user", _PROMPT),
    ]
)
