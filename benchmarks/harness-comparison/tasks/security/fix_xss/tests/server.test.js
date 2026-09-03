const request = require('supertest');
const app = require('./server');

describe('XSS Prevention', () => {
  test('search endpoint escapes HTML', async () => {
    const res = await request(app).get('/search').query({ q: '<script>alert(1)</script>' });
    expect(res.text).not.toContain('<script>alert(1)</script>');
    expect(res.text).toContain('You searched for');
  });

  test('search escapes angle brackets', async () => {
    const res = await request(app).get('/search').query({ q: '<img src=x onerror=alert(1)>' });
    expect(res.text).not.toContain('<img src=x onerror=alert(1)>');
  });

  test('profile endpoint escapes HTML', async () => {
    const res = await request(app).get('/profile').query({ name: '<script>alert("xss")</script>' });
    expect(res.text).not.toContain('<script>alert("xss")</script>');
  });

  test('comment endpoint stores escaped content', async () => {
    await request(app).get('/comment').query({ text: '<script>alert(1)</script>' });
    const res = await request(app).get('/comments');
    expect(res.text).not.toContain('<script>alert(1)</script>');
  });

  test('has Content-Security-Policy header', async () => {
    const res = await request(app).get('/');
    expect(res.headers['content-security-policy']).toBeDefined();
  });

  test('has X-Content-Type-Options header', async () => {
    const res = await request(app).get('/');
    expect(res.headers['x-content-type-options']).toBe('nosniff');
  });

  test('normal text still works', async () => {
    const res = await request(app).get('/search').query({ q: 'hello world' });
    expect(res.text).toContain('hello world');
  });

  test('normal name still works', async () => {
    const res = await request(app).get('/profile').query({ name: 'John Doe' });
    expect(res.text).toContain('John Doe');
  });
});
