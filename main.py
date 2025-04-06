# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.db import meta, engine
from routes.user import UserAPI
from routes.post import PostAPI
from routes.profile import ProfileAPI
from routes.comments import CommentAPI
from routes.notifications import NotificationAPI
from middlewares.middlewares import refresh_db_session, handle_errors, log_requests_and_responses
from payment.payment import PaymentAPI
from routes.reports import ReportsAPI
from smtp.email import EmailAPI
from password.password_change import PasswordChangeAPI
from routes.recommendations import RecommendationsAPI
from routes.shared_images import CPwAPI

app = FastAPI(parse_json=True)

origins = [
    "http://localhost:80",
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8101",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(refresh_db_session)
app.middleware("http")(handle_errors)
app.middleware("http")(log_requests_and_responses)

app.include_router(UserAPI)
app.include_router(PostAPI)
app.include_router(ProfileAPI)
app.include_router(CommentAPI)
app.include_router(CPwAPI)
app.include_router(NotificationAPI)
app.include_router(PaymentAPI)
app.include_router(ReportsAPI)
app.include_router(EmailAPI)
app.include_router(PasswordChangeAPI)
app.include_router(RecommendationsAPI)


meta.create_all(engine)
