const RateLimiter = require('./rateLimiter');

describe('RateLimiter', () => {
  test('allows requests within limit', () => {
    const rl = new RateLimiter(5, 1000);
    for (let i = 0; i < 5; i++) {
      expect(rl.isAllowed('user1')).toBe(true);
    }
  });

  test('blocks requests exceeding limit', () => {
    const rl = new RateLimiter(3, 1000);
    expect(rl.isAllowed('user1')).toBe(true);
    expect(rl.isAllowed('user1')).toBe(true);
    expect(rl.isAllowed('user1')).toBe(true);
    expect(rl.isAllowed('user1')).toBe(false);
  });

  test('separate limits per identifier', () => {
    const rl = new RateLimiter(2, 1000);
    expect(rl.isAllowed('user1')).toBe(true);
    expect(rl.isAllowed('user1')).toBe(true);
    expect(rl.isAllowed('user1')).toBe(false);
    expect(rl.isAllowed('user2')).toBe(true);
    expect(rl.isAllowed('user2')).toBe(true);
    expect(rl.isAllowed('user2')).toBe(false);
  });

  test('allows after window expires', (done) => {
    const rl = new RateLimiter(2, 100);
    expect(rl.isAllowed('user1')).toBe(true);
    expect(rl.isAllowed('user1')).toBe(true);
    expect(rl.isAllowed('user1')).toBe(false);
    setTimeout(() => {
      expect(rl.isAllowed('user1')).toBe(true);
      done();
    }, 150);
  });

  test('sliding window allows partial refresh', (done) => {
    const rl = new RateLimiter(3, 100);
    expect(rl.isAllowed('user1')).toBe(true);
    expect(rl.isAllowed('user1')).toBe(true);
    expect(rl.isAllowed('user1')).toBe(true);
    setTimeout(() => {
      expect(rl.isAllowed('user1')).toBe(true);
      done();
    }, 60);
  });

  test('handles many identifiers', () => {
    const rl = new RateLimiter(1, 1000);
    for (let i = 0; i < 100; i++) {
      expect(rl.isAllowed(`user${i}`)).toBe(true);
    }
    for (let i = 0; i < 100; i++) {
      expect(rl.isAllowed(`user${i}`)).toBe(false);
    }
  });

  test('limit of 1 works correctly', () => {
    const rl = new RateLimiter(1, 1000);
    expect(rl.isAllowed('user1')).toBe(true);
    expect(rl.isAllowed('user1')).toBe(false);
    expect(rl.isAllowed('user1')).toBe(false);
  });
});
