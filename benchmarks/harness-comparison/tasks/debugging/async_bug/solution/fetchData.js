async function fetchWithTimeout(url, timeoutMs = 5000) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok) {
            return null;
        }
        return await response.json();
    } catch {
        return null;
    } finally {
        clearTimeout(timeout);
    }
}

async function fetchAllData(urls) {
    const results = await Promise.all(
        urls.map(async (url) => ({
            url,
            data: await fetchWithTimeout(url),
        }))
    );
    return results;
}

module.exports = { fetchAllData };
