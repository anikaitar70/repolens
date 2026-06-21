import { reserveStock } from "./inventoryService";
import type { Order } from "./orderService";

export function calculatePricing(order: Order) {
  const subtotal = (order.items ?? []).reduce((sum, item) => sum + (item.price ?? 0), 0);
  const reservation = reserveStock(order);
  return { subtotal, tax: subtotal * 0.09, reservation };
}
