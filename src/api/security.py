from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://kdxuxvyampomffkkzjzw.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_73UxfjkT_aSklAArzHGtrw_A9NljNZz")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    supabase = None

security = HTTPBearer()

async def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    if token == "OFFLINE_MODE":
        # Create a mock user object with dict-like access for offline usage
        class MockUser:
            pass
        user = MockUser()
        user.id = "offline-user"
        user.email = "offline@local"
        return user
        
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_response.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
