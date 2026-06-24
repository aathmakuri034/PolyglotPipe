
import stream lit as lt


open source: python and typescript
connect llms with our data
connect to external api

Components - Llm wrappers, prompt - hard coded templates, index
Chains- assemble the components to solve a task
Agents - allow llms to interact

Load_dotEnv : to save nv varaibles / secret keys

call the openAI 
Temperature
JSON format
prompt template

component : lmm = anthropic(YOUR_ANTHROPIC_KEY)
llm-chain : put together the componets of langchian : LLMChain(llm, prompt, output_key)
Agents : let the llms choose sequence of actions/tools : as a reasoning engine . Powered by language model and prompt
tools: functions that agents call : give acess and describe the tool that is helpful to the agent


JSON format
response = lch.generate_pet_name

load_tools
intialize_agent
verbose = reasoning thats happening = true 
agents.run
agent type


provide knowledge base on which llm can take an action
Build a llm - Book 
indexig - storage for llm

FAISS - meta vector db

text splitter, loader

token context and limits a model can take

docs, context,

llm, prompt,

chain : LLm chain

stream lit


chains/	Engineer A
graph/	Engineer A
providers/	Engineer A
scripts/	Whoever wrote it
tests/unit/	Matches source ownership
tests/integration/	Whoever wrote it

from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from IPython.display import display, Image
import os

LangGraph workflows share data through a state object:
class HelloWorldState(TypedDict):
    message: str

Nodes are just Python functions that perform tasks
# def display_message_node(state: HelloWorldState) -> str:
    '''A node function that takes the current state and returns a new state with a 
    modified message.'''
    state["message"] = f"Hello, {state['message']} from LangGraph!"
    return state


# Create a graph with our state schema
graph = StateGraph(HelloWorldState)

# Add nodes
graph.add_node("message_node", display_message_node)
# Define edges
graph.set_entry_point("message_node")
graph.set_finish_point("message_node")
# Another way to define edges
# graph.add_edge(START, "message_node")
# graph.add_edge("message_node", END)
