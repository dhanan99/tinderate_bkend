# curl -X GET "https://cm9tkdbh-8000.inc1.devtunnels.ms/" -H "accept: application/json"
# curl -X GET "https://cm9tkdbh-8000.inc1.devtunnels.ms/users/me" -H "accept: application/json"
# curl -X POST "https://cm9tkdbh-8000.inc1.devtunnels.ms/token" -H "accept: application/json" -H "Content-Type: application/x-www-form-urlencoded" -d "grant_type=&username=admin&password=admin&scope=&client_id=&client_secret="

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Form
from pydantic import BaseModel, EmailStr
from typing import Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
import string

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific origins as needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# OAuth2 token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Fake database
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "John Doe",
        "email": "dhananjayhrssss@gmail.com",
        "hashed_password": pwd_context.hash("admin"),
        "disabled": False,
    }
}

# Fake database to store confirmation codes
confirmation_codes = {}

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

def get_user(db, email: str):
    for user in db.values():
        if user['email'] == email:
            return user
    return None
def save_user(db, user: User):
    db[user.username] = user.dict()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def generate_confirmation_code(length=6):
    """Generate a random confirmation code."""
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))

def send_email(email: str, subject: str, message: str):
    """Send an email to a specific address."""
    from_email = "konets567@gmail.com"
    from_password = "ppvfzzytoyletwyw"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))
                    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, from_password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.get("/")
async def home():
    return {"message": "Hello, World!"}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    print(user)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(token: str = Depends(oauth2_scheme)):
    user = get_user(fake_users_db, token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

@app.post("/send-confirmation-code")
async def send_confirmation_code(email: EmailStr, background_tasks: BackgroundTasks):
    confirmation_code = generate_confirmation_code()
    confirmation_codes[email] = confirmation_code
    subject = "Your Confirmation Code"
    message = f"Your confirmation code is: {confirmation_code}"
    background_tasks.add_task(send_email, email, subject, message)
    return {"message": "Confirmation code sent"}

@app.post("/verify-confirmation-code")
async def verify_confirmation_code(email: EmailStr = Form(...), confirmation_code: str = Form(...), password: str = Form(...)):
    user = get_user(fake_users_db, email)
    print(fake_users_db)
    if user and confirmation_codes.get(email) == confirmation_code:
        user['hashed_password'] = pwd_context.hash(password)  # Update the password
        save_user(fake_users_db, User(**user))
        del confirmation_codes[email]  # Optionally delete the used code
        print(user)
        return {"message": "Confirmation code verified and password updated"}
    else:
        raise HTTPException(status_code=400, detail="Invalid confirmation code")
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
