const express = require('express');
const authRoutes = require('./routes/auth'); // Adjust the path if necessary

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json()); // Middleware to parse JSON bodies
app.use('/api/auth', authRoutes); // Use the auth routes

app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});