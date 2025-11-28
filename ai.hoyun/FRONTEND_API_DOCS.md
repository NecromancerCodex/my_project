# 프론트엔드 API 문서

## 기본 정보

- **게이트웨이 URL**: `http://localhost:9000`
- **API 문서 (Swagger UI)**: `http://localhost:9000/docs`
- **API 문서 (ReDoc)**: `http://localhost:9000/redoc`

## 챗봇 API

### POST `/chatbot/chat` - 챗봇 대화

사용자 메시지를 받아 AI 챗봇 응답을 반환합니다. 대화 히스토리를 포함하여 연속적인 대화가 가능합니다.

**요청 URL:**
```
POST http://localhost:9000/chatbot/chat
```

**요청 헤더:**
```
Content-Type: application/json
```

**요청 본문:**
```json
{
    "message": "안녕하세요! 오늘 날씨 어때요?",
    "model": "gpt-3.5-turbo",
    "system_message": "You are a helpful assistant. Respond in Korean.",
    "conversation_history": [
        {
            "role": "user",
            "content": "안녕"
        },
        {
            "role": "assistant",
            "content": "안녕하세요! 무엇을 도와드릴까요?"
        }
    ]
}
```

**요청 필드:**
- `message` (필수, string): 사용자 메시지
- `model` (선택, string): 사용할 모델 (기본값: "gpt-3.5-turbo")
- `system_message` (선택, string): 시스템 메시지 (기본값: "You are a helpful assistant. Respond in Korean.")
- `conversation_history` (선택, array): 이전 대화 히스토리
  - 각 항목은 `{ "role": "user" | "assistant", "content": string }` 형태

**응답 예시:**
```json
{
    "message": "안녕하세요! 오늘 날씨에 대한 정보를 제공해드릴 수 없습니다...",
    "model": "gpt-3.5-turbo",
    "status": "success"
}
```

**에러 응답:**
```json
{
    "detail": "OpenAI API key not configured..."
}
```

### GET `/chatbot/chat` - 챗봇 대화 (테스트용)

기본 테스트용 엔드포인트입니다.

**요청 URL:**
```
GET http://localhost:9000/chatbot/chat
```

**응답 예시:**
```json
{
    "message": "안녕하세요! 오늘 날씨 어때요?",
    "model": "gpt-3.5-turbo",
    "status": "success"
}
```

## React 사용 예시

### 1. 기본 사용 (대화 히스토리 없음)

```javascript
const sendMessage = async (message) => {
    try {
        const response = await fetch('http://localhost:9000/chatbot/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                model: 'gpt-3.5-turbo'
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.message;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
};
```

### 2. 대화 히스토리 포함 (권장)

```javascript
// 대화 히스토리 저장
let conversationHistory = [];

const sendMessage = async (message) => {
    try {
        const response = await fetch('http://localhost:9000/chatbot/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                model: 'gpt-3.5-turbo',
                system_message: 'You are a helpful assistant. Respond in Korean.',
                conversation_history: conversationHistory
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // 대화 히스토리에 추가
        conversationHistory.push(
            { role: 'user', content: message },
            { role: 'assistant', content: data.message }
        );
        
        return data.message;
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
};

// 대화 초기화
const clearHistory = () => {
    conversationHistory = [];
};
```

### 3. React Hook 예시

```jsx
import { useState, useCallback } from 'react';

function useChatbot() {
    const [conversationHistory, setConversationHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const sendMessage = useCallback(async (message) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch('http://localhost:9000/chatbot/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    model: 'gpt-3.5-turbo',
                    system_message: 'You are a helpful assistant. Respond in Korean.',
                    conversation_history: conversationHistory
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // 대화 히스토리 업데이트
            setConversationHistory(prev => [
                ...prev,
                { role: 'user', content: message },
                { role: 'assistant', content: data.message }
            ]);
            
            return data.message;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [conversationHistory]);

    const clearHistory = useCallback(() => {
        setConversationHistory([]);
    }, []);

    return { sendMessage, clearHistory, loading, error, conversationHistory };
}

// 사용 예시
function ChatComponent() {
    const { sendMessage, clearHistory, loading, error } = useChatbot();
    const [input, setInput] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;
        
        try {
            const response = await sendMessage(input);
            console.log('응답:', response);
            setInput('');
        } catch (err) {
            console.error('오류:', err);
        }
    };

    return (
        <div>
            <form onSubmit={handleSubmit}>
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="메시지를 입력하세요..."
                    disabled={loading}
                />
                <button type="submit" disabled={loading}>
                    {loading ? '전송 중...' : '전송'}
                </button>
            </form>
            {error && <div>오류: {error}</div>}
            <button onClick={clearHistory}>대화 초기화</button>
        </div>
    );
}
```

### 4. Axios 사용 예시

```javascript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:9000';

const chatbotAPI = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

let conversationHistory = [];

const sendMessage = async (message) => {
    try {
        const response = await chatbotAPI.post('/chatbot/chat', {
            message: message,
            model: 'gpt-3.5-turbo',
            system_message: 'You are a helpful assistant. Respond in Korean.',
            conversation_history: conversationHistory
        });
        
        // 대화 히스토리 업데이트
        conversationHistory.push(
            { role: 'user', content: message },
            { role: 'assistant', content: response.data.message }
        );
        
        return response.data.message;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
        throw error;
    }
};
```

## 타입 정의 (TypeScript)

```typescript
interface Message {
    role: 'user' | 'assistant';
    content: string;
}

interface ChatRequest {
    message: string;
    model?: string;
    system_message?: string;
    conversation_history?: Message[];
}

interface ChatResponse {
    message: string;
    model: string;
    status: string;
}

const sendMessage = async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await fetch('http://localhost:9000/chatbot/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request)
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
};
```

## 주의사항

1. **CORS**: 게이트웨이는 `localhost:3000`에서의 요청을 허용하도록 설정되어 있습니다.
2. **타임아웃**: API 요청은 최대 60초까지 대기합니다.
3. **에러 처리**: API 키가 없거나 할당량이 부족한 경우 에러가 반환됩니다.
4. **대화 히스토리**: 연속적인 대화를 위해서는 `conversation_history`를 유지해야 합니다.

## 테스트

브라우저에서 다음 URL로 API 문서를 확인할 수 있습니다:
- Swagger UI: `http://localhost:9000/docs`
- ReDoc: `http://localhost:9000/redoc`

## 연결 문제 해결 가이드

### 현재 에러: "Failed to fetch" 또는 CORS 오류

이 에러는 **백엔드 서버가 실행되지 않았거나 연결할 수 없을 때** 발생합니다.

### 빠른 진단 방법

#### 1. 브라우저에서 직접 확인

브라우저 주소창에 다음 URL을 입력해보세요:

```
http://localhost:9000/docs
```

또는

```
http://localhost:9000/
```

**결과:**
- ✅ **페이지가 열리면**: 백엔드 서버는 실행 중입니다 (CORS 문제일 수 있음)
- ❌ **연결할 수 없음**: 백엔드 서버가 실행되지 않았습니다

#### 2. 터미널에서 확인 (PowerShell)

```powershell
# 9000번 포트가 사용 중인지 확인
netstat -ano | findstr :9000

# Docker 컨테이너 상태 확인
docker-compose ps
```

#### 3. 브라우저 개발자 도구 확인

1. **F12** 키를 눌러 개발자 도구 열기
2. **Console** 탭 확인:
   - CORS 관련 에러 메시지가 있는지 확인
   - 네트워크 에러 메시지 확인
3. **Network** 탭 확인:
   - 메시지 전송 시도
   - `chatbot/chat` 요청 확인
   - 요청 상태 확인 (Failed, CORS error 등)

### 가능한 원인과 해결 방법

#### 원인 1: 백엔드 서버가 실행되지 않음 ⚠️ (가장 흔함)

**증상:**
- 브라우저에서 `http://localhost:9000/docs` 접속 불가
- "연결할 수 없음" 또는 "ERR_CONNECTION_REFUSED" 에러

**해결 방법:**

이 프로젝트는 Docker Compose로 실행됩니다:

```bash
# 프로젝트 루트 디렉토리에서
docker-compose up -d

# 또는 특정 서비스만 실행
docker-compose up -d gateway chatbot-service

# 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs gateway
docker-compose logs chatbot-service
```

**서비스가 정상 실행 중인지 확인:**
```bash
# 게이트웨이 로그 확인
docker-compose logs gateway --tail 20

# 챗봇 서비스 로그 확인
docker-compose logs chatbot-service --tail 20
```

#### 원인 2: CORS 설정 문제

**증상:**
- 브라우저 콘솔에 CORS 에러 메시지
- `http://localhost:9000/docs`는 접속 가능하지만 API 호출 실패

**해결 방법:**

게이트웨이의 CORS 설정이 `http://localhost:3000`을 허용하도록 설정되어 있는지 확인:

1. `gateway/app/main.py` 파일 확인
2. CORS 설정에 `http://localhost:3000`이 포함되어 있는지 확인
3. 게이트웨이 재빌드:
   ```bash
   docker-compose up --build -d gateway
   ```

#### 원인 3: 포트 충돌

**증상:**
- 다른 프로세스가 9000번 포트를 사용 중

**해결 방법:**

```powershell
# 9000번 포트를 사용하는 프로세스 확인
netstat -ano | findstr :9000

# 프로세스 ID 확인 후 종료 (PID는 위 명령어 결과에서 확인)
taskkill /PID [프로세스ID] /F
```

또는 Docker 컨테이너가 이미 실행 중인 경우:

```bash
# 기존 컨테이너 중지 및 제거
docker-compose down

# 다시 시작
docker-compose up -d
```

#### 원인 4: 환경 변수 문제

**증상:**
- 서버는 실행되지만 API 호출 시 에러 발생
- "OpenAI API key not configured" 에러

**해결 방법:**

1. `.env` 파일 확인 (프로젝트 루트에 있어야 함):
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

2. Docker Compose에서 환경 변수 전달 확인:
   - `docker-compose.yaml`에서 `environment` 섹션 확인

3. 컨테이너 재시작:
   ```bash
   docker-compose restart chatbot-service
   ```

### 백엔드 서버 실행 확인 체크리스트

- [ ] Docker가 실행 중인지 확인
- [ ] 프로젝트 루트 디렉토리에서 `docker-compose up -d` 실행
- [ ] `docker-compose ps`로 모든 서비스가 실행 중인지 확인
- [ ] `http://localhost:9000/docs` 접속 가능한지 확인
- [ ] `.env` 파일에 `OPENAI_API_KEY`가 설정되어 있는지 확인
- [ ] CORS 설정에 `http://localhost:3000`이 포함되어 있는지 확인

### 프론트엔드에서 확인할 수 있는 것

프론트엔드 코드는 올바르게 설정되어 있습니다:
- ✅ API URL: `http://localhost:9000`
- ✅ 엔드포인트: `/chatbot/chat`
- ✅ 요청 형식: 올바름
- ✅ 에러 처리: 구현됨

**문제는 백엔드 서버 실행 또는 CORS 설정에 있을 가능성이 높습니다.**

### 다음 단계

1. **Docker 서비스 실행 확인**
   ```bash
   docker-compose ps
   docker-compose logs gateway
   ```

2. **게이트웨이 접속 테스트**
   - 브라우저에서 `http://localhost:9000/docs` 접속
   - Swagger UI가 표시되는지 확인

3. **CORS 설정 확인**
   - `gateway/app/main.py`에서 CORS 설정 확인
   - 필요시 재빌드: `docker-compose up --build -d gateway`

4. **브라우저 콘솔 확인**
   - F12 → Console 탭
   - 에러 메시지 확인
   - Network 탭에서 요청 상태 확인

5. **환경 변수 확인**
   - `.env` 파일 확인
   - `OPENAI_API_KEY` 설정 확인

