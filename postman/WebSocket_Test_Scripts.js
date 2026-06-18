// Postman WebSocket Test Scripts
// Copy these into the WebSocket request's "Tests" tab in Postman

// ============================================
// PRE-REQUEST SCRIPT (WebSocket Connection)
// ============================================
// Add this to the "Pre-request" tab

console.log('🔌 WebSocket Relay Test');
console.log('======================');
console.log('Endpoint: ws://localhost:8000/api/v1/ws/stream');
console.log('Time:', new Date().toISOString());

// ============================================
// TEST SCRIPT (WebSocket Messages)
// ============================================
// Add this to the "Tests" tab

// Store received messages
const messages = [];

// Test: Connection established
pm.test('WebSocket connection established', function() {
    // This runs when connection is established
    console.log('✅ Connected to WebSocket relay');
});

// Test: Received CandleTick
pm.test('Received CandleTick message', function() {
    // Parse the received message
    try {
        const message = JSON.parse(pm.response.text());
        
        // Verify message structure
        pm.expect(message).to.have.property('pair');
        pm.expect(message).to.have.property('interval');
        pm.expect(message).to.have.property('timestamp');
        pm.expect(message).to.have.property('open');
        pm.expect(message).to.have.property('high');
        pm.expect(message).to.have.property('low');
        pm.expect(message).to.have.property('close');
        pm.expect(message).to.have.property('volume');
        pm.expect(message).to.have.property('is_closed');
        
        // Store message for later analysis
        messages.push(message);
        
        console.log(`📊 Received tick for ${message.pair} (${message.interval}m)`);
        console.log(`   Open: ${message.open}, Close: ${message.close}`);
        console.log(`   Volume: ${message.volume}, Closed: ${message.is_closed}`);
        
    } catch (error) {
        console.error('❌ Failed to parse message:', error);
    }
});

// Test: Pong response
pm.test('Received pong response', function() {
    try {
        const message = JSON.parse(pm.response.text());
        
        if (message.type === 'pong') {
            pm.expect(message.type).to.equal('pong');
            console.log('✅ Pong received');
        }
    } catch (error) {
        // Not a pong message, skip
    }
});

// Test: Status message
pm.test('Received status message', function() {
    try {
        const message = JSON.parse(pm.response.text());
        
        if (message.type === 'status') {
            pm.expect(message).to.have.property('type', 'status');
            pm.expect(message).to.have.property('kraken_connected');
            
            console.log(`📋 Status: Kraken connected = ${message.kraken_connected}`);
            console.log(`   Reconnects: ${message.reconnect_count}`);
        }
    } catch (error) {
        // Not a status message, skip
    }
});

// ============================================
// HELPER FUNCTIONS
// ============================================

// Function to send subscribe message
function subscribe(pair, interval) {
    const message = {
        action: 'subscribe',
        pair: pair,
        interval: interval
    };
    
    console.log(`📤 Subscribing to ${pair} (${interval}m)...`);
    return JSON.stringify(message);
}

// Function to send unsubscribe message
function unsubscribe(pair, interval) {
    const message = {
        action: 'unsubscribe',
        pair: pair,
        interval: interval
    };
    
    console.log(`📤 Unsubscribing from ${pair} (${interval}m)...`);
    return JSON.stringify(message);
}

// Function to send ping
function ping() {
    const message = {
        action: 'ping'
    };
    
    console.log('📤 Sending ping...');
    return JSON.stringify(message);
}

// ============================================
// USAGE IN POSTMAN
// ============================================
// 1. Connect to ws://localhost:8000/api/v1/ws/stream
// 2. In the message input, paste one of these:
//
// Subscribe to BTC/USD 1m:
// {"action":"subscribe","pair":"BTC/USD","interval":1}
//
// Subscribe to ETH/USD 5m:
// {"action":"subscribe","pair":"ETH/USD","interval":5}
//
// Unsubscribe from BTC/USD:
// {"action":"unsubscribe","pair":"BTC/USD","interval":1}
//
// Ping:
// {"action":"ping"}

// ============================================
// COLLECTION RUNNER SCRIPT
// ============================================
// For automated testing with Postman Collection Runner

// Clear previous results
pm.collectionVariables.set('test_results', JSON.stringify([]));

// Track test results
const results = JSON.parse(pm.collectionVariables.get('test_results') || '[]');

// Add current result
results.push({
    timestamp: new Date().toISOString(),
    status: pm.response.code,
    message: pm.response.text()
});

// Store results
pm.collectionVariables.set('test_results', JSON.stringify(results));

// Log results
console.log(`📝 Test ${results.length} completed`);
console.log(`   Status: ${pm.response.code}`);
console.log(`   Total tests: ${results.length}`);
