"""Boot smoke: the agent module imports and registers its server without a microphone,
a LiveKit connection, or per-session provider init (those happen inside the entrypoint).
"""

import src.agent as agent_module


def test_agent_boots_as_realty():
    assert agent_module.config.AGENT_NAME == "realty"
    assert agent_module.server is not None
    assert agent_module.server.setup_fnc is agent_module.prewarm
