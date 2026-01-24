from jarvis.core.executor import Executor
from jarvis.core.planner.schemas import ExecutionPlan, PlanStep, StepAction, PlanType

def test_executor_fix():
    print("Testing Executor _execute_step fix...")
    executor = Executor()
    
    # Create a dummy plan
    plan = ExecutionPlan(
        plan_id="test_plan",
        description="Test Plan",
        plan_type=PlanType.LINEAR,
        steps=[
            PlanStep(
                step_id=1,
                description="Test Tool Call",
                action=StepAction.TOOL_CALL,
                tool="SYSTEM_CONTROL",
                input="check volume"
            )
        ]
    )
    
    result = executor.execute_plan(plan)
    print(f"Executor Result: {result}")
    
    if result["status"] == "COMPLETED":
        print("PASS: Executor executed successfully.")
    else:
        print(f"FAIL: Executor failed with {result}")

if __name__ == "__main__":
    test_executor_fix()
