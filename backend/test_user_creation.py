import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.db.session import Base

DATABASE_URL = "sqlite+aiosqlite:///./sql_app.db"

async def test_user_creation():
    print("Testing user creation...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        try:
            user = User(
                email="test_direct@example.com",
                name="Test Direct",
                is_verified=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"✅ User created: {user.id}, {user.email}")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_user_creation())
