import asyncio
from datetime import datetime, timedelta
import sys
sys.path.append('C:/Users/Leandro/Documents/Developing/project-d/API (2)')
from config.db import Session
from models.user import User
from models.post import Post
from models.profile import Profile  # Importa Profile
from models.reports import Report  # Importa Report

async def check_membership():
    while True:
        await asyncio.sleep(10)  # Espera 60 segundos
        with Session() as session:
            current_date = datetime.utcnow()
            expired_users = session.query(User).filter(User.expiration_date <= current_date, User.is_paid == True).all()
            for user in expired_users:
                user.is_paid = False
            session.commit()
            with open("checker_log.txt", "a") as log_file:
                log_file.write(f"Membership check executed at: {datetime.utcnow()}\n")
                log_file.flush()

if __name__ == "__main__":
    asyncio.run(check_membership())

