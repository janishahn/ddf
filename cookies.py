from typing import Optional
from fastapi import Request, Response


def get_age_cookie(request: Request) -> Optional[str]:
    """Get the age selection from the cookie"""
    age = request.cookies.get("age")
    if age and age in ["old", "medium", "new", "all"]:
        return age
    return None


def set_age_cookie(response: Response, age: str):
    """Set the age selection in the cookie (90 days)"""
    if age not in ["old", "medium", "new", "all"]:
        age = "all"  # Default to "all" if invalid value

    # Set cookie with 90 days expiry, SameSite=Lax
    response.set_cookie(
        key="age",
        value=age,
        max_age=90 * 24 * 60 * 60,  # 90 days in seconds
        httponly=True,  # Prevent XSS
        samesite="lax",  # CSRF protection
        secure=False,  # Set to True if serving over HTTPS
    )


def validate_age_param(age: str) -> str:
    """Validate and normalize the age parameter"""
    if age and age.lower() in ["old", "medium", "new", "all"]:
        return age.lower()
    return "all"  # Default to "all"
