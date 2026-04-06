import time
from typing import Any, Dict, List, Optional

from src.agent.parser import parse_react_response
from src.agent.prompts import build_react_system_prompt
from src.agent.tools_registry import get_tools, preview_result, render_tool_descriptions
from src.core.config import get_settings
from src.core.llm_provider import LLMProvider
from src.core.provider_factory import build_provider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker
from src.telemetry.trace_store import trace_store


class ReActAgent:
    """Runnable standard ReAct-style agent using LLM for tool selection and planning."""

    def __init__(self, llm: Optional[LLMProvider] = None, tools: Optional[List[Dict[str, Any]]] = None, max_steps: int = 5):
        self.llm = llm or build_provider()
        self.tools = tools or get_tools()
        self.max_steps = max_steps

    def get_system_prompt(self) -> str:
        return build_react_system_prompt(render_tool_descriptions(self.tools), self.max_steps)

    def run(self, user_input: str, session_id: str | None = None) -> Dict[str, Any]:
        started_at = time.time()
        trace = trace_store.create_trace(version="v2", user_query=user_input, session_id=session_id)
        logger.log_event("AGENT_REQUEST_RECEIVED", {"trace_id": trace["trace_id"], "input": user_input, "model": self.llm.model_name})

        tool_calls: List[Dict[str, Any]] = []
        steps = 0
        scratchpad = f"User: {user_input}\n"
        system_prompt = self.get_system_prompt()
        provider_name = "unknown"
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        while steps < self.max_steps:
            steps += 1
            logger.log_event("AGENT_STEP_STARTED", {"trace_id": trace["trace_id"], "step": steps})

            try:
                response = self.llm.generate(prompt=scratchpad, system_prompt=system_prompt)
                text = response["content"]
                provider_name = response.get("provider", provider_name)
                usage = response.get("usage") or {}
                for key in total_usage:
                    total_usage[key] += int(usage.get(key, 0) or 0)
                tracker.track_request(provider=provider_name, model=self.llm.model_name, usage=usage, latency_ms=response.get("latency_ms", 0))

                try:
                    parsed = parse_react_response(text)
                except Exception as exc:
                    observation = f"System Error parsing your response: {str(exc)}. Please strictly use valid JSON in 'Action Input'."
                    scratchpad += f"{text}\nObservation: {observation}\n"
                    trace_store.append_step(trace, {"step": steps, "thought": text, "action": None, "observation": observation})
                    continue

                thought = parsed.get("thought")
                action = parsed.get("action")
                final_answer = parsed.get("final_answer")

                if final_answer:
                    trace_store.append_step(trace, {"step": steps, "thought": thought, "action": None, "observation": final_answer})
                    return self._finalize(trace, final_answer, started_at, steps, tool_calls, "success", None, provider_name, total_usage)

                if action:
                    tool_name, args = action
                    has_error = False
                    try:
                        result = self._execute_tool(tool_name, args)
                        observation = preview_result(result)
                    except Exception as exc:
                        result = f"Error executing tool {tool_name}: {str(exc)}"
                        observation = result
                        has_error = True

                    trace_store.append_step(
                        trace,
                        {
                            "step": steps,
                            "thought": thought,
                            "action": {"tool": tool_name, "args": args},
                            "observation": result,
                        },
                    )

                    if not has_error:
                        tool_calls.append({"tool": tool_name, "args": args, "result_preview": observation})

                    scratchpad += f"{text}\nObservation: {observation}\n"
                    continue

                observation = "Error parsing action, you must provide 'Action' and 'Action Input', or 'Final Answer'."
                scratchpad += f"{text}\nObservation: {observation}\n"
                trace_store.append_step(trace, {"step": steps, "thought": thought or text, "action": None, "observation": observation})

            except Exception as exc:
                logger.log_event("AGENT_STEP_ERROR", {"trace_id": trace["trace_id"], "step": steps, "error": str(exc)})
                answer = "Hệ thống đang gặp trục trặc khi suy luận, vui lòng thử lại sau."
                return self._finalize(trace, answer, started_at, steps, tool_calls, "error", "PROVIDER_ERROR", provider_name, total_usage)

        answer = "Tôi đã suy nghĩ quá giới hạn số bước nhưng chưa tìm được câu trả lời."
        return self._finalize(trace, answer, started_at, steps, tool_calls, "error", "MAX_STEPS_REACHED", provider_name, total_usage)

    def _finalize(
        self,
        trace: Dict[str, Any],
        answer: str,
        started_at: float,
        steps: int,
        tool_calls: List[Dict[str, Any]],
        status: str,
        error_code: str | None,
        provider_name: str,
        usage: Dict[str, int],
    ) -> Dict[str, Any]:
        latency_ms = int((time.time() - started_at) * 1000)
        trace = trace_store.finalize_trace(
            trace,
            final_answer=answer,
            status=status,
            metrics={
                "latency_ms": latency_ms,
                "tool_calls_count": len(tool_calls),
                "steps": steps,
                "provider": provider_name,
                "model": self.llm.model_name,
                **usage,
            },
            error_code=error_code,
        )
        logger.log_event("AGENT_FINAL", {"trace_id": trace["trace_id"], "latency_ms": latency_ms, "steps": steps, "status": status})
        return {
            "version": "v2",
            "answer": answer,
            "latency_ms": latency_ms,
            "steps": steps,
            "tool_calls": tool_calls,
            "trace_id": trace["trace_id"],
            "status": status,
            "error_code": error_code,
        }

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        for tool in self.tools:
            if tool["name"] == tool_name:
                logger.log_event("TOOL_EXECUTION_STARTED", {"tool": tool_name, "args": args})
                result = tool["handler"](**args)
                logger.log_event("TOOL_EXECUTED", {"tool": tool_name, "args": args, "result": result})
                return result
        raise ValueError(f"Tool {tool_name} not found.")


settings = get_settings()
agent = ReActAgent(max_steps=settings.max_agent_steps)
