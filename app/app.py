# https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_amazon_eks/

import boto3
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import asyncio

# 전역 변수
mcp_client = None
tools = None
bedrock_model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 초기화
    global mcp_client, tools, bedrock_model

    # AWS 자격증명
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        bedrock_model = BedrockModel(
            model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            boto_session=session,
        )
    except Exception as e:
        print(f"AWS 자격 증명 오류: {e}")

    # MCP 클라이언트 초기화
    mcp_client = MCPClient(
        lambda: streamablehttp_client("https://knowledge-mcp.global.api.aws")
    )

    # 동기 방식으로 세션 시작
    await asyncio.to_thread(mcp_client.__enter__)
    tools = await asyncio.to_thread(mcp_client.list_tools_sync)

    yield

    # 종료 시 정리
    await asyncio.to_thread(mcp_client.__exit__, None, None, None)


app = FastAPI(title="AWS knowledge", lifespan=lifespan)

SYSTEM_PROMPT = """
당신은 AWS 전문가로써 질문에 대한 답은 기본적으로 AWS knowledge mcp 서버에서 검색해서 답을 하세요
답변은 정중하고 모호한 답변은 하지 마세요
"""


class PromptRequest(BaseModel):
    prompt: str


@app.get("/")
def read_root():
    return {"message": "안녕하세요 어서오세요!"}


@app.post("/knowledge")
async def get_knowledge(request: PromptRequest):
    """AWS 지식 정보를 가져오는 엔드포인트 생성."""
    prompt = request.prompt

    if not prompt:
        raise HTTPException(status_code=400, detail="No prompt provided")

    try:
        agent = Agent(model=bedrock_model, tools=tools, system_prompt=SYSTEM_PROMPT)
        response = agent(prompt)
        content = str(response)
        return PlainTextResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


######################
# test 실행 방법
# --------------
#
# 1. 터미널 창에서 uvicorn 명령으로 실행합니다. 기본 포트는 8000번으로 시작합니다.
#   uvicorn app:app --reload
#
# 2. 다른 터미널 창에서 다음명령으로 test 해봅니다. 이때 포트 번호는 8000번으로 합니다.
# curl -X POST http://127.0.0.1:8000/knowledge -H "Content-Type: application/json"   -d '{"prompt": "Amazon S3가 뭐야?"}'
#
######################
