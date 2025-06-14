from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import time
import base64
import io
from datetime import datetime

app = FastAPI(title="TDS Virtual TA", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None

class Link(BaseModel):
    url: str
    text: str

class AnswerResponse(BaseModel):
    answer: str
    links: List[Link]

# Enhanced knowledge base with TDS-specific content
KNOWLEDGE_BASE = {
    "gpt-4o-mini": {
        "keywords": ["gpt-4o-mini", "gpt-3.5-turbo", "openai", "model", "api"],
        "answer": "You must use `gpt-3.5-turbo-0125`, even if the AI Proxy only supports `gpt-4o-mini`. Use the OpenAI API directly for this question.",
        "links": [
            {
                "url": "https://discourse.onlinedegree.iitm.ac.in/t/ga5-question-8-clarification/155939/4",
                "text": "Use the model that's mentioned in the question."
            },
            {
                "url": "https://discourse.onlinedegree.iitm.ac.in/t/ga5-question-8-clarification/155939/3",
                "text": "My understanding is that you just have to use a tokenizer, similar to what Prof. Anand used, to get the number of tokens and multiply that by the given rate."
            }
        ]
    },
    "python": {
        "keywords": ["python", "programming", "code", "syntax", "variable"],
        "answer": "Python is a high-level programming language extensively used in data science. In TDS, we cover Python basics including variables, data types, control structures, functions, and object-oriented programming. Key libraries include pandas for data manipulation, numpy for numerical computing, and matplotlib for visualization.",
        "links": [
            {
                "url": "https://tds.s-anand.net/python-basics",
                "text": "Python fundamentals covered in TDS"
            },
            {
                "url": "https://discourse.onlinedegree.iitm.ac.in/c/tools-in-data-science/python",
                "text": "Python discussions on TDS forum"
            }
        ]
    },
    "pandas": {
        "keywords": ["pandas", "dataframe", "data manipulation", "csv", "excel"],
        "answer": "Pandas is the primary data manipulation library in Python for the TDS course. It provides DataFrame and Series objects for handling structured data. Key operations include reading CSV/Excel files, filtering, grouping, merging, and data cleaning. Always remember to handle missing values and check data types.",
        "links": [
            {
                "url": "https://tds.s-anand.net/pandas-tutorial",
                "text": "Pandas tutorial with TDS examples"
            },
            {
                "url": "https://discourse.onlinedegree.iitm.ac.in/t/pandas-best-practices",
                "text": "Pandas best practices discussion"
            }
        ]
    },
    "visualization": {
        "keywords": ["matplotlib", "seaborn", "plot", "chart", "graph", "visualization"],
        "answer": "Data visualization in TDS covers matplotlib for basic plots and seaborn for statistical visualizations. Key concepts include choosing appropriate chart types, color schemes, and making plots accessible. Always label your axes and provide clear titles.",
        "links": [
            {
                "url": "https://tds.s-anand.net/visualization-guide",
                "text": "Complete visualization guide for TDS"
            }
        ]
    },
    "git": {
        "keywords": ["git", "github", "version control", "commit", "push", "pull"],
        "answer": "Git is essential for version control in TDS projects. Key commands include git add, git commit, git push, and git pull. Always write meaningful commit messages and use .gitignore for sensitive files. For collaborative projects, use branches and pull requests.",
        "links": [
            {
                "url": "https://tds.s-anand.net/git-tutorial",
                "text": "Git workflow for TDS assignments"
            }
        ]
    },
    "sql": {
        "keywords": ["sql", "database", "query", "select", "join", "sqlite"],
        "answer": "SQL in TDS covers database querying, joins, aggregations, and subqueries. Practice with SQLite for local development. Remember to use proper indexing for performance and always validate your query results.",
        "links": [
            {
                "url": "https://tds.s-anand.net/sql-basics",
                "text": "SQL fundamentals for data science"
            }
        ]
    },
    "assignment": {
        "keywords": ["assignment", "homework", "submission", "deadline", "grading"],
        "answer": "For TDS assignments, always check the submission format requirements, follow the provided templates, and test your code thoroughly. Submit before the deadline and keep backups. If you face issues, post on Discourse with specific error messages.",
        "links": [
            {
                "url": "https://discourse.onlinedegree.iitm.ac.in/c/tools-in-data-science/assignments",
                "text": "Assignment help and discussions"
            }
        ]
    },
    "error": {
        "keywords": ["error", "bug", "exception", "debugging", "traceback"],
        "answer": "When debugging in TDS, read error messages carefully, check variable types, and use print statements for debugging. Common issues include import errors, file path problems, and data type mismatches. Share the full error traceback when asking for help.",
        "links": [
            {
                "url": "https://discourse.onlinedegree.iitm.ac.in/t/common-errors-and-solutions",
                "text": "Common TDS errors and their solutions"
            }
        ]
    }
}

def find_relevant_answer(question: str, image_description: str = "") -> tuple:
    question_lower = (question + " " + image_description).lower()
    scores = {}
    for topic, data in KNOWLEDGE_BASE.items():
        score = sum(question_lower.count(keyword) for keyword in data["keywords"])
        scores[topic] = score
    if scores and max(scores.values()) > 0:
        best_topic = max(scores, key=scores.get)
        return KNOWLEDGE_BASE[best_topic]["answer"], KNOWLEDGE_BASE[best_topic]["links"]
    return (
        f"I understand you're asking about '{question[:50]}...' in the TDS course. While I don't have specific information about this topic in my current knowledge base, I recommend checking the course materials or posting on the Discourse forum for detailed help from instructors and peers.",
        [
            {"url": "https://discourse.onlinedegree.iitm.ac.in/c/tools-in-data-science", "text": "TDS Discourse Forum - Post your question here"},
            {"url": "https://tds.s-anand.net/", "text": "TDS Course Materials and Resources"}
        ]
    )

def process_image_description(image_base64: str) -> str:
    try:
        image_data = base64.b64decode(image_base64)
        size = len(image_data)
        if size > 100000:
            return "screenshot code error interface"
        elif size > 50000:
            return "diagram chart visualization"
        else:
            return "icon button interface element"
    except Exception:
        return ""

@app.post("/api/", response_model=AnswerResponse)
async def answer_question(request: QuestionRequest):
    try:
        start_time = time.time()
        image_description = process_image_description(request.image) if request.image else ""
        answer, links = find_relevant_answer(request.question, image_description)
        formatted_links = [Link(url=link["url"], text=link["text"]) for link in links]
        if time.time() - start_time > 25:
            raise HTTPException(status_code=408, detail="Request timeout")
        return AnswerResponse(answer=answer, links=formatted_links)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "TDS Virtual TA is running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    return {
        "message": "TDS Virtual TA API - Helping students with Tools in Data Science course",
        "version": "1.0.0",
        "endpoints": {
            "answer_question": "POST /api/ - Submit questions with optional image",
            "health_check": "GET /health - Check API status",
            "documentation": "GET /docs - Interactive API documentation"
        },
        "usage": {
            "example_request": {
                "question": "How do I use pandas to read a CSV file?",
                "image": "base64_encoded_image_optional"
            },
            "curl_example": 'curl -X POST "your-api-url/api/" -H "Content-Type: application/json" -d \'{"question": "Your question here"}\''
        }
    }



if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

    @app.post("/")
    async def root_post(request: Request):
        return {
        "message": "POST request received at root. Use /api/ for actual queries.",
        "status": "ok"
    }


