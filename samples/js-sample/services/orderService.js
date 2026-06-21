const { calculatePricing } = require("./pricingService");
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
