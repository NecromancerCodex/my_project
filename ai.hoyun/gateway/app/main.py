from fastapi import FastAPI, APIRouter  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from pydantic import BaseModel  # type: ignore
import uvicorn  # type: ignore
import httpx  # type: ignore

app = FastAPI(
    title="Gateway API",
    version="1.0.0",
    description="Gateway API 서버"
)

# CORS 설정 - React 프론트엔드(localhost:3000) 연결용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3000/home",
        "http://127.0.0.1:3000/home"
    ],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 루트 경로 - API 정보 반환
@app.get("/")
async def read_root():
    return {
        "message": "Gateway API is running",
        "docs": "/docs",
        "frontend": "React app should connect from http://localhost:3000"
    }

# Health check 엔드포인트
@app.get("/health")
async def health_check():
    """
    Health check 엔드포인트
    
    프론트엔드에서 서버 연결 상태를 확인하는 용도로 사용됩니다.
    """
    return {
        "status": "healthy",
        "service": "gateway",
        "message": "Gateway API is running"
    }

# 메인 라우터 생성
main_router = APIRouter()

# 챗봇 서비스 라우터 생성 및 연결
chatbot_router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# 요청/응답 모델 정의
class Message(BaseModel):
    """메시지 모델"""
    role: str  # "system", "user", "assistant"
    content: str

class ChatRequest(BaseModel):
    """챗봇 요청 모델"""
    message: str
    model: str = "gpt-3.5-turbo"
    system_message: str = "You are a helpful assistant. Respond in Korean."
    conversation_history: list[Message] = []  # 대화 히스토리 (선택사항)

class ChatResponse(BaseModel):
    """챗봇 응답 모델"""
    message: str
    model: str
    status: str = "success"

@chatbot_router.get("/chat")
async def chat():
    """
    챗봇 서비스 프록시 - 대화 (GET)
    
    기본 테스트용 엔드포인트입니다.
    
    - **반환**: 챗봇 응답 (기본 메시지)
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://chatbot-service:9001/chatbot/chat")
            
            if response.status_code != 200:
                error_data = response.json()
                error_message = error_data.get('detail', 'Unknown error occurred')
                return ChatResponse(
                    message=f"오류가 발생했습니다: {error_message}",
                    model="gpt-3.5-turbo",
                    status="error"
                )
            
            response_data = response.json()
            if 'message' in response_data and 'model' in response_data:
                return ChatResponse(
                    message=response_data.get('message', ''),
                    model=response_data.get('model', 'gpt-3.5-turbo'),
                    status=response_data.get('status', 'success')
                )
            else:
                return ChatResponse(
                    message=str(response_data),
                    model="gpt-3.5-turbo",
                    status="error"
                )
        except Exception as e:
            return ChatResponse(
                message=f"서버 연결 오류: {str(e)}",
                model="gpt-3.5-turbo",
                status="error"
            )

@chatbot_router.post("/chat")
async def chat_post(request: ChatRequest):
    """
    챗봇 서비스 프록시 - 대화 (POST)
    
    사용자 메시지를 받아 AI 챗봇 응답을 반환합니다.
    
    **요청 예시:**
    ```json
    {
        "message": "안녕하세요! 오늘 날씨 어때요?",
        "model": "gpt-3.5-turbo",
        "system_message": "You are a helpful assistant. Respond in Korean."
    }
    ```
    
    **응답 예시:**
    ```json
    {
        "message": "안녕하세요! 오늘 날씨에 대한 정보를 제공해드릴 수 없습니다...",
        "model": "gpt-3.5-turbo",
        "status": "success"
    }
    ```
    
    - **message** (필수): 사용자 메시지
    - **model** (선택): 사용할 모델 (기본값: gpt-3.5-turbo)
    - **system_message** (선택): 시스템 메시지 (기본값: "You are a helpful assistant. Respond in Korean.")
    
    - **반환**: 챗봇 응답
    """
    from fastapi import HTTPException  # type: ignore
    
    timeout = httpx.Timeout(60.0, connect=10.0)  # 1분 타임아웃
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                "http://chatbot-service:9001/chatbot/chat",
                json=request.dict()
            )
            
            # 에러 응답 처리
            if response.status_code != 200:
                error_data = response.json()
                error_message = error_data.get('detail', 'Unknown error occurred')
                
                # 에러 응답을 ChatResponse 형태로 변환
                return ChatResponse(
                    message=f"오류가 발생했습니다: {error_message}",
                    model=request.model,
                    status="error"
                )
            
            response_data = response.json()
            
            # 응답이 ChatResponse 형태인지 확인
            if 'message' in response_data and 'model' in response_data:
                return ChatResponse(
                    message=response_data.get('message', ''),
                    model=response_data.get('model', request.model),
                    status=response_data.get('status', 'success')
                )
            else:
                # 예상치 못한 응답 형태
                return ChatResponse(
                    message=str(response_data),
                    model=request.model,
                    status="error"
                )
                
        except httpx.RequestError as e:
            # 네트워크 오류
            return ChatResponse(
                message=f"서버 연결 오류: {str(e)}",
                model=request.model,
                status="error"
            )
        except Exception as e:
            # 기타 오류
            return ChatResponse(
                message=f"오류가 발생했습니다: {str(e)}",
                model=request.model,
                status="error"
            )

# 일기 서비스 라우터 생성 및 연결
diary_router = APIRouter(prefix="/diary", tags=["diary"])

@diary_router.get("/diaries")
async def get_diaries():
    """
    일기 서비스 프록시 - 일기 목록 조회
    
    - **반환**: 일기 목록
    """
    async with httpx.AsyncClient() as client:
        response = await client.get("http://diary-service:9002/diary/diaries")
        return response.json()

# 크롤러 서비스 라우터 생성 및 연결
crawler_router = APIRouter(prefix="/crawler", tags=["crawler"])

@crawler_router.get("/crawl")
async def crawl():
    """
    크롤러 서비스 프록시 - 크롤링 실행
    
    - **반환**: 크롤링 결과
    """
    async with httpx.AsyncClient() as client:
        response = await client.get("http://crawler-service:9003/crawler/crawl")
        return response.json()

@crawler_router.get("/bugsmusic")
async def bugsmusic():
    """
    벅스 실시간 차트 크롤링 프록시
    
    - **반환**: 벅스 실시간 차트 데이터 (순위, 제목, 아티스트, 앨범)
    """
    async with httpx.AsyncClient() as client:
        response = await client.get("http://crawler-service:9003/crawler/bugsmusic")
        return response.json()

@crawler_router.get("/danawa_tv")
async def danawa_tv():
    """
    다나와 TV 상품 목록 크롤링 프록시
    
    - **반환**: 다나와 TV 상품 데이터 (상품명, 가격, 판매처, 링크, 이미지)
    """
    async with httpx.AsyncClient() as client:
        response = await client.get("http://crawler-service:9003/crawler/danawa_tv")
        return response.json()

@crawler_router.get("/netflix")
async def netflix():
    """
    JustWatch Netflix 영화 산업 목록 크롤링 프록시
    
    - **반환**: Netflix 영화 데이터 (제목, 타입, 링크, 이미지)
    """
    # Netflix 크롤링은 Selenium 사용으로 시간이 오래 걸리므로 타임아웃을 길게 설정
    timeout = httpx.Timeout(300.0, connect=10.0)  # 5분 타임아웃
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get("http://crawler-service:9003/crawler/netflix")
        return response.json()

@crawler_router.get("/movie")
async def movie():
    """
    KMDB 뉴욕타임즈 21세기 영화 100선 크롤링 프록시
    
    - **반환**: 영화 데이터 (순위, 제목, 감독, 제작년도, 링크)
    """
    # Selenium 크롤링은 시간이 오래 걸리므로 타임아웃을 길게 설정
    timeout = httpx.Timeout(120.0, connect=10.0)  # 2분 타임아웃
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get("http://crawler-service:9003/crawler/movie")
        return response.json()

# 메인 라우터를 앱에 포함
app.include_router(main_router)
# 챗봇 라우터를 앱에 포함
app.include_router(chatbot_router)
# 일기 라우터를 앱에 포함
app.include_router(diary_router)
# 크롤러 라우터를 앱에 포함
app.include_router(crawler_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
