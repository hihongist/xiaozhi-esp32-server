"""服务端MCP工具模块。

语音主路径只导入 ServerMCPExecutor。ServerMCPManager / ServerMCPClient
会加载 mcp 与 httpx2（httpx2 2.16.0 要求 Python>=3.11），因此推迟到
真正访问这两个名字时再导入。
"""

from .mcp_executor import ServerMCPExecutor

__all__ = ["ServerMCPManager", "ServerMCPExecutor", "ServerMCPClient"]


def __getattr__(name):
    if name == "ServerMCPManager":
        from .mcp_manager import ServerMCPManager

        return ServerMCPManager
    if name == "ServerMCPClient":
        from .mcp_client import ServerMCPClient

        return ServerMCPClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
