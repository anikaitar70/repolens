const { processOrders } = require("./orderService");

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
