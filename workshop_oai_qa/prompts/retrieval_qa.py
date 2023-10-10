from typing import Any, List

from langchain.prompts import ChatPromptTemplate, BaseChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain.schema import BaseMessage, SystemMessage, HumanMessage, ChatMessage, Document
from pydantic import validator, BaseModel

_SYSTEM_PROMPT = """Assistant helps the company employees with their questions, By using companies knowledge base. Be brief in your answers.
Answer ONLY with the facts listed in the list of sources below. If there isn't enough information below, say you don't know. Do not generate answers that don't use the sources below. If asking a clarifying question to the user would help, ask the question.
For tabular information return it as an html table. Do not return markdown format. If the question is not in English, answer in the language used in the question.
Each source has a name followed by colon and the actual information, always include the source name for each fact you use in the response. Use square brackets to reference the source, e.g. [info1.txt]. Don't combine sources, list each source separately, e.g. [info1.txt][info2.pdf].
"""

_FOLLOW_UP_QUESTIONS_PROMPT = """Generate three very brief follow-up questions that the user would likely ask next regarding the answer to the question and retrieved documents form the knowledgebase.
Use double angle brackets to reference the questions, e.g. <<Can you give me a code example?>>.
Try not to repeat questions that have already been asked.
Only generate questions and do not generate any text before or after the questions, such as 'Next Questions'
Here is an example of follow-up questions:
Answer to the question.
<<Can you give me a code example?>>, <<What is the difference between X and Y?>>, <<What is the best way to do Z?>>.
"""

_EXAMPLE_FOLLOW_UP_QUESTIONS = [
    "<<What are some examples of tasks that can be performed using the Transformers library?>>",
    "<<Can I use the Transformers library with different deep learning frameworks?>>",
    "<<How can I fine-tune a pretrained model using the Transformers library?>>"
]

_EXAMPLES = [
    {
        "input": "What can you tell me about the transformers library?",
        "output": """The Transformers library is an opinionated library built for machine learning researchers, 
        practitioners, and engineers. It provides state-of-the-art models for natural language processing, 
        computer vision, and audio and speech processing tasks. The library is designed to be easy and fast to use, 
        with minimal user-facing abstractions. It supports PyTorch, TensorFlow, and JAX frameworks and allows for 
        framework interoperability. The library also provides APIs for quickly using models for inference and for 
        training or fine-tuning models. [data/transformers_docs_full/philosophy.md][
        data/transformers_docs_full/index.md][data/transformers_docs_full/task_summary.md]""".replace('\n', '')
                  + '\n' + ''.join(_EXAMPLE_FOLLOW_UP_QUESTIONS)
    },
]


class RetrievalQAPrompt(BaseChatPromptTemplate):
    input_variables: List[str] = ["input", "history", 'documents']

    def format_messages(
            self,
            input: str,
            history: List[BaseMessage],
            documents: List[Document],
            **kwargs: Any
    ) -> List[BaseMessage]:
        # Format documents into prompt
        sources = self.format_documents(documents)

        # Format input into prompt by including sources
        question = f'{input}\nSources:\n{sources}' if documents else input

        return [
            SystemMessage(content=_SYSTEM_PROMPT + '\n' + _FOLLOW_UP_QUESTIONS_PROMPT),
            *FewShotChatMessagePromptTemplate(
                example_prompt=ChatPromptTemplate.from_messages([
                    ("user", "{input}"),
                    ("assistant", "{output}"),
                ]),
                examples=_EXAMPLES,
            ).format_messages(),
            *history,
            ChatMessage(role='user', content=question),
        ]

    def format_documents(self, documents: List[Document]) -> str:
        return '\n'.join([self.format_document(doc) for doc in documents])

    def format_document(self, document: Document) -> str:
        content = document.page_content.replace('\n', '')
        return f'{document.metadata["source"]}: {content}'
