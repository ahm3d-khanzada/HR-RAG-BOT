# HR Document & Query System

A secure, role-based HR management and knowledge system with document upload, RAG-powered chat assistant, and user management — built with **FastAPI** (backend) + **Streamlit** (frontend) and **Pinecone + OpenAI** for intelligent document search.

## Features

- **Role-based access control** (RBAC) with 4 roles:
  - **Employee** — unlimited users, basic policy access
  - **Team Lead** — max 4, can delete their own team employees
  - **HR Executive** — can delete any user
  - **HR Manager** — only 1 allowed, can upload documents
- **Document upload & indexing** (PDF, DOCX, TXT) → HR Manager only
- **Permanent document access** — uploaded docs remain queryable until explicitly deleted by HR Executive/Manager
- **Intelligent HR Chat** — role-filtered RAG answers using Pinecone vector search + OpenAI LLM
- **User authentication** — signup, email verification, forgot/reset password
- **Delete users** — HR Executive can delete any user (except self)
- **Progress bar** during document upload
- **Typewriter chat effect** for better UX
- **Safe logout** — survives page reload (persistent session)

## Tech Stack

**Backend**
- FastAPI
- MongoDB (user data)
- Pinecone (vector database for RAG)
- OpenAI Embeddings & GPT-4o-mini (LLM)
- itsdangerous (token generation)
- aiosmtplib (email sending)

**Frontend**
- Streamlit
- requests + HTTPBasicAuth

**Other**
- LangChain (document loading, splitting, chaining)
- PyPDFLoader, RecursiveCharacterTextSplitter
- tqdm (progress bars)

## Project Structure
```bash
HR-RAG-BOT/
├── SERVER/
│   ├── main.py
│   ├── auth/
│   │   ├── routes.py
│   │   ├── models.py
│   │   ├── hash_utils.py
│   ├── docs/
│   │   ├── routes.py
│   │   ├── vectorstore.py
│   ├── chat/
│   │   ├── chat_query.py
|   |   ├── models.py
|   |   ├── routes.py
│   ├── config/
│   │   ├── db.py
│   ├── utils/
│   │   ├── email_utils.py
│   └── requirements.txt
└── CLIENT/
└── main.py.py
```

## Installation & Setup

### Prerequisites

- Python 3.10+
- MongoDB running locally or cloud (MongoDB Atlas)
- Pinecone account + API key
- OpenAI API key
- Gmail account for email sending (or any SMTP)

### Backend Setup

1. Clone repo
```bash
git clone <your-repo-url>
```
2. Go to the Backend
```bash
cd HR-RAG-BOT/SERVER
```
3. Create and Activate venv
```bash
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows
```
4. Install dependencies
```bash
pip install -r requirements.txt
```
5. Create `.env` file in `SERVER/`
```bash
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=hr-system-index
SENDER_EMAIL=your@gmail.com
SENDER_PASSWORD=your-app-password
SECRET_KEY=your-secret-key-here
MONGODB_URI=mongodb://localhost:27017/hr_system   # or Atlas URI
```
6. Run backend
```bash
uvicorn main:app --reload --port 8000
```
### Frontend Setup
1. Go to CLIENT folder
```bash
cd ../frontend
```
2. Install Streamlit (if not already)
```bash
pip install streamlit requests
```
3. Run Streamlit app
```bash
streamlit run main.py
```
**Usage Flow**

- Sign Up → choose role, for Employee add valid Team Lead username
- Verify email → click link from email
- Login
- HR Manager → upload documents (progress bar shown)
- Ask questions in chat → answers from role-accessible docs only
- HR Executive → delete any user
- Team Lead → delete own team employees
- Logout → session cleared

**Future Improvements**

- Real document delete endpoint (Pinecone delete by filter)
- User list view for HR Executive
- Team-based filtering UI
- JWT instead of Basic Auth
- Docker + deployment (Render/Vercel/Fly.io)

