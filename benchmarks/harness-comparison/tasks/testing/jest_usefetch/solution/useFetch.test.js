const { renderHook, waitFor } = require('@testing-library/react');
const { useFetch } = require('./useFetch');

// Mock global fetch
global.fetch = jest.fn();

afterEach(() => {
    jest.clearAllMocks();
});

describe('useFetch', () => {
    test('returns initial state with loading=true', () => {
        fetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
        const { result } = renderHook(() => useFetch('http://test.com'));
        expect(result.current.data).toBeNull();
        expect(result.current.loading).toBe(true);
        expect(result.current.error).toBeNull();
    });

    test('fetches and sets data on success', async () => {
        const mockData = { users: [1, 2, 3] };
        fetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockData) });

        const { result } = renderHook(() => useFetch('http://test.com'));

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });
        expect(result.current.data).toEqual(mockData);
        expect(result.current.error).toBeNull();
    });

    test('sets error on fetch failure', async () => {
        fetch.mockRejectedValue(new Error('Network error'));

        const { result } = renderHook(() => useFetch('http://test.com'));

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });
        expect(result.current.error).toBeInstanceOf(Error);
        expect(result.current.data).toBeNull();
    });

    test('sets error on non-ok response', async () => {
        fetch.mockResolvedValue({ ok: false, status: 404, json: () => Promise.resolve({}) });

        const { result } = renderHook(() => useFetch('http://test.com'));

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });
        expect(result.current.error).toBeInstanceOf(Error);
        expect(result.current.error.message).toContain('404');
    });

    test('transitions through loading states', async () => {
        fetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({ data: 'test' }) });

        const { result } = renderHook(() => useFetch('http://test.com'));
        expect(result.current.loading).toBe(true);

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });
    });

    test('does not update state after unmount', async () => {
        let resolvePromise;
        fetch.mockReturnValue(new Promise((resolve) => { resolvePromise = resolve; }));

        const { result, unmount } = renderHook(() => useFetch('http://test.com'));
        unmount();

        resolvePromise({ ok: true, json: () => Promise.resolve({ data: 'test' }) });

        // State should still be initial since unmounted
        expect(result.current.loading).toBe(true);
    });
});
