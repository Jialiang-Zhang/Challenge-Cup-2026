import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class FakeAgentMessage:
    def __init__(self, sender: str, content: str) -> None:
        self.sender = sender
        self.content = content


class FakeAgent:
    def __init__(self, llm, template: str, name: str) -> None:
        self.name = name

    def __call__(self, message, **kwargs):
        if self.name == "policy_agent":
            candidate_id = kwargs["session_id"].rsplit(":", 1)[-1]
            return FakeAgentMessage(
                sender=self.name,
                content=f"private candidate response {candidate_id}",
            )
        return FakeAgentMessage(
            sender=self.name,
            content="VERDICT: A\nprivate verifier explanation",
        )


def load_user_agent_module():
    lagent_module = types.ModuleType("lagent")
    agents_module = types.ModuleType("lagent.agents")
    agents_module.Agent = FakeAgent
    schema_module = types.ModuleType("lagent.schema")
    schema_module.AgentMessage = FakeAgentMessage
    client_module = types.ModuleType("llm_client")
    client_module.InternChatClient = type("InternChatClient", (), {})

    module_path = Path(__file__).resolve().parents[1] / "user_agent.py"
    spec = importlib.util.spec_from_file_location("_baseline_user_agent_trace", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load baseline user agent")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(
        sys.modules,
        {
            "lagent": lagent_module,
            "lagent.agents": agents_module,
            "lagent.schema": schema_module,
            "llm_client": client_module,
        },
    ):
        spec.loader.exec_module(module)
    return module


user_agent = load_user_agent_module()


class UserAgentTraceTest(unittest.TestCase):
    def test_trace_omits_problem_prompts_and_raw_model_responses(self) -> None:
        agent = user_agent.ReasoningAgent(client=object())
        problem = "PRIVATE HIDDEN PROBLEM: find the secret value"

        result = agent.solve(problem, {"idx": 7})

        self.assertEqual(result["final_response"], "private candidate response 0")
        trace_text = json.dumps(result["trace"], ensure_ascii=False)
        self.assertNotIn(problem, trace_text)
        self.assertNotIn("private candidate response", trace_text)
        self.assertNotIn("private verifier explanation", trace_text)

        policy_steps = [
            entry for entry in result["trace"] if entry["step"].startswith("policy_call_")
        ]
        verifier_steps = [
            entry
            for entry in result["trace"]
            if entry["step"].startswith("verifier_call_")
        ]
        self.assertEqual(len(policy_steps), 3)
        self.assertEqual(len(verifier_steps), 6)
        self.assertEqual(
            set(policy_steps[0]["content"]),
            {"candidate_id", "status", "response_chars"},
        )
        self.assertEqual(
            set(verifier_steps[0]["content"]),
            {"candidate_id", "vote_id", "accepted"},
        )
        self.assertEqual(
            result["trace"][-1],
            {
                "step": "select_final_response",
                "content": {"candidate_id": 0, "confidence_score": 1.0},
            },
        )


if __name__ == "__main__":
    unittest.main()
