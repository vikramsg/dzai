# Pydantic AI: Logging Agent Thinking and Tool Calls

## Agent Iteration with Detailed Logging

For the most detailed control, use `agent.iter()` to manually drive the agent execution:

```python
async def detailed_agent_logging(agent_name: str, query: str) -> None:
    # ... your existing setup code ...
    
    print("🚀 Starting detailed agent execution...")
    
    async with agent.iter(query) as run:
        step_count = 0
        async for node in run:
            step_count += 1
            print(f"\n--- Step {step_count} ---")
            
            if agent.is_user_prompt_node(node):
                print(f"👤 User Prompt: {node.user_prompt}")
            
            elif agent.is_model_request_node(node):
                print(f"🤖 Model Request Node")
                
                # Stream the model request to see real-time thinking and tool calls
                async with node.stream(run.ctx) as stream:
                    current_response = ""
                    async for event in stream:
                        if isinstance(event, PartStartEvent):
                            print(f"📝 Starting part {event.index}: {type(event.part).__name__}")
                        
                        elif isinstance(event, PartDeltaEvent):
                            if isinstance(event.delta, ThinkingPartDelta):
                                print(f"🤔 Thinking: {event.delta.content_delta}")
                            elif isinstance(event.delta, TextPartDelta):
                                current_response += event.delta.content_delta
                                print(f"💬 Response chunk: {event.delta.content_delta}")
                            elif isinstance(event.delta, ToolCallPartDelta):
                                print(f"🔧 Tool call delta: {event.delta}")
            
            elif agent.is_call_tools_node(node):
                print(f"⚙️ Calling Tools Node")
                print(f"   Tools to call: {[call.tool_name for call in node.tool_calls]}")
                
                # Execute tools and log results
                for tool_call in node.tool_calls:
                    print(f"   🔧 Executing {tool_call.tool_name}")
                    print(f"      Args: {tool_call.args}")
            
            else:
                print(f"❓ Unknown node type: {type(node).__name__}")
    
    print(f"\n🎯 Agent execution completed in {step_count} steps")
    print(f"📊 Final result: {run.result}")
```


## Common Pitfalls and Solutions

### 1. Missing Tool Call Details
Some users report seeing tool calls only in the most recent message. **Solution**: Use `all_messages()` instead of just checking the latest message, and ensure you're iterating through all message parts.

### 2. Incomplete Event Capture
When using `event_stream_handler`, you need to piece together streamed text from PartStartEvent and PartDeltaEvent. **Solution**: Use the examples above to properly handle event streaming.

## Links to Relevant Resources

- [Pydantic AI Message History Documentation](https://ai.pydantic.dev/message-history/)
- [Logfire Integration Guide](https://ai.pydantic.dev/logfire/)
- [Agent Streaming Documentation](https://ai.pydantic.dev/agents/#streaming-all-events-and-output)

## Notes

This doc was created by `uv run dzai api-research-agent -q "$(cat src/dzai/agent.py) Show me how to log agent thinking and tool calls"`.
