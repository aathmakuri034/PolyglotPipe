
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