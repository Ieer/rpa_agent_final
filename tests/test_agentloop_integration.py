import asyncio
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
LOCAL_NANOBOT_ROOT = ROOT / "nanobot"
if str(LOCAL_NANOBOT_ROOT) not in sys.path:
    sys.path.insert(0, str(LOCAL_NANOBOT_ROOT))

from nanobot.agent.loop import AgentLoop
from nanobot.bus.queue import MessageBus
from nanobot.providers.base import LLMProvider, LLMResponse, ToolCallRequest

from nanobot_tool import register_rpa_tool


class DummyProvider(LLMProvider):
    def __init__(self):
        super().__init__(api_key="k", api_base=None)
        self.call_count = 0

    async def chat(self, messages, tools=None, model=None, max_tokens=4096, temperature=0.7):
        self.call_count += 1
        if self.call_count == 1:
            return LLMResponse(
                content="calling tool",
                tool_calls=[
                    ToolCallRequest(
                        id="tc1",
                        name="execute_rpa",
                        arguments={"rpa_name": "demo", "params": {"x": 1}},
                    )
                ],
            )
        return LLMResponse(content="done")

    def get_default_model(self):
        return "dummy-model"


class TestAgentLoopIntegration(unittest.TestCase):
    def test_agentloop_execute_rpa_tool(self):
        async def run_case():
            with tempfile.TemporaryDirectory() as tmp:
                workspace = Path(tmp)
                bus = MessageBus()
                provider = DummyProvider()
                agent = AgentLoop(
                    bus=bus,
                    provider=provider,
                    workspace=workspace,
                    model=provider.get_default_model(),
                    max_iterations=5,
                    memory_window=5,
                    restrict_to_workspace=False,
                )
                register_rpa_tool(agent.tools)
                session_key = f"test:agent:{uuid.uuid4().hex}"

                with patch("nanobot_tool.execute_rpa", return_value={"status": "success", "rpa": "demo"}) as execute_mock:
                    response = await agent.process_direct("run demo", session_key=session_key)

                self.assertEqual(response, "done")
                self.assertGreaterEqual(provider.call_count, 2)
                execute_mock.assert_called_once_with("demo", {"x": 1})

        asyncio.run(run_case())


if __name__ == "__main__":
    unittest.main()
