import { processOrders, type Order } from "./orderService";

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
