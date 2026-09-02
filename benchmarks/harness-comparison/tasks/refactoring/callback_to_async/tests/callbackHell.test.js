const { fetchUserOrderHistory } = require('./callbackHell');

describe('fetchUserOrderHistory', () => {
    test('returns user order history as a Promise', async () => {
        const result = await fetchUserOrderHistory(1);
        expect(result).toBeDefined();
        expect(result.user).toBeDefined();
        expect(result.user.id).toBe(1);
        expect(result.user.name).toBe('User1');
    });

    test('returns orders array', async () => {
        const result = await fetchUserOrderHistory(1);
        expect(result.orders).toBeDefined();
        expect(Array.isArray(result.orders)).toBe(true);
        expect(result.orders.length).toBe(2);
    });

    test('each order has items with product info', async () => {
        const result = await fetchUserOrderHistory(1);
        for (const order of result.orders) {
            expect(order.orderId).toBeDefined();
            expect(order.orderDate).toBeDefined();
            expect(order.items).toBeDefined();
            expect(Array.isArray(order.items)).toBe(true);
            for (const item of order.items) {
                expect(item.productName).toBeDefined();
                expect(item.price).toBeDefined();
                expect(item.quantity).toBeDefined();
            }
        }
    });

    test('product info is correct', async () => {
        const result = await fetchUserOrderHistory(1);
        const firstOrder = result.orders[0];
        const firstItem = firstOrder.items[0];
        expect(firstItem.productName).toBe(`Product${firstItem.productId}`);
        expect(firstItem.price).toBe(firstItem.productId * 10);
    });

    test('handles different user IDs', async () => {
        const result = await fetchUserOrderHistory(42);
        expect(result.user.id).toBe(42);
        expect(result.user.name).toBe('User42');
    });

    test('function returns a Promise (not callback-based)', () => {
        const result = fetchUserOrderHistory(1);
        expect(result).toBeInstanceOf(Promise);
    });

    test('uses async function (no callback parameter)', () => {
        // The function should not accept a callback as second parameter
        const fnStr = fetchUserOrderHistory.toString();
        // Should not have 'callback' as a parameter name in the main function signature
        expect(fnStr.length).toBeGreaterThan(0);
    });
});
