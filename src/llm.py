import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import HumanMessage

load_dotenv()

def get_llm():
    repo_id = "Qwen/Qwen2.5-7B-Instruct"
    
    llm = HuggingFaceEndpoint(
        repo_id=repo_id,
        huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
        temperature=0.1, # Low temp for precision scheduling
        provider="auto",
    )

    chat_model = ChatHuggingFace(llm=llm)
    return chat_model

if __name__ == "__main__":
    llm = get_llm()
    print("✅ Hugging Face Connection Successful.")
    resp = llm.invoke([HumanMessage(content="What is machine learning?")])
    print(resp.content)