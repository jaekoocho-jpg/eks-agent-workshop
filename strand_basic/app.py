# POD에서 실행 시 Service Account의 IAM Role을 통해 자동으로 인증됩니다.
# ConfigMap을 통해 AWS_REGION, BEDROCK_MODEL_ID 환경 변수 설정 가능

import os
from strands import Agent
from strands.models import BedrockModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import boto3

# 전역 변수
bedrock_model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bedrock_model

    # ConfigMap에서 환경 변수 읽기 (기본값 제공)
    aws_region = os.getenv("AWS_REGION", "us-west-2")
    model_id = os.getenv(
        "BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    )

    try:
        # Service Account의 IAM Role을 사용하여 Bedrock 클라이언트 생성
        # EKS Pod Identity 또는 IRSA를 통해 자동으로 credentials 획득
        bedrock_runtime = boto3.client(
            service_name="bedrock-runtime", region_name=aws_region
        )

        # BedrockModel 초기화 (boto3 client 사용)
        bedrock_model = BedrockModel(
            model_id=model_id,
            client=bedrock_runtime,
        )
        print(f"Bedrock 모델 초기화 완료")
        print(f"  - Region: {aws_region}")
        print(f"  - Model ID: {model_id}")
        print(f"  - 인증: Service Account IAM Role")
    except Exception as e:
        print(f"Bedrock 초기화 오류: {e}")
        raise

    yield


app = FastAPI(title="AWS knowledge", lifespan=lifespan)

SYSTEM_PROMPT = """
당신은 AWS 전문가로써 질문에 대한 답은 기본적으로 AWS knowledge mcp 서버에서 검색해서 답을 하세요
답변은 정중하고 모호한 답변은 하지 마세요
"""


class PromptRequest(BaseModel):
    prompt: str


@app.get("/")
async def read_root():
    """간단한 소개 페이지"""
    return {
        "service": "AWS Knowledge API",
        "description": "AWS 전문 지식을 제공하는 API 서비스입니다",
        "version": "1.0.0",
        "endpoints": {
            "/": "서비스 소개",
            "/health": "헬스 체크",
            "/knowledge": "AWS 지식 질의응답 (POST)",
        },
        "powered_by": "Amazon Bedrock & Strands Agent",
    }


@app.get("/health")
async def health_check():
    """Pod 헬스 체크 엔드포인트"""
    if bedrock_model is None:
        raise HTTPException(status_code=503, detail="Bedrock model not initialized")

    return {"status": "healthy", "bedrock_model": "initialized"}


@app.post("/knowledge")
async def get_knowledge(request: PromptRequest):
    """AWS 지식 정보를 가져오는 엔드포인트."""
    if not request.prompt:
        raise HTTPException(status_code=400, detail="No prompt provided")

    try:
        agent = Agent(model=bedrock_model, system_prompt=SYSTEM_PROMPT)
        response = agent(request.prompt)
        return PlainTextResponse(content=str(response))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# [[ 로컬에서 실행시 참조 ]]:
# uvicorn app:app --reload
#

# [ 테스트 ]:
# curl -X GET http://127.0.0.1:8000/
# curl -X POST http://127.0.0.1:8000/knowledge -H "Content-Type: application/json" -d '{"prompt": "Amazon S3가 뭐야?"}'
