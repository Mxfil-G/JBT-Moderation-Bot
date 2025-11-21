const express = require('express');
const cron = require('node-cron');
const axios = require('axios');
const app = express();
const port = 3000;

// Your Replit app URL
const REPLIT_URL = process.env.REPLIT_URL || "https://your-bot-name.your-username.repl.co";

async function pingBot() {
    try {
        const response = await axios.get(REPLIT_URL);
        console.log(`✅ Ping successful at ${new Date().toLocaleString()}`);
    } catch (error) {
        console.log(`❌ Ping failed at ${new Date().toLocaleString()}: ${error.message}`);
    }
}

// Ping every 5 minutes
cron.schedule('*/5 * * * *', pingBot);

// Initial ping
console.log('🚀 Starting bot pinger...');
pingBot();

app.get('/', (req, res) => {
    res.send('Bot pinger is running!');
});

app.listen(port, () => {
    console.log(`Pinger server running on port ${port}`);
});
