import { calculatePricing } from "./pricingService";
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
