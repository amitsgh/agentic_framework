"""FastAPI Application"""

import warnings
warnings.filterwarnings("ignore", message=".*ResourceTracker.*")
warnings.filterwarnings("ignore", category=ResourceWarning)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import register_routers

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routers(app)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "LLM Application", "status": "healty"}


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
