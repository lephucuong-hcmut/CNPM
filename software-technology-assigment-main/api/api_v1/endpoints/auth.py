import random
from fastapi import APIRouter, Header, HTTPException, status, Depends
from models.user import CreateUserRequest
from models.user import User
from utils import hash_password, verify_password, create_access_token
from ..deps import admin_required
from typing import List


router = APIRouter(prefix="/auth")

@router.post(
    "/signup/admin",
)
async def create_admin_user(
    create_admin_user: CreateUserRequest
):
    try:
        existing = await User.find_one(User.email == create_admin_user.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        new_user = User(
            user_id=str(random.randint(1000000, 9999999)),
            user_name=create_admin_user.user_name,
            email=create_admin_user.email,
            phone_number=create_admin_user.phone_number,
            password=hash_password(create_admin_user.password),
            role="admin",
        )
        await new_user.insert()
        return {"message": "Admin user created successfully"}
    except Exception as e:
        raise e

@router.get(
    "/signin/admin",
)
async def signin_admin_user(
    email: str = Header(..., description="Email"),
    password: str = Header(..., description="Password"),
):
    try:
        user = await User.find_one(User.email == email)
        if not user or not verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="User name or password is incorrect!")

        token = create_access_token(data={"sub": user.user_id, "role": user.role})
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        raise e


@router.get(
    "/signin/student",
)
async def signin_student_user(
    email: str = Header(..., description="Email"),
    password: str = Header(..., description="Password"),
):
    try:
        user = await User.find_one(User.email == email)
        if not user or not verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="User name or password is incorrect!")

        token = create_access_token(data={"sub": user.user_id, "role": user.role})
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        raise e

@router.post(
    "/signup/student",
)
async def create_student_user(
    create_student_user: CreateUserRequest
):
    try:
        existing = await User.find_one(User.email == create_student_user.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        new_user = User(
            user_id=str(random.randint(1000000, 9999999)),
            user_name=create_student_user.user_name,
            email=create_student_user.email,
            phone_number=create_student_user.phone_number,
            password=hash_password(create_student_user.password),
            role="student",  # khác admin chỗ này
        )
        await new_user.insert()
        return {"message": "Student user created successfully"}
    except Exception as e:
        raise e

@router.get(
    "/users",
    response_model=List[User]
)
async def get_all_users(
     user: dict = Depends(admin_required)
):
    try:
        users = await User.find_all().to_list()
        return users
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete(
    "/users/{user_id}",
)
async def delete_user(
    user_id: str,
    user: dict = Depends(admin_required)
):
    try:
        print('user_id param:', user_id)
        print('admin user:', user)
        user_to_delete = await User.find_one(User.user_id == user_id)
        print('user_to_delete:', user_to_delete)
        if not user_to_delete:
            raise HTTPException(status_code=404, detail="User not found")

        # if user_to_delete.user_id == user["user_id"]:
        #     raise HTTPException(status_code=400, detail="Admin cannot delete themselves")

        await user_to_delete.delete()
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print('Delete user error:', e)
        raise HTTPException(status_code=400, detail=str(e))