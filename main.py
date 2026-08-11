import os
from urllib import response
import yaml
import json
import base64
import subprocess
import threading
import httpx
from anthropic import Anthropic
from ai_tools_loader import discover_tools
from ai_skills_loader import (
    discover_skills as discover_skill_docs,
    build_skill_catalog,
    make_load_skill,
    LOAD_SKILL_TOOL,
)

# Load API key from YAML config
config_path = os.path.join(os.path.dirname(__file__), "open_ai_key.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

base_url = 'https://gnai.intel.com/api/providers/anthropic'
auth_token = config['gnai_token']

# Initialize the Anthropic client (skip SSL verify for Intel internal proxy)
http_client = httpx.Client(verify=False)
client = Anthropic(base_url=base_url, auth_token=auth_token, http_client=http_client)

MODEL = "claude-4-5-sonnet"


_discovered = discover_tools("tools")
TOOLS = _discovered["tools_schema"]
TOOL_FUNCTIONS = _discovered["tool_functions"]

# Progressive disclosure: expose a load_skill tool so the model can pull the
# full SKILL.md instructions on demand instead of bloating the system prompt.
_SKILL_DOCS = discover_skill_docs("skills")
SKILL_CATALOG = build_skill_catalog(_SKILL_DOCS)
TOOLS.append(LOAD_SKILL_TOOL)
TOOL_FUNCTIONS["load_skill"] = make_load_skill(_SKILL_DOCS)

print(f"TOOLS is {TOOLS}")
print(f"TOOL_FUNCTIONS is {TOOL_FUNCTIONS}")



def _run_agent_turn(messages: list, user_text: str, print_tool_logs: bool = True) -> str:
    """Run one agent turn with tool handling and return final text reply."""

    messages = list(messages)
    messages.append({"role": "user", "content": user_text})

    while True:
        response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=(
                    "It is a build backport-iwlwifi program.\n\n"
                    "Available skills (call the load_skill tool with the exact "
                    "name before performing a matching task):\n"
                    f"{SKILL_CATALOG}"
                ),
                tools=TOOLS,
                messages=messages,
        )
        response_dict = response.model_dump()
        print(json.dumps(response_dict, indent=2, ensure_ascii=False))


        # Print any assistant text and collect tool calls.
        tool_results = []
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input or {}
                    tool_use_id = content_block.id

                    print(f"\n>>> Claude wants to call tool: {tool_name}({tool_input})")

                    fn = TOOL_FUNCTIONS.get(tool_name)
                    if fn:
                        try:
                            result = fn(**tool_input)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": str(result),
                                "is_error": False if fn else True
                            })
                        except Exception as e:
                            result = f"Error executing tool '{tool_name}': {str(e)}"
                            print(f"\n result: {result}")
                            tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": f"Error executing tool: {result.stderr if hasattr(result, 'stderr') else str(result)}",
                            "is_error": True
                            })
                            print(f"Error executing tool '{tool_name}': {str(e)}")
                    else:
                        result = f"Unknown tool: {tool_name}"
                        tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": f"Error: Unknown tool '{tool_name}'",
                        "is_error": True
                        })


            messages.append({"role": "user", "content": tool_results})
        elif response.stop_reason == "end_turn":
            for block in response.content:
                final_text = block.text
                if block.type == "text":
                    print("\nClaude's final response:")
                    print(final_text)

                return final_text


def main() -> None:
    _run_agent_turn(
        [],
        "Please build the backport-iwlwifi project.",
    )
    print("All jobs done. Exiting.")


if __name__ == "__main__":
    main()
