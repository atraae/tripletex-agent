import json
import base64
import logging
import os
import httpx
from app.tripletex import TripletexClient
from app.prompts import SYSTEM_PROMPT, TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-5-20251022"
MAX_TOKENS = 4096
MAX_TOOL_ITERATIONS = 10


class TripletexAgent:
    def __init__(self, credentials: dict):
        base_url = credentials.get("base_url", "")
        session_token = credentials.get("session_token", "")
        self.client = TripletexClient(base_url=base_url, session_token=session_token)

    async def solve(self, prompt: str, files: list) -> dict:
        """Main entry point: interpret prompt and execute Tripletex operations."""

        # Build initial user message
        content = []

        # Attach files if provided
        for file in files:
            mime_type = file.get("mime_type", "application/octet-stream")
            file_data = file.get("data", "")  # base64 encoded
            file_name = file.get("name", "attachment")

            if mime_type == "application/pdf":
                content.append({
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": file_data
                    }
                })
            elif mime_type.startswith("image/"):
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": file_data
                    }
                })
            logger.info(f"Attached file: {file_name} ({mime_type})")

        content.append({
            "type": "text",
            "text": f"Complete the following accounting task in Tripletex:\n\n{prompt}"
        })

        messages = [{"role": "user", "content": content}]

        # Agentic tool-use loop
        iterations = 0
        while iterations < MAX_TOOL_ITERATIONS:
            iterations += 1
            logger.info(f"Agent iteration {iterations}")

            response = await self._call_claude(messages)
            stop_reason = response.get("stop_reason")
            response_content = response.get("content", [])

            # Add assistant response to history
            messages.append({"role": "assistant", "content": response_content})

            if stop_reason == "end_turn":
                # Extract final text response
                for block in response_content:
                    if block.get("type") == "text":
                        try:
                            return json.loads(block["text"])
                        except json.JSONDecodeError:
                            return {"summary": block["text"], "actions_taken": []}
                return {"summary": "Task completed", "actions_taken": []}

            elif stop_reason == "tool_use":
                # Execute tool calls
                tool_results = []
                for block in response_content:
                    if block.get("type") == "tool_use":
                        tool_name = block["name"]
                        tool_input = block.get("input", {})
                        tool_use_id = block["id"]

                        logger.info(f"Executing tool: {tool_name} with {tool_input}")
                        result = await self._execute_tool(tool_name, tool_input)
                        logger.info(f"Tool result: {str(result)[:300]}")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": json.dumps(result)
                        })

                messages.append({"role": "user", "content": tool_results})
            else:
                logger.warning(f"Unexpected stop_reason: {stop_reason}")
                break

        return {"summary": "Task completed (max iterations reached)", "actions_taken": []}

    async def _call_claude(self, messages: list) -> dict:
        """Call the Anthropic API."""
        payload = {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "system": SYSTEM_PROMPT,
            "tools": TOOL_DEFINITIONS,
            "messages": messages
        }

        async with httpx.AsyncClient(timeout=60) as http:
            response = await http.post(
                ANTHROPIC_API_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": os.environ.get("ANTHROPIC_API_KEY", ""),
                    "anthropic-version": "2023-06-01"
                }
            )
            response.raise_for_status()
            return response.json()

    async def _execute_tool(self, tool_name: str, tool_input: dict) -> dict:
        """Dispatch tool calls to the Tripletex client."""
        try:
            if tool_name == "get_company_info":
                return await self.client.get_company_info()
            elif tool_name == "list_employees":
                return await self.client.list_employees()
            elif tool_name == "create_employee":
                return await self.client.create_employee(tool_input)
            elif tool_name == "list_customers":
                return await self.client.list_customers()
            elif tool_name == "create_customer":
                return await self.client.create_customer(tool_input)
            elif tool_name == "list_products":
                return await self.client.list_products()
            elif tool_name == "create_product":
                return await self.client.create_product(tool_input)
            elif tool_name == "create_invoice":
                return await self.client.create_invoice(tool_input)
            elif tool_name == "list_orders":
                return await self.client.list_orders()
            elif tool_name == "create_order":
                return await self.client.create_order(tool_input)
            elif tool_name == "list_departments":
                return await self.client.list_departments()
            elif tool_name == "create_department":
                return await self.client.create_department(tool_input)
            elif tool_name == "list_projects":
                return await self.client.list_projects()
            elif tool_name == "create_project":
                return await self.client.create_project(tool_input)
            elif tool_name == "list_accounts":
                return await self.client.list_accounts()
            elif tool_name == "get_vat_types":
                return await self.client.get_vat_types()
            elif tool_name == "get_currencies":
                return await self.client.get_currencies()
            elif tool_name == "create_voucher":
                return await self.client.create_voucher(tool_input)
            elif tool_name == "list_invoices":
                return await self.client.list_invoices()
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {"error": str(e), "tool": tool_name}

