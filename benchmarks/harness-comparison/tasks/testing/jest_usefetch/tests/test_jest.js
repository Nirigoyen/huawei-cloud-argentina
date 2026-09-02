const fs = require('fs');
const path = require('path');

// This is a meta-test that validates the test file exists and has proper structure

describe('Jest test file validation', () => {
    test('useFetch.test.js exists', () => {
        const testFile = path.resolve('useFetch.test.js');
        expect(fs.existsSync(testFile)).toBe(true);
    });

    test('test file mocks fetch', () => {
        const testFile = path.resolve('useFetch.test.js');
        const content = fs.readFileSync(testFile, 'utf-8');
        expect(content).toMatch(/fetch/i);
        expect(content).toMatch(/mock|jest\.fn/i);
    });

    test('test file tests initial state', () => {
        const content = fs.readFileSync(path.resolve('useFetch.test.js'), 'utf-8');
        expect(content).toMatch(/loading|initial/i);
    });

    test('test file tests success case', () => {
        const content = fs.readFileSync(path.resolve('useFetch.test.js'), 'utf-8');
        expect(content).toMatch(/success|resolve|data/i);
    });

    test('test file tests error case', () => {
        const content = fs.readFileSync(path.resolve('useFetch.test.js'), 'utf-8');
        expect(content).toMatch(/error|reject/i);
    });

    test('test file has at least 4 test cases', () => {
        const content = fs.readFileSync(path.resolve('useFetch.test.js'), 'utf-8');
        const testCount = (content.match(/test\(|it\(/g) || []).length;
        expect(testCount).toBeGreaterThanOrEqual(4);
    });

    test('package.json has testing dependencies', () => {
        const pkg = JSON.parse(fs.readFileSync(path.resolve('package.json'), 'utf-8'));
        const allDeps = {
            ...pkg.dependencies,
            ...pkg.devDependencies,
        };
        expect(allDeps).toHaveProperty('jest');
    });
});
