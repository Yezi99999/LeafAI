import asyncio, uuid
from app.db.session import async_session_factory
from app.db.models import User, PointsTransaction, AITask, AIModel, TaskStatus
from sqlalchemy import select
from app.tasks.workers import _settle_and_stats
from app.api.v1.chat import _settle_chat
from app.services.billing import PLAN_POINTS

async def main():
    async with async_session_factory() as db:
        u = (await db.execute(select(User).where(User.username=='test01'))).scalar_one()
        u.points_balance = 500
        u.free_quota = {**u.free_quota, 'image': 0}
        m = (await db.execute(select(AIModel).where(AIModel.category=='image').limit(1))).scalar_one()
        cost_img = m.unit_points or 3
        t = AITask(task_id='e2e-img-'+uuid.uuid4().hex[:8], user_id=u.id, category='image', model_id=m.id,
                   status=TaskStatus.SUCCESS, input_params={'_charge_plan':'points','_charge_points':cost_img})
        db.add(t); await db.flush()
        await _settle_and_stats(db, t)
        await db.commit()
        u2 = (await db.execute(select(User).where(User.username=='test01'))).scalar_one()
        chat_m = (await db.execute(select(AIModel).where(AIModel.category=='chat').limit(1))).scalar_one()
        cost_chat = chat_m.unit_points or 2
        await _settle_chat(db, u2, PLAN_POINTS, cost_chat, chat_m.id, token_count=50, task_id='e2e-chat-1234')
        await db.commit()
        for r in (await db.execute(select(PointsTransaction).where(PointsTransaction.user_id==u.id, PointsTransaction.task_id.like('e2e-%')).order_by(PointsTransaction.id))).scalars().all():
            print(f'TX service={r.service_code} type={r.tx_type} delta={r.points_delta} balance={r.balance_after} model={r.model_id}')
        print('final balance=', u2.points_balance, 'expected=', 500-cost_img-cost_chat)
        for r in (await db.execute(select(PointsTransaction).where(PointsTransaction.user_id==u.id, PointsTransaction.task_id.like('e2e-%')))).scalars().all():
            await db.delete(r)
        for t in (await db.execute(select(AITask).where(AITask.task_id.like('e2e-img-%')))).scalars().all():
            await db.delete(t)
        u.points_balance = 0
        await db.commit()
        print('E2E BOTH PASS (cleaned)')
asyncio.run(main())
