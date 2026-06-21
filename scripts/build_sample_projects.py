#!/usr/bin/env python3
"""Generate complex sample projects and ZIP archives for RepoLens testing."""

from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_catalog_data_lines(count: int = 520) -> str:
    lines = [
        '"""Auto-generated catalog data module (intentionally large for testing)."""',
        "",
        "CATALOG_VERSION = 3",
        "",
    ]
    for index in range(1, count - 10):
        lines.extend(
            [
                f"def catalog_rule_{index}(item: dict) -> bool:",
                f'    """Validate catalog item rule {index}."""',
                f'    return item.get("category") == "cat_{index % 25}" and item.get("active", False)',
                "",
            ]
        )
    lines.append("def summarize_catalog(items: list) -> int:")
    lines.append("    return sum(1 for item in items if item.get('active'))")
    lines.append("")
    return "\n".join(lines)


def create_python_sample(base: Path) -> None:
    write(
        base / "config.py",
        '''"""Application configuration (contains intentional security issues)."""

DATABASE_URL = "postgresql://admin:SuperSecret123!@localhost/app"
API_KEY = "sk-live-repolens-test-key-abcdef123456"
password = "admin-password-not-rotated"
client_secret = "oauth-client-secret-value-987654"
''',
    )

    write(
        base / "auth" / "security.py",
        '''"""Authentication helpers."""

from services.orders import validate_session


def run_dynamic_check(payload: str) -> object:
    """Dangerous dynamic execution for testing."""
    result = eval(payload)
    return result


def execute_policy(script: str) -> None:
    exec(script)


def check(payload: dict) -> bool:
    return validate_session(payload)
''',
    )

    write(
        base / "services" / "orders.py",
        '''"""Order processing service."""

from services.billing import calculate_invoice
from data.catalog_data import summarize_catalog


def validate_session(payload: dict) -> bool:
    token = payload.get("token")
    return bool(token and len(token) > 8)


def process_orders(orders: list, options: dict) -> list:
    """Large, complex order processor for analyzer testing."""
    processed = []
    for order in orders:
        status = order.get("status")
        if status == "pending":
            if order.get("priority") == "high":
                if order.get("amount", 0) > 100:
                    if order.get("customer", {}).get("verified"):
                        if order.get("items"):
                            if all(item.get("in_stock") for item in order["items"]):
                                if order.get("shipping", {}).get("country") in {"US", "CA", "UK"}:
                                    if not order.get("fraud_flag"):
                                        if order.get("payment", {}).get("method") != "cash":
                                            invoice = calculate_invoice(order)
                                            processed.append({"order_id": order["id"], "invoice": invoice})
                                        else:
                                            processed.append({"order_id": order["id"], "error": "cash blocked"})
                                    else:
                                        processed.append({"order_id": order["id"], "error": "fraud"})
                                else:
                                    processed.append({"order_id": order["id"], "error": "region"})
                            else:
                                processed.append({"order_id": order["id"], "error": "stock"})
                        else:
                            processed.append({"order_id": order["id"], "error": "items"})
                    else:
                        processed.append({"order_id": order["id"], "error": "customer"})
                else:
                    processed.append({"order_id": order["id"], "error": "amount"})
            elif order.get("priority") == "medium":
                if order.get("warehouse") == "east":
                    processed.append({"order_id": order["id"], "status": "queued-east"})
                elif order.get("warehouse") == "west":
                    processed.append({"order_id": order["id"], "status": "queued-west"})
                elif order.get("warehouse") == "north":
                    processed.append({"order_id": order["id"], "status": "queued-north"})
                elif order.get("warehouse") == "south":
                    processed.append({"order_id": order["id"], "status": "queued-south"})
                else:
                    processed.append({"order_id": order["id"], "status": "queued-default"})
            elif order.get("priority") == "low":
                processed.append({"order_id": order["id"], "status": "backlog"})
            else:
                processed.append({"order_id": order["id"], "status": "low-priority"})
        elif status == "review":
            processed.append({"order_id": order["id"], "status": "needs-review"})
        elif status == "cancelled":
            processed.append({"order_id": order["id"], "status": "cancelled"})
        elif status == "shipped":
            processed.append({"order_id": order["id"], "status": "complete"})
        else:
            processed.append({"order_id": order["id"], "status": "unknown"})
    return processed


def build_order_report(orders: list) -> dict:
    active = [order for order in orders if order.get("status") != "cancelled"]
    return {
        "total": len(orders),
        "active": len(active),
        "catalog_total": summarize_catalog(orders),
    }
''',
    )

    write(
        base / "services" / "billing.py",
        '''"""Billing service."""

from services.fulfillment import schedule_delivery


def calculate_invoice(order: dict) -> dict:
    subtotal = sum(item.get("price", 0) for item in order.get("items", []))
    tax = subtotal * 0.08
    shipping = schedule_delivery(order)
    return {"subtotal": subtotal, "tax": tax, "shipping": shipping, "total": subtotal + tax + shipping}
''',
    )

    write(
        base / "services" / "fulfillment.py",
        '''"""Fulfillment service."""

from auth.security import check


def schedule_delivery(order: dict) -> float:
    if check({"token": order.get("session_token", "")}):
        return 12.5
    return 99.0
''',
    )

    write(base / "data" / "catalog_data.py", generate_catalog_data_lines())

    write(
        base / "main.py",
        '''"""Entry point."""

from services.orders import build_order_report, process_orders


def main() -> None:
    sample = [{"id": 1, "status": "pending", "priority": "high", "amount": 150, "customer": {"verified": True}, "items": [{"in_stock": True, "price": 10}], "shipping": {"country": "US"}, "payment": {"method": "card"}, "session_token": "abc123456"}]
    print(process_orders(sample, {}))
    print(build_order_report(sample))


if __name__ == "__main__":
    main()
''',
    )


def create_js_sample(base: Path) -> None:
    write(
        base / "config.js",
        '''const API_KEY = "js-live-api-key-abcdefghijklmnop";
const password = "legacy-admin-password";
const secret = "jwt-signing-secret-not-from-vault";
const access_token = "ghp_testtoken123456789012345678901234";

module.exports = { API_KEY, password, secret, access_token };
''',
    )

    write(
        base / "services" / "orderService.js",
        '''const { calculatePricing } = require("./pricingService");
const { validateInventory } = require("./inventoryService");

function processOrders(orders, options) {
  const processed = [];
  for (const order of orders) {
    const status = order.status;
    if (status === "pending") {
      if (order.priority === "high") {
        if (order.amount > 100) {
          if (order.customer && order.customer.verified) {
            if (order.items && order.items.length > 0) {
              if (order.items.every((item) => item.inStock)) {
                if (order.shipping && ["US", "CA"].includes(order.shipping.country)) {
                  if (!order.fraudFlag) {
                    if (order.payment && order.payment.method !== "cash") {
                      const pricing = calculatePricing(order);
                      processed.push({ orderId: order.id, pricing });
                    } else {
                      processed.push({ orderId: order.id, error: "cash blocked" });
                    }
                  } else {
                    processed.push({ orderId: order.id, error: "fraud" });
                  }
                } else {
                  processed.push({ orderId: order.id, error: "region" });
                }
              } else {
                processed.push({ orderId: order.id, error: "stock" });
              }
            } else {
              processed.push({ orderId: order.id, error: "items" });
            }
          } else {
            processed.push({ orderId: order.id, error: "customer" });
          }
        } else {
          processed.push({ orderId: order.id, error: "amount" });
        }
      } else if (order.priority === "medium") {
        processed.push({ orderId: order.id, status: "queued" });
      } else if (order.priority === "low") {
        processed.push({ orderId: order.id, status: "backlog" });
      } else if (order.priority === "rush") {
        processed.push({ orderId: order.id, status: "rush-queue" });
      } else if (order.priority === "standard") {
        processed.push({ orderId: order.id, status: "standard-queue" });
      } else if (order.priority === "bulk") {
        processed.push({ orderId: order.id, status: "bulk-queue" });
      } else {
        processed.push({ orderId: order.id, status: "low-priority" });
      }
    } else if (status === "review") {
      processed.push({ orderId: order.id, status: "needs-review" });
    } else if (status === "cancelled") {
      processed.push({ orderId: order.id, status: "cancelled" });
    } else {
      processed.push({ orderId: order.id, status: "unknown" });
    }
  }
  return processed;
}

function renderOrderPanel(element, html) {
  element.innerHTML = html;
}

function runDynamicRule(payload) {
  return eval(payload);
}

module.exports = { processOrders, renderOrderPanel, runDynamicRule, validateInventory };
''',
    )

    write(
        base / "services" / "pricingService.js",
        '''const { reserveStock } = require("./inventoryService");

function calculatePricing(order) {
  const subtotal = order.items.reduce((sum, item) => sum + (item.price || 0), 0);
  const reservation = reserveStock(order);
  return { subtotal, tax: subtotal * 0.07, reservation };
}

module.exports = { calculatePricing };
''',
    )

    write(
        base / "services" / "inventoryService.js",
        '''const { processOrders } = require("./orderService");

function validateInventory(order) {
  return order.items.every((item) => item.inStock);
}

function reserveStock(order) {
  if (validateInventory(order)) {
    return { reserved: true, count: order.items.length };
  }
  return { reserved: false, count: 0 };
}

module.exports = { validateInventory, reserveStock, processOrders };
''',
    )

    write(
        base / "data" / "catalog.js",
        generate_catalog_data_lines(520)
        .replace("def ", "function ")
        .replace("item: dict", "item")
        .replace("-> bool:", "")
        .replace('item.get("category")', 'item.category')
        .replace('item.get("active", False)', 'item.active')
        .replace("list", "Array")
        .replace("sum(1 for item in items if item.get('active'))", "items.filter((item) => item.active).length"),
    )

    # Fix catalog.js properly with dedicated JS content
    js_catalog_lines = [
        "/** Auto-generated catalog module (intentionally large for testing). */",
        "const CATALOG_VERSION = 2;",
        "",
    ]
    for index in range(1, 510):
        js_catalog_lines.extend(
            [
                f"function catalogRule{index}(item) {{",
                f"  return item.category === 'cat_{index % 25}' && item.active === true;",
                "}",
                "",
            ]
        )
    js_catalog_lines.extend(
        [
            "function summarizeCatalog(items) {",
            "  return items.filter((item) => item.active).length;",
            "}",
            "",
            "module.exports = { summarizeCatalog };",
            "",
        ]
    )
    write(base / "data" / "catalog.js", "\n".join(js_catalog_lines))

    write(
        base / "index.js",
        '''const { processOrders } = require("./services/orderService");

const sample = [{ id: 1, status: "pending", priority: "high", amount: 150, customer: { verified: true }, items: [{ inStock: true, price: 10 }], shipping: { country: "US" }, payment: { method: "card" } }];
console.log(processOrders(sample, {}));
''',
    )


def create_typescript_sample(base: Path) -> None:
    write(
        base / "config.ts",
        '''export const API_KEY = "ts-live-api-key-zyxwvu9876543210";
export const password = "typescript-admin-password";
export const client_secret = "typescript-client-secret-value";
export const access_token = "pat_test_token_abcdefghijklmnopqrst";
''',
    )

    write(
        base / "services" / "orderService.ts",
        '''import { calculatePricing } from "./pricingService";
import { validateInventory } from "./inventoryService";

export interface Order {
  id: number;
  status: string;
  priority?: string;
  amount?: number;
  customer?: { verified?: boolean };
  items?: Array<{ inStock?: boolean; price?: number }>;
  shipping?: { country?: string };
  payment?: { method?: string };
  fraudFlag?: boolean;
}

export function processOrders(orders: Order[]): Array<Record<string, unknown>> {
  const processed: Array<Record<string, unknown>> = [];
  for (const order of orders) {
    const status = order.status;
    if (status === "pending") {
      if (order.priority === "high") {
        if ((order.amount ?? 0) > 100) {
          if (order.customer?.verified) {
            if (order.items && order.items.length > 0) {
              if (order.items.every((item) => item.inStock)) {
                if (order.shipping?.country === "US" || order.shipping?.country === "CA") {
                  if (!order.fraudFlag) {
                    if (order.payment?.method !== "cash") {
                      const pricing = calculatePricing(order);
                      processed.push({ orderId: order.id, pricing });
                    } else {
                      processed.push({ orderId: order.id, error: "cash blocked" });
                    }
                  } else {
                    processed.push({ orderId: order.id, error: "fraud" });
                  }
                } else {
                  processed.push({ orderId: order.id, error: "region" });
                }
              } else {
                processed.push({ orderId: order.id, error: "stock" });
              }
            } else {
              processed.push({ orderId: order.id, error: "items" });
            }
          } else {
            processed.push({ orderId: order.id, error: "customer" });
          }
        } else {
          processed.push({ orderId: order.id, error: "amount" });
        }
      } else if (order.priority === "medium") {
        processed.push({ orderId: order.id, status: "queued" });
      } else if (order.priority === "low") {
        processed.push({ orderId: order.id, status: "backlog" });
      } else if (order.priority === "rush") {
        processed.push({ orderId: order.id, status: "rush-queue" });
      } else if (order.priority === "standard") {
        processed.push({ orderId: order.id, status: "standard-queue" });
      } else if (order.priority === "bulk") {
        processed.push({ orderId: order.id, status: "bulk-queue" });
      } else {
        processed.push({ orderId: order.id, status: "low-priority" });
      }
    } else if (status === "review") {
      processed.push({ orderId: order.id, status: "needs-review" });
    } else if (status === "cancelled") {
      processed.push({ orderId: order.id, status: "cancelled" });
    } else {
      processed.push({ orderId: order.id, status: "unknown" });
    }
  }
  return processed;
}

export function renderPanel(element: HTMLElement, html: string): void {
  element.innerHTML = html;
}

export function runDynamicRule(payload: string): unknown {
  return eval(payload);
}

export { validateInventory };
''',
    )

    write(
        base / "services" / "pricingService.ts",
        '''import { reserveStock } from "./inventoryService";
import type { Order } from "./orderService";

export function calculatePricing(order: Order) {
  const subtotal = (order.items ?? []).reduce((sum, item) => sum + (item.price ?? 0), 0);
  const reservation = reserveStock(order);
  return { subtotal, tax: subtotal * 0.09, reservation };
}
''',
    )

    write(
        base / "services" / "inventoryService.ts",
        '''import { processOrders, type Order } from "./orderService";

export function validateInventory(order: Order): boolean {
  return (order.items ?? []).every((item) => item.inStock);
}

export function reserveStock(order: Order) {
  if (validateInventory(order)) {
    return { reserved: true, count: order.items?.length ?? 0 };
  }
  return { reserved: false, count: 0 };
}

export { processOrders };
''',
    )

    ts_catalog_lines = [
        "/** Auto-generated catalog module (intentionally large for testing). */",
        "export const CATALOG_VERSION = 4;",
        "",
    ]
    for index in range(1, 510):
        ts_catalog_lines.extend(
            [
                f"export function catalogRule{index}(item: {{ category?: string; active?: boolean }}): boolean {{",
                f"  return item.category === 'cat_{index % 25}' && item.active === true;",
                "}",
                "",
            ]
        )
    ts_catalog_lines.extend(
        [
            "export function summarizeCatalog(items: Array<{ active?: boolean }>): number {",
            "  return items.filter((item) => item.active).length;",
            "}",
            "",
        ]
    )
    write(base / "data" / "catalog.ts", "\n".join(ts_catalog_lines))

    write(
        base / "index.ts",
        '''import { processOrders } from "./services/orderService";

const sample = [{ id: 1, status: "pending", priority: "high", amount: 150, customer: { verified: true }, items: [{ inStock: true, price: 10 }], shipping: { country: "US" }, payment: { method: "card" } }];
console.log(processOrders(sample));
''',
    )


def create_dead_code_sample(base: Path) -> None:
    write(
        base / "utils.py",
        '''import json
import numpy
import os

temp = 123
active = True

def format_date():
    return "2026-01-01"

def main():
    print(json.dumps({"active": active}))

if __name__ == "__main__":
    main()
''',
    )
    write(
        base / "app.ts",
        '''import axios from "axios";
import fs from "fs";

const temp = 456;
const enabled = true;

function helperFunction() {
  return "unused";
}

export function main() {
  console.log(enabled);
}
''',
    )
    write(
        base / "worker.js",
        '''const unusedValue = 789;
const status = "ready";

function cleanupStaleEntries() {
  return status;
}

function main() {
  console.log(status);
}

module.exports = { main };
''',
    )
    write(
        base / "data" / "large_data.py",
        "\n".join([f"# padding line {index} for large file detection test" for index in range(1, 521)]),
    )
    write(
        base / "services" / "orders.py",
        '''def process_orders(orders):
    result = []
    for order in orders:
        if order.get("status") == "pending":
            if order.get("priority") == "high":
                if order.get("amount", 0) > 100:
                    if order.get("customer", {}).get("verified"):
                        if order.get("items"):
                            if all(item.get("in_stock") for item in order["items"]):
                                if order.get("shipping", {}).get("country") in {"US", "CA", "UK"}:
                                    if not order.get("fraud_flag"):
                                        if order.get("payment", {}).get("method") != "cash":
                                            result.append(order)
                                        else:
                                            result.append({"error": "cash blocked"})
                                    else:
                                        result.append({"error": "fraud"})
                                else:
                                    result.append({"error": "region"})
                            else:
                                result.append({"error": "stock"})
                        else:
                            result.append({"error": "items"})
                    else:
                        result.append({"error": "customer"})
                else:
                    result.append({"error": "amount"})
            elif order.get("priority") == "medium":
                result.append({"status": "queued"})
            elif order.get("priority") == "low":
                result.append({"status": "backlog"})
            elif order.get("priority") == "rush":
                result.append({"status": "rush-queue"})
            elif order.get("priority") == "standard":
                result.append({"status": "standard-queue"})
            elif order.get("priority") == "bulk":
                result.append({"status": "bulk-queue"})
            else:
                result.append({"status": "low-priority"})
        elif order.get("status") == "review":
            result.append({"status": "needs-review"})
        elif order.get("status") == "cancelled":
            result.append({"status": "cancelled"})
        elif order.get("status") == "shipped":
            result.append({"status": "complete"})
        else:
            result.append({"status": "unknown"})
    return result
''',
    )


def zip_directory(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(source.rglob("*")):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(source.parent).as_posix())


def main() -> None:
    projects = {
        "python-sample": create_python_sample,
        "js-sample": create_js_sample,
        "typescript-sample": create_typescript_sample,
        "dead-code-sample": create_dead_code_sample,
    }

    SAMPLES.mkdir(parents=True, exist_ok=True)

    for name, builder in projects.items():
        project_dir = SAMPLES / name
        if project_dir.exists():
            import shutil

            shutil.rmtree(project_dir)
        builder(project_dir)
        zip_path = SAMPLES / f"{name}.zip"
        zip_directory(project_dir, zip_path)
        print(f"Created {project_dir} and {zip_path}")


if __name__ == "__main__":
    main()
