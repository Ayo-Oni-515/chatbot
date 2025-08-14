import os
import shutil
from typing import Annotated, TypedDict, Optional, Literal  # noqa

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    DirectoryLoader, TextLoader, PyMuPDFLoader, CSVLoader)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END  # noqa
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, ToolMessage  # noqa
from pydantic import BaseModel, Field  # noqa
from langgraph.checkpoint.memory import MemorySaver  # noqa
# from langchain_core.tools import tool

from utils import save_to_json, load_from_json


class RouteDecision(BaseModel):
    """router output schema"""
    route: Literal["rag", "answer"]


class RagJudge(BaseModel):
    """rag judge boolean output schema"""
    sufficient: bool


class BotState(TypedDict):
    """handles how data's state is structured throughout the workflow"""
    context: Optional[list[Document]]
    route: Optional[Literal["rag", "answer", "end"]]
    messages: Annotated[list[BaseMessage], add_messages]


class ChatBot():
    # tailored prompt templates
    query_template = """
    You are a highly skilled support chatbot with access to a knowledge base.
    Use the following pieces of retrieved context to answer the question
    while maintaining conversation flow.

    context: {context}

    question: {question}

    Instructions:
    - Provide detailed answers when the context supports it
    - Use your general knowledge if the
        context doesn't cover the question
    - If you don't know the answer, say
        "I don't have enough information to answer that question"
    - Be concise, helpful, and professional
    - Don't mention that you're using provided context
    """

    router_template = """
    You are a router that decides how to handle user queries:
    - Use 'rag' when knowledge base lookup is required.
    - Use 'answer' whenever you can answer directly without external info or
    for pure greetings or small-talk (also providing a reply).

    Look at the question below:

    question: {question}
    """

    retrieval_judge_template = """
    You are a judge evaluating if the retrieved information is sufficient
    to answer the user's question. Consider both relevance and completeness.

    question: {question}

    retrieved context: {context}

    Is this sufficient to answer the question?
    """

    def __init__(self,
                 data_path: str = "./data_sources",
                 db_location: str = "./vector_store",
                 user_db_location: str = "./user_vector_store",
                 sp_db_location: str = "./sp_vector_store",
                 llm: str = "llama3.2:3b",
                 embedding_model: str = "mxbai-embed-large:335m",
                 ):
        self.data_path = data_path
        self.db_location = db_location
        self.user_db_location = user_db_location
        self.sp_db_location = sp_db_location

        # Initialize the graph's memory saver
        self.memory = MemorySaver()

        try:
            self.llm = ChatOllama(model=llm)
        except Exception as e:
            raise Exception(e.args)

        self.router_llm = self.llm.with_structured_output(RouteDecision)
        self.judge_llm = self.llm.with_structured_output(RagJudge)
        self.answer_llm = self.llm

        self.embedding_model = embedding_model

        self.querying_template = ChatPromptTemplate.from_template(
            ChatBot.query_template)
        self.routing_template = ChatPromptTemplate.from_template(
            ChatBot.router_template)
        self.retrieval_judging_template = ChatPromptTemplate.from_template(
            ChatBot.retrieval_judge_template)

        documents_directory = os.listdir(self.data_path)
        tracked_documents = load_from_json()

        if sorted(documents_directory) != sorted(tracked_documents):
            chunks = self.run()

            # ensures vectorizing is done only once on document update
            self.vector_store = self.save_to_chroma(chunks)
        else:
            # initializes a chroma client
            self.vector_store = Chroma(
                persist_directory=self.db_location,
                embedding_function=self.initialize_embedding()
            )

    def initialize_embedding(self):
        """returns chatbot's embedding model used for vectorizing chunks"""
        try:
            return OllamaEmbeddings(model=self.embedding_model)
        except Exception as e:
            raise Exception(e.args)

    def initialize_text_splitter(self):
        """returns chatbot's recursive character text
            splitter used for chunking"""
        try:
            return RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                add_start_index=True
            )
        except Exception as e:
            raise Exception(e.args)

    def load_documents(self):
        """loads knowledge sources into a list of 'Document' objects

        load documents from a directory (supported formats .pdf, .md, .txt)
        """
        # handle
        # only stores new sources
        # include web scraper

        data_path = self.data_path
        documents = []

        document_extensions = {
            ".pdf": PyMuPDFLoader,
            ".md": TextLoader,
            ".txt": TextLoader,
            ".csv": CSVLoader
            }

        for extension, loader_class in document_extensions.items():
            loader = DirectoryLoader(
                data_path, glob=f"*{extension}",
                loader_cls=(
                    loader_class if extension == ".pdf" else (
                        lambda path: loader_class(
                            path, encoding="utf-8"))),
                show_progress=True)
            documents.extend(loader.load())

        return documents

    def save_to_chroma(self, chunks: list[Document]):
        """returns a chroma client used to query the vector database"""
        # handle
        try:
            # Clear out the database first.
            if os.path.exists(self.db_location):
                shutil.rmtree(self.db_location)

            db = Chroma.from_documents(
                documents=chunks,
                embedding=self.initialize_embedding(),
                persist_directory=self.db_location
            )

            return db
        except Exception as e:
            raise Exception(e.args)

    def run(self):
        """runs the indexing process: loading + splitting + chunking"""
        # handle
        try:
            documents = self.load_documents()
        except Exception as e:
            raise Exception(e.args)

        # keeps track of all chunked documents
        loaded_documents = [
            os.path.basename(doc.metadata["source"]) for doc in documents]

        # save loaded documents to a json file
        save_to_json(data_to_save=list(set(loaded_documents)))

        chunks = (self.initialize_text_splitter()).split_documents(
            documents
        )

        return chunks

    async def router_node(self, state: BotState):
        """core router node responsible for properly forwarding queries
        along the right workflow branch
        """
        if len(state["messages"]) == 0:
            # Initial state: start of the conversation

            route_prompt = self.routing_template.invoke(
                {"question": (state["messages"]).content})
            route_decision: RouteDecision = await self.router_llm.ainvoke(
                route_prompt)
        else:
            # Subsequent state: other conversations

            route_prompt = self.routing_template.invoke(
                {"question": (state["messages"][-1]).content})
            route_decision: RouteDecision = await self.router_llm.ainvoke(
                route_prompt)

        return {"route": route_decision.route}

    async def aretrieve(self, state: BotState):
        """query the vector store asynchronously to retrieved context"""
        if len(state["messages"]) == 0:
            # Initial state: start of the conversation

            retrieved_docs = await self.vector_store.asimilarity_search(
                (state["messages"]).content)
            return {"context": retrieved_docs}
        else:
            # Subsequent state: other conversations

            retrieved_docs = await self.vector_store.asimilarity_search(
                (state["messages"][-1]).content)
            return {"context": retrieved_docs}

    async def agenerate(self, state: BotState):
        """reconstructs the query based on retrieved context"""
        context = await self.aretrieve(state)

        docs_content = "\n\n".join(
            doc.page_content for doc in context["context"])

        modified_query = self.querying_template.invoke(
                {"question": (state["messages"][-1]).content,
                 "context": docs_content})

        # response = await self.llm.ainvoke(messages)
        state["messages"].pop()
        state["messages"].append(
            modified_query.messages[0])
        # print(state["messages"])
        return {"messages": state["messages"]}

    async def answer_node(self, state: BotState):
        """llm node for answering all queries."""
        response = await self.answer_llm.ainvoke(state["messages"])
        return {"messages": response}

    def from_router(self, state: BotState) -> Literal["rag", "answer"]:
        """returns route to follow down the graph"""
        return state["route"]

    def acompile(self):
        """returns a grpah depicting the overall workflow"""
        graph_builder = StateGraph(BotState)

        # adding graph nodes
        graph_builder.add_node("router", self.router_node)
        graph_builder.add_node("answer", self.answer_node)
        graph_builder.add_node("rag", self.agenerate)

        # setting graph's entry point as the router
        graph_builder.set_entry_point("router")

        # adding graph edges
        graph_builder.add_conditional_edges("router", self.from_router,
                                            {
                                                "rag": "rag",
                                                "answer": "answer"
                                            })
        graph_builder.add_edge("rag", "answer")
        graph_builder.add_edge("answer", END)

        # compile the graph with an in-memory saver
        graph = graph_builder.compile(checkpointer=self.memory)

        return graph
