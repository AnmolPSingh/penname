"""penname-mcp — optional local MCP server. Off unless the user enables it.

A thin wrapper: every tool delegates to penname.mcp.tools, which delegates to
penname.core. Nothing here talks to the network except the local stdio MCP
transport the client speaks over.
"""

from __future__ import annotations

import sys

from penname.mcp import config, tools


class MCPDisabledError(RuntimeError):
    """Raised when the server is constructed while the MCP feature is off."""


def build_server(require_enabled: bool = True):
    """Construct the MCP server with Penname's tools registered.

    The off-by-default gate lives here so no caller can start the server
    without the user having opted in. Tests pass require_enabled=False to
    build the object without touching the user's real setting."""
    if require_enabled and not config.is_enabled():
        raise MCPDisabledError("the Penname MCP server is off by default")

    from mcp.server.fastmcp import FastMCP

    server = FastMCP("penname-mcp")

    @server.tool()
    def pseudonymize_document(
        input_path: str,
        output_path: str | None = None,
        mapping_path: str | None = None,
        overwrite: bool = False,
    ) -> dict:
        """Give sensitive values in a local document a pen name before it is
        shared with a model. Writes a pseudonymized copy and an encrypted
        mapping file (inside the input file's folder) and returns their paths
        plus counts by type. Existing files are not overwritten unless
        overwrite=true. Always review the pseudonymized file before sharing it."""
        return tools.pseudonymize_document(
            input_path, output_path, mapping_path, overwrite
        )

    @server.tool()
    def reverse_to_file(
        response_text: str,
        mapping_path: str,
        output_path: str,
        overwrite: bool = False,
    ) -> dict:
        """Take the pen names off a model's reply and save the restored text to
        a local file (inside the mapping file's folder). Returns only a success
        flag and the file path — the restored content is deliberately never
        returned into model context. Existing files are not overwritten unless
        overwrite=true."""
        return tools.reverse_to_file(
            response_text, mapping_path, output_path, overwrite
        )

    return server


def main() -> int:
    if not config.is_enabled():
        sys.stderr.write(
            "The Penname MCP server is off by default.\n"
            "Enable it first:  python -m penname.mcp.config enable\n"
            "(or turn it on in the desktop app's settings).\n"
        )
        return 1
    build_server().run()  # stdio transport (FastMCP default); no network
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
