from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .database import engine, SessionLocal
from app.models import Base, User

# Проверяем, что таблица создается только один раз
Base.metadata.create_all(bind=engine)

app = FastAPI()


class UserCreate(BaseModel):
    username: str
    password: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/register/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = User(username=user.username, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/highscores/")
def read_highscores(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.highscore.desc()).offset(skip).limit(limit).all()
    return users


@app.post("/update_score/")
def update_score(username: str, score: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if score > db_user.highscore:
        db_user.highscore = score
        db.commit()
        db.refresh(db_user)
    return db_user


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
