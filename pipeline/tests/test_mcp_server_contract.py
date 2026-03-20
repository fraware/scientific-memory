"""MCP server contract tests (tool schemas + argument errors)."""

from sm_pipeline import mcp_server


def test_tool_definitions_have_expected_names_and_required_fields() -> None:
    defs = mcp_server.get_tool_definitions()
    names = [d["name"] for d in defs]
    assert names == [
        "list_declarations_for_paper",
        "list_declarations_in_file",
        "get_dependency_graph_for_declaration",
    ]
    required = {
        d["name"]: set(d["inputSchema"].get("required") or []) for d in defs
    }
    assert required["list_declarations_for_paper"] == {"paper_id"}
    assert required["list_declarations_in_file"] == {"paper_id", "file_path"}
    assert required["get_dependency_graph_for_declaration"] == {"paper_id", "lean_decl"}


def test_call_tool_payload_missing_required_args_messages() -> None:
    assert (
        mcp_server._call_tool_payload("list_declarations_for_paper", {})
        == "Missing required argument: paper_id"
    )
    assert (
        mcp_server._call_tool_payload("get_dependency_graph_for_declaration", {"paper_id": "x"})
        == "Missing required argument: lean_decl"
    )
    assert (
        mcp_server._call_tool_payload("unknown_tool", {})
        == "Unknown tool: unknown_tool"
    )
