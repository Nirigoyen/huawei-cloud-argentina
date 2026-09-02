// Callback hell: deeply nested callbacks for fetching user order history

function fetchUserOrderHistory(userId, callback) {
    // Step 1: Fetch user
    getUser(userId, function(err, user) {
        if (err) { callback(err, null); return; }

        // Step 2: Fetch user's orders
        getUserOrders(user.id, function(err, orders) {
            if (err) { callback(err, null); return; }

            let results = [];
            let completed = 0;

            // Step 3: For each order, fetch details
            orders.forEach(function(order) {
                getOrderDetails(order.id, function(err, details) {
                    if (err) { callback(err, null); return; }

                    let items = [];
                    let itemCompleted = 0;

                    // Step 4: For each item, fetch product info
                    details.items.forEach(function(item) {
                        getProductInfo(item.productId, function(err, product) {
                            if (err) { callback(err, null); return; }

                            items.push({
                                productId: item.productId,
                                quantity: item.quantity,
                                productName: product.name,
                                price: product.price,
                            });

                            itemCompleted++;
                            if (itemCompleted === details.items.length) {
                                results.push({
                                    orderId: order.id,
                                    orderDate: details.date,
                                    items: items,
                                });

                                completed++;
                                if (completed === orders.length) {
                                    // Step 5: Format final result
                                    callback(null, {
                                        user: { id: user.id, name: user.name },
                                        orders: results,
                                    });
                                }
                            }
                        });
                    });
                });
            });
        });
    });
}

// Mock data functions (callback-based)
function getUser(id, cb) {
    setTimeout(() => cb(null, { id: id, name: `User${id}` }), 10);
}

function getUserOrders(userId, cb) {
    setTimeout(() => cb(null, [{ id: 1 }, { id: 2 }]), 10);
}

function getOrderDetails(orderId, cb) {
    setTimeout(() => cb(null, {
        id: orderId,
        date: `2024-01-${orderId}`,
        items: [{ productId: 100 + orderId, quantity: orderId }],
    }), 10);
}

function getProductInfo(productId, cb) {
    setTimeout(() => cb(null, { name: `Product${productId}`, price: productId * 10 }), 10);
}

module.exports = { fetchUserOrderHistory };
