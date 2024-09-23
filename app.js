const express = require('express');
const mongoose = require('mongoose');
const authRoutes = require('./routes/auth'); // Adjust the path if necessary

const app = express();
const PORT = process.env.PORT || 3000;

// Connect to MongoDB
mongoose.connect('mongodb://localhost:27017/mydatabase', { // Replace with your MongoDB connection string
    useNewUrlParser: true,
    useUnifiedTopology: true,
})
.then(() => console.log('MongoDB connected'))
.catch(err => console.error('MongoDB connection error:', err));

app.use(express.json()); // Middleware to parse JSON bodies
app.use('/api/auth', authRoutes); // Use the auth routes

app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});