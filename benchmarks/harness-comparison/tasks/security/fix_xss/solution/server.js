const express = require('express');
const app = express();

const comments = [];

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Security headers
app.use((req, res, next) => {
    res.setHeader('Content-Security-Policy', "default-src 'self'");
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-Frame-Options', 'DENY');
    next();
});

app.get('/', (req, res) => {
    res.send('<h1>Welcome</h1><p>Use /search?q=term to search</p>');
});

app.get('/search', (req, res) => {
    const q = escapeHtml(req.query.q || '');
    res.send(`<h1>Search Results</h1><p>You searched for: ${q}</p>`);
});

app.get('/comments', (req, res) => {
    const commentHtml = comments.map(c => `<div class="comment">${escapeHtml(c)}</div>`).join('');
    res.send(`<h1>Comments</h1>${commentHtml}<form action="/comment" method="get"><input name="text"><button>Post</button></form>`);
});

app.get('/comment', (req, res) => {
    const text = req.query.text || '';
    comments.push(text);
    res.redirect('/comments');
});

app.get('/profile', (req, res) => {
    const name = escapeHtml(req.query.name || 'Anonymous');
    res.send(`<h1>Profile</h1><p>Name: ${name}</p>`);
});

if (require.main === module) {
    app.listen(3000, () => {
        console.log('Server running on port 3000');
    });
}

module.exports = app;
