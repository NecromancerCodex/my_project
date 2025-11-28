from fastapi import FastAPI, APIRouter, HTTPException  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from pydantic import BaseModel  # type: ignore
import uvicorn  # type: ignore
import os
from openai import OpenAI  # type: ignore
from dotenv import load_dotenv  # type: ignore

# 환경 변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
openai_api_key = os.getenv("OPENAI_API_KEY", "")
if not openai_api_key:
    print("Warning: OPENAI_API_KEY not set. Chat functionality will be limited.")
    client = None
else:
    client = OpenAI(api_key=openai_api_key)

app = FastAPI(
    title="Chatbot Service API",
    version="1.0.0",
    description="챗봇 서비스 API"
)

# CORS 설정 - 게이트웨이만 허용 (프론트엔드는 게이트웨이를 통해 접근)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:9000",
        "http://gateway-app:9000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 서브 라우터 생성
chatbot_router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# 메시지 모델
class Message(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str

# 요청 모델
class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-3.5-turbo"
    system_message: str = "You are a helpful assistant. Respond in Korean."
    conversation_history: list[Message] = []  # 대화 히스토리 (선택사항)

# 응답 모델
class ChatResponse(BaseModel):
    message: str
    model: str

@chatbot_router.get("/chat")
def chat():
    """
    챗봇 대화 API (GET - 기본 테스트)
    
    - **반환**: 챗봇 응답
    """
    if client is None:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "안녕하세요! 오늘 날씨 어때요?"}
            ]
        )
        
        return {
            "message": response.choices[0].message.content,
            "model": response.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

@chatbot_router.post("/chat", response_model=ChatResponse)
def chat_post(request: ChatRequest):
    """
    챗봇 대화 API (POST - 사용자 메시지 전송)
    
    대화 히스토리를 포함하여 연속적인 대화가 가능합니다.
    
    - **message**: 사용자 메시지
    - **model**: 사용할 모델 (기본값: gpt-3.5-turbo)
    - **system_message**: 시스템 메시지 (기본값: "You are a helpful assistant. Respond in Korean.")
    - **conversation_history**: 이전 대화 히스토리 (선택사항)
        예: [{"role": "user", "content": "안녕"}, {"role": "assistant", "content": "안녕하세요!"}]
    
    - **반환**: 챗봇 응답
    """
    if client is None:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )
    
    try:
        # 메시지 배열 구성
        messages = [
            {"role": "system", "content": request.system_message}
        ]
        
        # 대화 히스토리가 있으면 추가
        if request.conversation_history:
            for msg in request.conversation_history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 현재 사용자 메시지 추가
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        response = client.chat.completions.create(
            model=request.model,
            messages=messages
        )
        
        return ChatResponse(
            message=response.choices[0].message.content or "",
            model=response.model
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

# 서브 라우터를 앱에 포함
app.include_router(chatbot_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9001)
