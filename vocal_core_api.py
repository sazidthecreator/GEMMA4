from fastapi import FastAPI
from pydantic import BaseModel
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

app = FastAPI()

# Initializing Engine
llm = ChatOllama(model="gemma", temperature=0.6)
system_instruction = """[INSERT YOUR FULL SYSTEM PROMPT WITH FEW-SHOT EXAMPLES HERE]"""
prompt = ChatPromptTemplate.from_messages(
    [("system", system_instruction), ("human", "{text}")])
chain = prompt | llm


class TextRequest(BaseModel):
    text: str


@app.post("/transcreate")
async def transcreate(request: TextRequest):
    response = chain.invoke({"text": request.text})
    return {"formatted_text": response.content}

# Run with: uvicorn vocal_core_api:app --reload --port 8000