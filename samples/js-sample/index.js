const { processOrders } = require("./services/orderService");

const sample = [{ id: 1, status: "pending", priority: "high", amount: 150, customer: { verified: true }, items: [{ inStock: true, price: 10 }], shipping: { country: "US" }, payment: { method: "card" } }];
console.log(processOrders(sample, {}));
