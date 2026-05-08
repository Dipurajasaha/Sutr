import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.core.database import AsyncSessionLocal
from app.models.file import FileMetadata


async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(FileMetadata))
        files = result.scalars().all()
        updated = 0
        for f in files:
            if not f.file_path:
                continue
            if '/' in f.file_path or '\\' in f.file_path:
                new = f.file_path.replace('\\', '/').split('/')[-1]
                if new != f.file_path:
                    print(f'Updating {f.id}: {f.file_path} -> {new}')
                    f.file_path = new
                    session.add(f)
                    updated += 1
        if updated:
            await session.commit()
        print(f'Done. Updated {updated} rows.')


if __name__ == '__main__':
    asyncio.run(main())
