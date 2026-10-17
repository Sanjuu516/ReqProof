from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserRegister, UserLogin, UserResponse, Token, ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth_service import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=hash_password(user_in.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.user_id, "email": user.email})
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    token = create_access_token({"sub": user.user_id, "email": user.email})
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

@router.post("/forgot-password")
def forgot_password(
    req: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    from app.services.auth_service import create_password_reset_token
    from app.services.email_service import send_password_reset_email

    user = db.query(User).filter(User.email == req.email.strip()).first()
    if not user:
        # Avoid user enumeration while still returning a friendly message
        return {
            "message": "If this email is registered, a password reset link has been dispatched.",
            "delivered": False
        }

    token = create_password_reset_token(user.email)
    frontend_base = "http://localhost:5173"
    reset_url = f"{frontend_base}/reset-password?token={token}"

    result = send_password_reset_email(user.email, reset_url)
    return {
        "message": f"Password reset instructions have been sent to {user.email}.",
        "delivery": result
    }

@router.post("/reset-password")
def reset_password(
    req: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    from app.services.auth_service import verify_password_reset_token, hash_password

    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters long.")

    email = verify_password_reset_token(req.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired password reset token.")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    user.password_hash = hash_password(req.new_password)
    db.commit()

    return {"message": "Password successfully updated! You can now log in with your new credentials."}

