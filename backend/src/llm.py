import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import HumanMessage

load_dotenv()


def get_llm():
    """
    Returns the HuggingFace-backed chat model.
    Model can be changed via the HF_MODEL env var, or by editing repo_id below.
    For better tool-calling reliability, consider a larger model:
      - Qwen/Qwen2.5-72B-Instruct  (much stronger tool use)
      - meta-llama/Llama-3.3-70B-Instruct
    """
    repo_id = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")

    llm = HuggingFaceEndpoint(
        repo_id=repo_id,
        huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
        temperature=0.1,
        provider="auto",
    )

    return ChatHuggingFace(llm=llm)


if __name__ == "__main__":
    llm = get_llm()
    print("✅ Hugging Face Connection Successful.")
    resp = llm.invoke([HumanMessage(content="What is machine learning? Answer in one sentence.")])
    print(resp.content)