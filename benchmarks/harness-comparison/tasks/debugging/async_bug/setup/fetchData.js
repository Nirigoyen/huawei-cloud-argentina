// BUGGY: Promise.all fails entirely if any single fetch fails.
// Also missing timeout handling and proper error isolation.

async function fetchAllData(urls) {
    // BUG: Promise.all rejects entirely if any promise rejects.
    // This means one failed URL causes all results to be lost.
    const results = await Promise.all(urls.map(url => fetch(url)));

    // BUG: No error handling around the .json() calls
    const data = await Promise.all(results.map(r => r.json()));

    // BUG: Results don't include URL information
    return data;
}

module.exports = { fetchAllData };
