import sys
import os

# 将当前目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude.core import RumorSimulation
import claude.llm as llm_module

def register_llm_methods(simulation):
    """将LLM方法注册到模拟类"""
    simulation.create_llm_prompt_for_knowledge_test = llm_module.create_llm_prompt_for_knowledge_test.__get__(simulation)
    simulation.call_llm_for_knowledge_test = llm_module.call_llm_for_knowledge_test.__get__(simulation)
    simulation.create_llm_prompt_for_message_decision = llm_module.create_llm_prompt_for_message_decision.__get__(simulation)
    simulation.call_llm_for_message_decision = llm_module.call_llm_for_message_decision.__get__(simulation)
    simulation.simulate_message_decision = llm_module.simulate_message_decision.__get__(simulation)
    simulation.create_llm_prompt_for_debunk_reaction = llm_module.create_llm_prompt_for_debunk_reaction.__get__(simulation)
    simulation.call_llm_for_debunk_reaction = llm_module.call_llm_for_debunk_reaction.__get__(simulation)
    simulation.simulate_debunk_reaction = llm_module.simulate_debunk_reaction.__get__(simulation)

def run_simulation(api_key, model="glm-3-turbo", initial_users=10, max_time_steps=10):
    """运行完整的谣言传播模拟"""
    # 创建模拟实例 - 使用正确的参数名称
    simulation = RumorSimulation(
        api_key=api_key,  # 使用正确的参数名称
        model=model,
        initial_users=initial_users,
        max_time_steps=max_time_steps
    )
    
    # 注册LLM方法
    register_llm_methods(simulation)
    
    # 运行模拟
    simulation.run_simulation()
    
    return simulation

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="运行谣言传播模拟")
    parser.add_argument("--api_key", type=str, help="智谱AI API密钥")
    parser.add_argument("--model", type=str, default="glm-3-turbo", help="使用的模型名称")
    parser.add_argument("--users", type=int, default=10, help="初始用户数量")
    parser.add_argument("--steps", type=int, default=10, help="最大时间步数")
    
    args = parser.parse_args()
    
    run_simulation(
        api_key=args.api_key,
        model=args.model,
        initial_users=args.users,
        max_time_steps=args.steps
    )