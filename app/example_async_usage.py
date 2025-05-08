import asyncio
from app.Agents_services.factory import create_agent

async def example_async_usage():
    # Create an agent
    agent = create_agent(
        llm_provider="openai",
        api_key="your-api-key-here",
        model="gpt-4"
    )
    
    # Use the agent asynchronously
    response = await agent.run_async(
        system_prompt="You are a helpful assistant.",
        user_input="Tell me about AI.",
        chat_history=[]
    )
    
    print(response["content"])
    
    # Process multiple requests concurrently
    tasks = []
    for i in range(5):
        tasks.append(
            agent.run_async(
                system_prompt="You are a helpful assistant.",
                user_input=f"Question {i}: What is machine learning?",
                chat_history=[]
            )
        )
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    
    # Process results
    for i, result in enumerate(results):
        print(f"Result {i}: {result['content'][:50]}...")

# Run the example
if __name__ == "__main__":
    asyncio.run(example_async_usage())