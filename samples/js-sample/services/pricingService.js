const { reserveStock } = require("./inventoryService");

function calculatePricing(order) {
  const subtotal = order.items.reduce((sum, item) => sum + (item.price || 0), 0);
  const reservation = reserveStock(order);
  return { subtotal, tax: subtotal * 0.07, reservation };
}

module.exports = { calculatePricing };
