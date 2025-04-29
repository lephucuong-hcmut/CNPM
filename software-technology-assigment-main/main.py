from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from api.api_v1.api import router as api_router
from config import ALLOWED_HOSTS, API_V1_STR, PROJECT_NAME
from db.mongodb_utils import close_mongo_connection, connect_to_mongo
from fastapi_pagination import add_pagination


app = FastAPI(title=PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)


@app.get("/")
def health_check():
    print("Health check endpoint called")
    return {"message": "healcheck ok!"}


app.include_router(api_router, prefix=API_V1_STR)

add_pagination(app)
