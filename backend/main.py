from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.topics import router as topics_router
from routes.upload import router as upload_router
from routes.companies import router as companies_router
from routes.analytics import router as analytics_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://epa-bachelorprojekt.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(topics_router)
app.include_router(upload_router)
app.include_router(companies_router)
app.include_router(analytics_router)


@app.get("/api/hello")
def hello():
    return {"message": "Hallo von FastAPI"}
