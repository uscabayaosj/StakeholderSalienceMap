const express = require('express');
const router = express.Router();
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

let users = []; // In-memory user store
let submissions = []; // In-memory submissions store

// User registration
router.post('/register', async (req, res) => {
    const { username, password, role } = req.body;
    const hashedPassword = await bcrypt.hash(password, 10);
    users.push({ username, password: hashedPassword, role });
    res.status(201).send('User registered');
});

// User login
router.post('/login', async (req, res) => {
    const { username, password } = req.body;
    const user = users.find(u => u.username === username);
    if (user && await bcrypt.compare(password, user.password)) {
        const token = jwt.sign({ username: user.username, role: user.role }, 'secret_key');
        res.json({ token });
    } else {
        res.status(401).send('Invalid credentials');
    }
});

// Middleware to authenticate users
function authenticate(req, res, next) {
    const token = req.headers['authorization'];
    if (!token) return res.sendStatus(401);
    jwt.verify(token, 'secret_key', (err, user) => {
        if (err) return res.sendStatus(403);
        req.user = user;
        next();
    });
}

// Route for users to submit data
router.post('/submit', authenticate, (req, res) => {
    if (req.user.role !== 'user') return res.sendStatus(403);
    submissions.push(req.body);
    res.status(201).send('Data submitted');
});

// Route for admin to view submissions
router.get('/submissions', authenticate, (req, res) => {
    if (req.user.role !== 'admin') return res.sendStatus(403);
    res.json(submissions);
});

module.exports = router;