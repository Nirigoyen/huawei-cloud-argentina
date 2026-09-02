// Refactored from callback hell to async/await

function getUser(id) {
    return new Promise((resolve) => {
        setTimeout(() => resolve({ id, name: `User${id}` }), 10);
    });
}

function getUserOrders(userId) {
    return new Promise((resolve) => {
        setTimeout(() => resolve([{ id: 1 }, { id: 2 }]), 10);
    });
}

function getOrderDetails(orderId) {
    return new Promise((resolve) => {
        setTimeout(() => resolve({
            id: orderId,
            date: `2024-01-${orderId}`,
            items: [{ productId: 100 + orderId, quantity: orderId }],
        }), 10);
    });
}

function getProductInfo(productId) {
    return new Promise((resolve) => {
        setTimeout(() => resolve({ name: `Product${productId}`, price: productId * 10 }), 10);
    });
}

async function fetchUserOrderHistory(userId) {
    try {
        const user = await getUser(userId);
        const orders = await getUserOrders(user.id);

        const results = await Promise.all(
            orders.map(async (order) => {
                const details = await getOrderDetails(order.id);
                const items = await Promise.all(
                    details.items.map(async (item) => {
                        const product = await getProductInfo(item.productId);
                        return {
                            productId: item.productId,
                            quantity: item.quantity,
                            productName: product.name,
                            price: product.price,
                        };
                    })
                );
                return {
                    orderId: order.id,
                    orderDate: details.date,
                    items,
                };
            })
        );

        return {
            user: { id: user.id, name: user.name },
            orders: results,
        };
    } catch (err) {
        throw err;
    }
}

module.exports = { fetchUserOrderHistory };
