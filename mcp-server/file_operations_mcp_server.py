#!/usr/bin/env python3
"""
MCP Server: File Operations (write_file, update_file, create_directory)

PURPOSE:
--------
Provides safe filesystem operations for sandboxed agents. Enables agents running
in restricted MCP environments to write and update files without direct filesystem
access. Separates concerns: model servers stay clean, file I/O handled by dedicated
server with path validation and security controls.

ARCHITECTURE:
-------------
- Dedicated MCP server for all file operations
- Three tools: write_file, update_file, create_directory
- Path validation: all paths constrained to repo root (prevents directory traversal)
- Error handling: clear, actionable error messages
- Reusable across all tasks and agents

USAGE:
------
    python file_operations_mcp_server.py

Registered in ~/.claude.json under "file_operations" provider.

TOOLS:
------
1. write_file(path, content) - Create or overwrite file
2. update_file(path, old_content, new_content) - Find and replace content
3. create_directory(path) - Create directory (creates parents if needed)

SECURITY:
---------
- Path validation prevents directory traversal attacks
- All paths validated against repo root
- Raises error if path escapes repo boundary
- Minimal dependencies (Python stdlib only)

Author: Julen Gamboa
julen.gamboa.ds@gmail.com
"""

import os
from pathlib import Path
from typing import Any, Dict
from base_mcp_server import BaseMCPServer, logger


class FileOperationsMCPServer(BaseMCPServer):
    """File operations server - allows agents to write/update files safely."""

    def __init__(self):
        super().__init__("file_operations")

        # Get repo root from environment or use current directory
        self.repo_root = Path(os.getenv("REPO_ROOT", os.getcwd())).resolve()
        logger.info(f"File operations server initialized with repo root: {self.repo_root}")

        # Override tools - define file operation tools instead of execute_task
        self.tools = {
            "write_file": {
                "description": "Write or create a file in the repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path (relative to repo root)"
                        },
                        "content": {
                            "type": "string",
                            "description": "File content to write"
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            "update_file": {
                "description": "Update specific content in a file (find and replace)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path (relative to repo root)"
                        },
                        "old_content": {
                            "type": "string",
                            "description": "Content to find and replace"
                        },
                        "new_content": {
                            "type": "string",
                            "description": "Replacement content"
                        }
                    },
                    "required": ["path", "old_content", "new_content"]
                }
            },
            "create_directory": {
                "description": "Create a directory in the repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path (relative to repo root)"
                        }
                    },
                    "required": ["path"]
                }
            }
        }

    def _validate_path(self, file_path: str) -> Path:
        """Validate path is within repo root (prevent directory traversal)."""
        # Convert to absolute path
        abs_path = (self.repo_root / file_path).resolve()

        # Check if path is within repo root
        try:
            abs_path.relative_to(self.repo_root)
        except ValueError:
            raise ValueError(f"Path {file_path} is outside repo root")

        return abs_path

    def _write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write or create a file."""
        try:
            abs_path = self._validate_path(path)

            # Create parent directories if needed
            abs_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            abs_path.write_text(content)
            logger.info(f"Wrote file: {path}")

            return {
                "isError": False,
                "content": [{
                    "type": "text",
                    "text": f"Successfully wrote {path} ({len(content)} bytes)"
                }]
            }
        except ValueError as e:
            logger.error(f"Path validation failed: {e}")
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Path validation error: {e}"}]
            }
        except Exception as e:
            logger.error(f"Write failed: {e}")
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Write failed: {e}"}]
            }

    def _update_file(self, path: str, old_content: str, new_content: str) -> Dict[str, Any]:
        """Update specific content in a file."""
        try:
            abs_path = self._validate_path(path)

            # Read file
            if not abs_path.exists():
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": f"File not found: {path}"}]
                }

            current_content = abs_path.read_text()

            # Check if old_content exists
            if old_content not in current_content:
                return {
                    "isError": True,
                    "content": [{
                        "type": "text",
                        "text": f"Content not found in {path}"
                    }]
                }

            # Replace (only first occurrence)
            updated_content = current_content.replace(old_content, new_content, 1)

            # Write back
            abs_path.write_text(updated_content)
            logger.info(f"Updated file: {path}")

            return {
                "isError": False,
                "content": [{
                    "type": "text",
                    "text": f"Successfully updated {path}"
                }]
            }
        except ValueError as e:
            logger.error(f"Path validation failed: {e}")
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Path validation error: {e}"}]
            }
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Update failed: {e}"}]
            }

    def _create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory."""
        try:
            abs_path = self._validate_path(path)

            # Create directory
            abs_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")

            return {
                "isError": False,
                "content": [{
                    "type": "text",
                    "text": f"Successfully created directory {path}"
                }]
            }
        except ValueError as e:
            logger.error(f"Path validation failed: {e}")
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Path validation error: {e}"}]
            }
        except Exception as e:
            logger.error(f"Directory creation failed: {e}")
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Directory creation failed: {e}"}]
            }

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file operation."""
        if tool_name == "write_file":
            path = arguments.get("path")
            content = arguments.get("content")
            if not path or content is None:
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": "path and content are required"}]
                }
            return self._write_file(path, content)

        elif tool_name == "update_file":
            path = arguments.get("path")
            old_content = arguments.get("old_content")
            new_content = arguments.get("new_content")
            if not path or old_content is None or new_content is None:
                return {
                    "isError": True,
                    "content": [{
                        "type": "text",
                        "text": "path, old_content, and new_content are required"
                    }]
                }
            return self._update_file(path, old_content, new_content)

        elif tool_name == "create_directory":
            path = arguments.get("path")
            if not path:
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": "path is required"}]
                }
            return self._create_directory(path)

        else:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]
            }


if __name__ == "__main__":
    server = FileOperationsMCPServer()
    server.run()
