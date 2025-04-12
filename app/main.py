import os
from fastapi import FastAPI, Request, Depends ,HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi import status
from pydantic import BaseModel
from contextlib import asynccontextmanager
from utils import hash_password, verify_password
from db import Database
from auth import create_access_token, verify_token
from fastapi.security import OAuth2PasswordBearer
from generate_url_code import get_url_code
import random
from fastapi.responses import RedirectResponse
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Starting up...")
    db = Database()
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """ 
                SELECT id FROM ticketing 
                WHERE current <> range_end;
            """
            )
            app.state.avail_range = [row[0] for row in cur.fetchall()]
    app.state.name = "Url shortener"
    app.state.db = db

    yield  # The application is running at this point

    print("Shutting down...")
    db.close_all_connections()
    del app.state.name


app = FastAPI(lifespan=lifespan)


def get_db_connection(request: Request):
    return request.app.state.db


def get_avaiable_range_list(request: Request):
    return request.app.state.avail_range

def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db_connection)) -> dict:
    payload = verify_token(token) 
    username = payload.get("sub")
    
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate the credentials"
        )
    
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """ 
                    SELECT id, username, avatar, created_at, updated_at 
                    FROM users 
                    WHERE username = %s;
                    """,
                    (username,)
                )
                
                user = cur.fetchone()
                
                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                
                # Return the user data as a dictionary
                user_data = {
                    "id": user[0],
                    "username": user[1],
                    "avatar": user[2],
                    "created_at": user[3],
                    "updated_at": user[4]
                }
                return user_data
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error retrieving user: {str(e)}"
                )

                
class RegisterForm(BaseModel):
    username: str
    password: str
    avatar: str | None = None


class LoginForm(BaseModel):
    username: str
    password: str


@app.post("/register")
async def register(form: RegisterForm, db=Depends(get_db_connection)):
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            try:
                # Check if the user already exists
                cur.execute(
                    """ 
                    SELECT id FROM users WHERE username = %s;
                    """,
                    (form.username,)
                )
                user = cur.fetchone()
                if user:
                    return JSONResponse(
                        {"message": "User Already Exists."},
                        status_code=status.HTTP_409_CONFLICT,
                    )

                # Insert the new user into the database
                cur.execute(
                    """
                    INSERT INTO users(username, password, avatar)
                    VALUES (%s, %s, %s) RETURNING id;
                    """,
                    (form.username, hash_password(form.password), form.avatar)
                )
                conn.commit()
                
                user_id = cur.fetchone()[0]
                return JSONResponse(
                    {"message": "User Created Successfully.", "user_id": user_id},
                    status_code=status.HTTP_201_CREATED,
                )
            except Exception as e:
                print(e)
                return JSONResponse(
                    {"message": f"Error: {str(e)}"},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )


@app.post("/login")
async def login(form: LoginForm, db=Depends(get_db_connection)):
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """ 
                    SELECT id, password FROM users WHERE username = %s;
                    """,
                    (form.username,)
                )
                user = cur.fetchone()

                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Incorrent Username or Password",
                    )

                stored_password = user[1]
                if not verify_password(form.password, stored_password):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Incorrent Username or Password",
                    )

                access_token = create_access_token(
                    data={"sub": form.username}
                )

                return JSONResponse(
                    {"message": "Login successful", "access_token": access_token, "token_type": "bearer"},
                    status_code=status.HTTP_200_OK,
                )

            except Exception as e:
                print(e)
                return JSONResponse(
                    {"message": f"Error: {str(e)}"},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )


            


            
@app.post("/generate_url")
async def protected_route(url : str = Query, current_user: dict = Depends(get_current_user), db = Depends(get_db_connection) , avail_range = Depends(get_avaiable_range_list)):
    idx = random.randint(0,len(avail_range) - 1)

    
    with db.get_connection() as conn:
        with conn.cursor() as cur:


            try:

                cur.execute("begin;")
                cur.execute("""
                    SELECT current FROM ticketing 
                    WHERE id = %s AND current <= range_end 
                    FOR UPDATE;
                """, (idx,))

                cur.execute("""
                    UPDATE ticketing SET current = current + 1 
                    WHERE id = %s AND current < range_end RETURNING current - 1;
                """, (idx,))

                current_value = cur.fetchone()[0]
                
                cur.execute("""
                    INSERT INTO tiny_url(user_id,url,url_code) VALUES (%s,%s,%s) returning url_code;        
                """ ,(current_user['id'],url,get_url_code(current_value))
                    )

                url_code = cur.fetchone()[0]
                short_url =f"http://{os.getenv('HOST')}:{os.getenv('PORT')}/{url_code}"
                conn.commit()

                return JSONResponse(
                    {"url" : url,"short_url" : short_url},
                    status_code=status.HTTP_201_CREATED,
                )

            except Exception as e:
                    conn.rollback()
                    print("Error:", e)


@app.get("/{short_code}")
async def resolve_short_url(short_code: str, db = Depends(get_db_connection)):     
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    SELECT url FROM tiny_url 
                    where url_code = %s
                """, (short_code,))
                url = cur.fetchone()[0]
                return RedirectResponse(url=url)

            except Exception as e:
                print(e)
                return JSONResponse(
                    {"message": f"Error: {str(e)}"},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            
    return JSONResponse(
        "Invalid Url",
        status_code=status.HTTP_404_NOT_FOUND
    )

if "__main__" == __name__:
    import uvicorn

    print(f"Starting Server at http://{os.getenv('HOST')}:{os.getenv('PORT')}")
    uvicorn.run("main:app", port=8080, reload=True, workers=4)
