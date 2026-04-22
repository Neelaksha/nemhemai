import asyncio
from workflows.report_workflow import run_workflow
async def test():
    result = await run_workflow('generate sales report')
    print('RESULT:', result)
asyncio.run(test())

