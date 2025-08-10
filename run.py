from langgraph.graph import StateGraph,START,END
from typing import TypedDict
from langchain_core.messages import AnyMessage,HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.store.memory import InMemoryStore
from typing_extensions import Annotated
from langgraph.types import CachePolicy
from langgraph.graph.message import add_messages
from langgraph.runtime import Runtime  
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from dotenv import load_dotenv
import os
import streamlit as st
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver

load_dotenv()

class MyState(TypedDict):
    input: Annotated[list[AnyMessage], add_messages]
    output: Annotated[list[AnyMessage], add_messages]

class myruntime(TypedDict):
    llm_model: str
    api_key: str
    end_point: str

# checkpointer=InMemorySaver()

api_key=os.getenv("NVIDIA_API_KEY")
llm_model=os.getenv("NVIDIA_MODEL_2")
end_point=os.getenv("NVIDIA_API_ENDPOINT")
mango_db_password=os.getenv("MONGO_DB_PASSWORD")
os.environ['NVIDIA_API_KEY']=api_key

mango_db_as_db=False

uri = f"mongodb+srv://hiremath0308:{mango_db_password}@mycluster.ug67j.mongodb.net/?retryWrites=true&w=majority&appName=mycluster"



# Build graph once
graph = StateGraph(MyState, context_schema=myruntime)

def call_llm(state: MyState, runtime: Runtime[myruntime]) -> MyState:
    input_message = state['input'][-1]
    llm_model = runtime.context['llm_model']
    end_point = runtime.context['end_point']

    model = ChatNVIDIA(model=llm_model, base_url=end_point)
    response = model.invoke([input_message])
    return {'output': [response]}

graph.add_node("call_llm", call_llm)
graph.add_edge(START, "call_llm")
graph.add_edge("call_llm", END)

context = {
            "llm_model": llm_model,
            "api_key": api_key,
            "end_point": end_point
            }
# if mango_db_as_db:
#     # with MongoDBSaver.from_conn_string(uri) as checkpointer:
#     #     build = graph.compile(checkpointer=checkpointer)
#     checkpointer = MongoDBSaver.from_conn_string(uri)       


conn = sqlite3.connect("checkpoints_2.db", check_same_thread=False)

checkpointer = SqliteSaver(conn)
print("has get method?", hasattr(checkpointer, "get"))

print(checkpointer.get({"configurable": {"thread_id": "satya"}}))
build = graph.compile(checkpointer=checkpointer)
print(checkpointer.get({"configurable": {"thread_id": "satya"}}))
