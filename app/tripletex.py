import httpx
import logging
from typing import Any

logger = logging.getLogger(__name__)


class TripletexClient:
    """Client for interacting with the Tripletex API via the competition proxy."""

    def __init__(self, base_url: str, session_token: str):
        self.base_url = base_url.rstrip("/")
        self.session_token = session_token
        # Tripletex uses HTTP Basic auth: username="0", password=session_token
        self.auth = ("0", session_token)
        self.headers = {"Content-Type": "application/json"}

    async def get(self, path: str, params: dict = None) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{self.base_url}/{path.lstrip('/')}"
            logger.info(f"GET {url} params={params}")
            response = await client.get(url, headers=self.headers, auth=self.auth, params=params or {})
            response.raise_for_status()
            return response.json()

    async def post(self, path: str, data: dict) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{self.base_url}/{path.lstrip('/')}"
            logger.info(f"POST {url} data={data}")
            response = await client.post(url, headers=self.headers, auth=self.auth, json=data)
            response.raise_for_status()
            return response.json()

    async def put(self, path: str, data: dict) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{self.base_url}/{path.lstrip('/')}"
            logger.info(f"PUT {url} data={data}")
            response = await client.put(url, headers=self.headers, auth=self.auth, json=data)
            response.raise_for_status()
            return response.json()

    async def delete(self, path: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{self.base_url}/{path.lstrip('/')}"
            logger.info(f"DELETE {url}")
            response = await client.delete(url, headers=self.headers, auth=self.auth)
            response.raise_for_status()
            return response.json() if response.content else {}

    # --- Convenience methods for common Tripletex resources ---

    async def get_company_info(self) -> dict:
        return await self.get("/company")

    async def list_employees(self) -> list:
        result = await self.get("/employee", {"count": 100})
        return result.get("values", [])

    async def create_employee(self, data: dict) -> dict:
        return await self.post("/employee", data)

    async def list_customers(self) -> list:
        result = await self.get("/customer", {"count": 100})
        return result.get("values", [])

    async def create_customer(self, data: dict) -> dict:
        return await self.post("/customer", data)

    async def list_products(self) -> list:
        result = await self.get("/product", {"count": 100})
        return result.get("values", [])

    async def create_product(self, data: dict) -> dict:
        return await self.post("/product", data)

    async def list_invoices(self) -> list:
        result = await self.get("/invoice", {"count": 100})
        return result.get("values", [])

    async def create_invoice(self, data: dict) -> dict:
        return await self.post("/invoice", data)

    async def list_orders(self) -> list:
        result = await self.get("/order", {"count": 100})
        return result.get("values", [])

    async def create_order(self, data: dict) -> dict:
        return await self.post("/order", data)

    async def list_accounts(self) -> list:
        result = await self.get("/ledger/account", {"count": 100})
        return result.get("values", [])

    async def list_departments(self) -> list:
        result = await self.get("/department", {"count": 100})
        return result.get("values", [])

    async def create_department(self, data: dict) -> dict:
        return await self.post("/department", data)

    async def list_projects(self) -> list:
        result = await self.get("/project", {"count": 100})
        return result.get("values", [])

    async def create_project(self, data: dict) -> dict:
        return await self.post("/project", data)

    async def create_voucher(self, data: dict) -> dict:
        return await self.post("/ledger/voucher", data)

    async def get_vat_types(self) -> list:
        result = await self.get("/vat/type", {"count": 100})
        return result.get("values", [])

    async def get_currencies(self) -> list:
        result = await self.get("/currency", {"count": 100})
        return result.get("values", [])
