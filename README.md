# Character AI Clone 🤖

A full-stack AI character chat application that allows users to create, customize, and chat with unique AI personalities. Built with **FastAPI** and **Streamlit**, powered by **LangChain** and **Groq**.

## ✨ Features

*   **Create Custom Characters**: Define identity, personality, backstory, speaking style, and scenarios.
*   **Interactive Chat**: Real-time chat with persistent memory/history per session.
*   **User Authentication**: Secure Login and Signup system.
*   **Guest Mode**: Try out the app without creating an account (chats not saved).
*   **Dashboard**: Manage your characters and view available companions.
*   **Vector Search**: Uses ChromaDB for efficient context management.

## 🛠️ Tech Stack

*   **Frontend**: Streamlit
*   **Backend**: FastAPI
*   **Database**: SQLite (SQLAlchemy) & ChromaDB (Vector Store)
*   **AI Orchestration**: LangChain
*   **LLM Provider**: Groq
*   **Authentication**: JWT (JSON Web Tokens)

## 📂 Project Structure

```bash
/
├── app/                 # FastAPI Backend Code
│   ├── main.py          # Entry point
│   ├── routers/         # API Routes (auth, chat, characters)
│   ├── models.py        # Database Models
│   └── ...
├── frontend.py          # Streamlit Frontend Application
├── requirements.txt     # Python Dependencies
├── .env                 # Environment Variables
└── ...
```

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Character_AI_Version_1
```

### 2. Set Up Environment Variables

Create a `.env` file in the root directory and add your API keys:

```ini
# Example .env configuration
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_secret_key_for_jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Install Dependencies

It is recommended to use a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

## 🏃‍♂️ Usage

You need to run both the backend and frontend servers.

### 1. Run the Backend (FastAPI)

Open a terminal and run:

```bash
uvicorn app.main:app --reload
```
*The API will be available at `http://127.0.0.1:8000`*

### 2. Run the Frontend (Streamlit)

Open a **new** terminal window and run:

```bash
streamlit run frontend.py
```

*The application will open in your browser at `http://localhost:8501`*

## 🧪 Testing

You can access the automatic API documentation provided by FastAPI at:
`http://127.0.0.1:8000/docs`

## 📝 License

This project is for educational purposes.
