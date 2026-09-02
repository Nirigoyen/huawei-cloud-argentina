const express = require('express');
const app = express();

const comments = [];

app.get('/', (req, res) => {
    res.send('<h1>Welcome</h1><p>Use /search?q=term to search</p>');
});

// VULNERABLE: Reflected XSS - query reflected directly in HTML
app.get('/search', (req, res) => {
    const q = req.query.q || '';
    res.send(`<h1>Search Results</h1><p>You searched for: ${q}</p>`);
});

// VULNERABLE: Stored XSS - comment stored and displayed without sanitization
app.get('/comments', (req, res) => {
    const commentHtml = comments.map(c => `<div class="comment">${c}</div>`).join('');
    res.send(`<h1>Comments</h1>${commentHtml}<form action="/comment" method="get"><input name="text"><button>Post</button></form>`);
});

app.get('/comment', (req, res) => {
    const text = req.query.text || '';
    comments.push(text);
    res.redirect('/comments');
});

// VULNERABLE: No security headers
app.get('/profile', (req, res) => {
    const name = req.query.name || 'Anonymous';
    res.send(`<h1>Profile</h1><p>Name: ${name}</p>`);
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});

module.exports = app;
