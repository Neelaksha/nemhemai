# from sqlalchemy import select
# from openagent.db import AsyncSessionLocal
# from openagent.models import Sales
# async def get_sales_data(limit=5):
#     async with AsyncSessionLocal() as session: 
#         result = await session.execute(
#             select(Sales).order_by(Sales.id.desc()).limit(limit)
#         )
#         rows = result.scalars().all()

#         return [
#             {
#                 "revenue": r.revenue,
#                 "growth": r.growth,
#                 "period": r.period
#             }
#             for r in rows
#         ]
from sqlalchemy import select
from openagent.db import AsyncSessionLocal
from openagent.models import Sales


async def get_sales_data(limit=5, start_date=None, end_date=None):
    async with AsyncSessionLocal() as session:

        query = select(Sales)

        # 🔹 Apply date filters if provided
        if start_date:
            query = query.where(Sales.period >= start_date)

        if end_date:
            query = query.where(Sales.period <= end_date)

        # 🔹 Order + limit
        query = query.order_by(Sales.id.desc()).limit(limit)

        result = await session.execute(query)
        rows = result.scalars().all()

        return [
            {
                "revenue": r.revenue,
                "growth": r.growth,
                "period": r.period
            }
            for r in rows
        ]