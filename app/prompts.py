SYSTEM_PROMPT = """You are an expert AI accounting agent for Tripletex, a Norwegian accounting system.
Your job is to interpret accounting task prompts (which may be in Norwegian, English, or other languages)
and execute the correct Tripletex API calls to complete the task.

## Your capabilities
You can interact with the Tripletex API to:
- Create and manage employees (ansatte)
- Create and manage customers (kunder)
- Create and manage products/services (produkter/tjenester)
- Create orders and invoices (ordrer og fakturaer)
- Create departments (avdelinger)
- Create projects (prosjekter)
- Create accounting vouchers/entries (bilag)
- Query existing data to make informed decisions

## Important rules
1. Always check existing data before creating duplicates
2. Use Norwegian date format where needed (YYYY-MM-DD for API calls)
3. Norwegian VAT (MVA) is typically 25% (high), 15% (food), 12% (transport/hotel)
4. Norwegian kroner (NOK) is the default currency
5. Always respond with valid JSON describing what you did

## Response format
Always respond with a JSON object like this:
{
  "actions_taken": ["description of each action"],
  "resources_created": [{"type": "employee", "id": 123, "name": "..."}],
  "resources_modified": [{"type": "invoice", "id": 456}],
  "summary": "Brief description of what was accomplished"
}

## Available API tools (you will be given these as function calls):
- get_company_info: Get company information
- list_employees / create_employee: Manage employees
- list_customers / create_customer: Manage customers
- list_products / create_product: Manage products
- list_invoices / create_invoice: Create invoices
- list_orders / create_order: Create orders
- list_departments / create_department: Manage departments
- list_projects / create_project: Manage projects
- create_voucher: Create accounting vouchers
- list_accounts: List chart of accounts
- get_vat_types: Get available VAT types
- get_currencies: Get available currencies

Think step by step:
1. Parse the task to understand what needs to be done
2. Query existing data if needed (to get IDs, check for duplicates)
3. Execute the required API calls in the correct order
4. Return a structured summary of what was accomplished
"""

TOOL_DEFINITIONS = [
    {
        "name": "get_company_info",
        "description": "Get information about the company in Tripletex",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "list_employees",
        "description": "List all employees in Tripletex",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "create_employee",
        "description": "Create a new employee in Tripletex",
        "input_schema": {
            "type": "object",
            "properties": {
                "firstName": {"type": "string", "description": "First name (fornavn)"},
                "lastName": {"type": "string", "description": "Last name (etternavn)"},
                "email": {"type": "string", "description": "Email address"},
                "employeeNumber": {"type": "string", "description": "Employee number"},
                "dateOfBirth": {"type": "string", "description": "Date of birth YYYY-MM-DD"},
                "phoneNumberMobile": {"type": "string", "description": "Mobile phone number"},
                "startDate": {"type": "string", "description": "Employment start date YYYY-MM-DD"},
            },
            "required": ["firstName", "lastName"]
        }
    },
    {
        "name": "list_customers",
        "description": "List all customers in Tripletex",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "create_customer",
        "description": "Create a new customer in Tripletex",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Customer name"},
                "email": {"type": "string", "description": "Customer email"},
                "phoneNumber": {"type": "string", "description": "Phone number"},
                "organizationNumber": {"type": "string", "description": "Norwegian org number"},
                "isPrivateIndividual": {"type": "boolean", "description": "True if private person"},
                "postalAddress": {
                    "type": "object",
                    "description": "Postal address",
                    "properties": {
                        "addressLine1": {"type": "string"},
                        "postalCode": {"type": "string"},
                        "city": {"type": "string"},
                        "country": {"type": "object", "properties": {"id": {"type": "integer"}}}
                    }
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "list_products",
        "description": "List all products/services in Tripletex",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "create_product",
        "description": "Create a new product or service",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Product name"},
                "number": {"type": "string", "description": "Product number/SKU"},
                "costExcludingVatCurrency": {"type": "number", "description": "Cost price ex VAT"},
                "priceExcludingVatCurrency": {"type": "number", "description": "Sales price ex VAT"},
                "priceIncludingVatCurrency": {"type": "number", "description": "Sales price inc VAT"},
                "vatType": {"type": "object", "properties": {"id": {"type": "integer"}}, "description": "VAT type object with id"},
                "unit": {"type": "object", "properties": {"id": {"type": "integer"}}}
            },
            "required": ["name"]
        }
    },
    {
        "name": "create_invoice",
        "description": "Create a new invoice",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer": {"type": "object", "properties": {"id": {"type": "integer"}}, "description": "Customer object with id"},
                "invoiceDate": {"type": "string", "description": "Invoice date YYYY-MM-DD"},
                "dueDate": {"type": "string", "description": "Due date YYYY-MM-DD"},
                "orders": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "integer"}}}},
            },
            "required": ["customer", "invoiceDate", "dueDate"]
        }
    },
    {
        "name": "list_orders",
        "description": "List all orders in Tripletex",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "create_order",
        "description": "Create a new order (ordre)",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer": {"type": "object", "properties": {"id": {"type": "integer"}}},
                "orderDate": {"type": "string", "description": "Order date YYYY-MM-DD"},
                "deliveryDate": {"type": "string", "description": "Delivery date YYYY-MM-DD"},
                "orderLines": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product": {"type": "object", "properties": {"id": {"type": "integer"}}},
                            "count": {"type": "number"},
                            "unitPriceExcludingVatCurrency": {"type": "number"},
                            "description": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["customer", "orderDate"]
        }
    },
    {
        "name": "list_departments",
        "description": "List all departments",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "create_department",
        "description": "Create a new department (avdeling)",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Department name"},
                "departmentNumber": {"type": "string", "description": "Department number"},
                "departmentManager": {"type": "object", "properties": {"id": {"type": "integer"}}},
            },
            "required": ["name"]
        }
    },
    {
        "name": "list_projects",
        "description": "List all projects",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "create_project",
        "description": "Create a new project",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "number": {"type": "string"},
                "startDate": {"type": "string", "description": "YYYY-MM-DD"},
                "endDate": {"type": "string", "description": "YYYY-MM-DD"},
                "customer": {"type": "object", "properties": {"id": {"type": "integer"}}},
                "projectManager": {"type": "object", "properties": {"id": {"type": "integer"}}},
            },
            "required": ["name", "startDate"]
        }
    },
    {
        "name": "list_accounts",
        "description": "List chart of accounts (kontoplan)",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_vat_types",
        "description": "Get available VAT types (momssatser)",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_currencies",
        "description": "Get available currencies",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "create_voucher",
        "description": "Create an accounting voucher/entry (bilag)",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Voucher date YYYY-MM-DD"},
                "description": {"type": "string"},
                "voucherType": {"type": "object", "properties": {"id": {"type": "integer"}}},
                "postings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "account": {"type": "object", "properties": {"id": {"type": "integer"}}},
                            "amount": {"type": "number"},
                            "description": {"type": "string"},
                            "date": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["date", "postings"]
        }
    }
]
