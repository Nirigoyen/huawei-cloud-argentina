const { fetchAllData } = require('./fetchData');

// Mock global fetch
global.fetch = jest.fn();

afterEach(() => {
    jest.clearAllMocks();
});

describe('fetchAllData', () => {
    test('returns all results on success', async () => {
        fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ data: 'test' }),
        });

        const results = await fetchAllData(['http://a.com', 'http://b.com']);
        expect(results).toHaveLength(2);
        expect(results[0].url).toBe('http://a.com');
        expect(results[0].data).toEqual({ data: 'test' });
        expect(results[1].url).toBe('http://b.com');
        expect(results[1].data).toEqual({ data: 'test' });
    });

    test('returns null for failed fetch, keeps successful ones', async () => {
        fetch
            .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ data: 'ok' }) })
            .mockRejectedValueOnce(new Error('Network error'));

        const results = await fetchAllData(['http://a.com', 'http://b.com']);
        expect(results).toHaveLength(2);
        expect(results[0].data).toEqual({ data: 'ok' });
        expect(results[1].data).toBeNull();
        expect(results[1].url).toBe('http://b.com');
    });

    test('never throws -- always resolves', async () => {
        fetch.mockRejectedValue(new Error('All fail'));

        const results = await fetchAllData(['http://a.com', 'http://b.com']);
        expect(results).toHaveLength(2);
        expect(results[0].data).toBeNull();
        expect(results[1].data).toBeNull();
    });

    test('preserves order of results', async () => {
        fetch
            .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ id: 1 }) })
            .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ id: 2 }) })
            .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ id: 3 }) });

        const results = await fetchAllData(['url1', 'url2', 'url3']);
        expect(results[0].url).toBe('url1');
        expect(results[0].data).toEqual({ id: 1 });
        expect(results[1].url).toBe('url2');
        expect(results[1].data).toEqual({ id: 2 });
        expect(results[2].url).toBe('url3');
        expect(results[2].data).toEqual({ id: 3 });
    });

    test('handles empty URL list', async () => {
        const results = await fetchAllData([]);
        expect(results).toEqual([]);
    });

    test('handles non-ok response', async () => {
        fetch.mockResolvedValue({
            ok: false,
            status: 404,
            json: () => Promise.resolve({}),
        });

        const results = await fetchAllData(['http://a.com']);
        expect(results).toHaveLength(1);
        expect(results[0].data).toBeNull();
    });
});
