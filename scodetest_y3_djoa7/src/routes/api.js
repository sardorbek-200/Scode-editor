const express = require('express');
const { getHealthStatus } = require('../controllers/healthController');

const router = express.Router();

router.get('/health', getHealthStatus);
router.get('/v1', (req, res) => {
  res.json({
    message: 'API v1 is ready',
    endpoints: ['/api/health'],
  });
});

module.exports = router;
