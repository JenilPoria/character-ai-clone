from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage,SystemMessage,HumanMessage,trim_messages
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START,END
import os
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

from app.schemas import State
from app.database import SessionLocal
from app.models import Character
from app.utils.memory import retrieve_relevant_memories
from app.prompt import system_prompt
 
load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(temperature=0.5, api_key=groq_key, model_name ="llama-3.1-8b-instant" )

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("placeholder", "{user_input}"),
])

chain = prompt | llm

def get_character_info(char_id : str):
    """
        Connects to app.db, finds the character, and returns their JSON prompt data.
    """
    db = SessionLocal()

    try: 
        character = db.query(Character).filter(Character.id == char_id).first()

        if character:
            return character.prompt_data
        return None
    finally:
        db.close()


def chat_node(state : State, config : RunnableConfig):

    char_id = config["configurable"].get("char_id")

    thread_id = config["configurable"].get("thread_id")

# --- DEBUGGING START ---
    user_id = thread_id.split("_")[0] 
    print(f"\n🕵️ DEBUG RETRIEVAL:")
    print(f"   -> Full Thread ID: '{thread_id}'")
    print(f"   -> Extracted User ID: '{user_id}' (Type: {type(user_id)})")
    print(f"   -> Character ID: '{char_id}'")
    # --- DEBUGGING END ---
    character_info = get_character_info(char_id)
    if not character_info:
        return {"messages": [HumanMessage(content="Error: Character deleted or not found.")]}
    
    last_user_msg = state.messages[-1].content

    print(f"🔍 Searching memories for: {last_user_msg}...")
    memories = retrieve_relevant_memories(user_id, char_id, last_user_msg)

    if memories:
        memory_text ="\n".join([f"- {m}" for m in memories])
    else :
        memory_text = "No RElavant past history"

    print(f"🧠 Context Found: {memory_text}")
    # print(f"\n--- Talking to  {character_info["CHAR_NAME"]} ---")
    print(f"\n--- TALKING TO: {character_info.get('CHAR_NAME', 'Unknown')} ---")

    message_length = len(state.messages)
    print(f"\n--- DEBUG START ---")
    print(f"Total messages in state : {message_length}")
    # message = [SystemMessage(content=system_prompt)] + state["messages"]
    # message = state.messages[-1].content
    selected_messages = trim_messages(
        state.messages,
        token_counter=len,
        max_tokens=10,
        strategy="last",
        start_on="human",
        include_system=False,
        allow_partial=False
    )
    trimed_messages_count = len(selected_messages)

    print(f"Messages  Sent to LLM : {trimed_messages_count}")
    response = chain.invoke({"user_input": selected_messages,"LONG_TERM_MEMORY":memory_text, **character_info})
    return {"messages":[response]}

conn = sqlite3.connect("./character_ai.db",check_same_thread=False)
checkpoint_saver =  SqliteSaver(conn= conn)

graph = StateGraph(State)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpoint_saver)
