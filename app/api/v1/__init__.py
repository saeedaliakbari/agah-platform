from fastapi import APIRouter

from app.api.v1 import auth, bank_accounts, loans, users, verification, wallet, withdrawal

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(verification.router)
api_router.include_router(wallet.router)
api_router.include_router(bank_accounts.router)
api_router.include_router(withdrawal.router)
api_router.include_router(loans.router)