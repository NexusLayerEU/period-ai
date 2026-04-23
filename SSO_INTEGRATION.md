# SSO Integration

PeriodAI supports Single Sign-On via **AIIdentityServer**.

## How it works
1. User visits PeriodAI frontend (`http://192.168.68.111:3003`)
2. If not authenticated, they are redirected to the identity server:
   `http://192.168.68.111:3007/login?redirect=http://192.168.68.111:3003`
3. After login, user is returned to PeriodAI with a JWT:
   `http://192.168.68.111:3003?sso_token=<jwt>`
4. The frontend stores the token and includes it in API calls

## Backend Integration
Import `sso_middleware.py` in your API routes to validate SSO tokens:

```python
from sso_middleware import get_current_user_from_bearer

@router.get("/protected")
async def protected_route(request: Request):
    user = get_current_user_from_bearer(request.headers.get("Authorization"))
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"email": user["sub"], "role": user.get("role", "USER")}
```

## Environment Variables
Add to `.env`:
```
SSO_JWT_SECRET=nexlayer-shared-sso-secret-change-in-production-64chars!!
IDENTITY_SERVER_URL=http://192.168.68.111:3007
```

## Shared JWT Secret
The shared secret must match `JWT_SECRET` in AIIdentityServer and all other products.
