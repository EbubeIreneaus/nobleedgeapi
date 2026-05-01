import json
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.plan import InvestmentPlan

async def sync_plans_from_json(db: AsyncSession):
    # Determine the path dynamically based on project root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    json_path = os.path.join(base_dir, "investment_plans.json")
    
    if not os.path.exists(json_path):
        print(f"Warning: {json_path} not found. Skipping sync.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    plans_data = data.get("plans", [])
    
    for plan_info in plans_data:
        query = await db.execute(select(InvestmentPlan).where(InvestmentPlan.slug == plan_info["slug"]))
        plan = query.scalars().first()
        
        # Calculate total expected return percentage
        total_return_percent = 0
        if plan_info["roi_cycle"] == "daily":
            total_return_percent = plan_info["roi_percent"] * plan_info["duration_days"]
        elif plan_info["roi_cycle"] == "weekly":
            total_return_percent = plan_info["roi_percent"] * (plan_info["duration_days"] // 7)
        elif plan_info["roi_cycle"] == "monthly":
            total_return_percent = plan_info["roi_percent"] * (plan_info["duration_days"] // 30)
            
        if not plan:
            plan = InvestmentPlan(
                name=plan_info["name"],
                slug=plan_info["slug"],
                description=plan_info["description"],
                min_amount=plan_info["min_amount"],
                max_amount=plan_info["max_amount"],
                roi_percent=plan_info["roi_percent"],
                roi_cycle=plan_info["roi_cycle"],
                duration_days=plan_info["duration_days"],
                total_return_percent=total_return_percent,
                capital_returned=plan_info["capital_returned"],
                color=plan_info["color"],
                features=plan_info["features"],
                is_active=True
            )
            db.add(plan)
        else:
            plan.name = plan_info["name"]
            plan.description = plan_info["description"]
            plan.min_amount = plan_info["min_amount"]
            plan.max_amount = plan_info["max_amount"]
            plan.roi_percent = plan_info["roi_percent"]
            plan.roi_cycle = plan_info["roi_cycle"]
            plan.duration_days = plan_info["duration_days"]
            plan.total_return_percent = total_return_percent
            plan.capital_returned = plan_info["capital_returned"]
            plan.color = plan_info["color"]
            plan.features = plan_info["features"]
            
    await db.commit()
