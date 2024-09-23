const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const mongoose = require('mongoose');

const router = express.Router();

// Define User and Submission schemas
const userSchema = new mongoose.Schema({
    username: { type: String, required: true, unique: true },
    password: { type: String, required: true },
    role: { type: String, required: true }
});

const submissionSchema = new mongoose.Schema({
    data: { type: String, required: true },
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' }
});

const User = mongoose.model('User', userSchema);
const Submission = mongoose.model('Submission', submissionSchema);

// User registration
router.post('/register', async (req, res) => {
    const { username, password, role } = req.body;
    const hashedPassword = await bcrypt.hash(password, 10);
    const user = new User({ username, password: hashedPassword, role });
    await user.save();
    res.status(201).send('User registered');
});

// User login
router.post('/login', async (req, res) => {
    const { username, password } = req.body;
    const user = await User.findOne({ username });
    if (user && await bcrypt.compare(password, user.password)) {
        const token = jwt.sign({ username: user.username, role: user.role, id: user._id }, 'secret_key');
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
router.post('/submit', authenticate, async (req, res) => {
    if (req.user.role !== 'user') return res.sendStatus(403);
    const submission = new Submission({ data: req.body.data, userId: req.user.id });
    await submission.save();
    res.status(201).send('Data submitted');
});

// Route for admin to view submissions
router.get('/submissions', authenticate, async (req, res) => {
    if (req.user.role !== 'admin') return res.sendStatus(403);
    const submissions = await Submission.find().populate('userId', 'username');
    res.json(submissions);
});

module.exports = router;