#!/usr/bin/env python3
"""
Simple webhook receiver for AlertManager notifications.
This is a demonstration service to show how alerts can be received and processed.
"""

from flask import Flask, request, jsonify
import json
import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/alerts', methods=['POST'])
def receive_alert():
    """Receive and process AlertManager webhook notifications"""
    try:
        data = request.get_json()
        
        # Log the received alert
        timestamp = datetime.datetime.now().isoformat()
        logger.info(f"[{timestamp}] Received alert notification")
        
        if 'alerts' in data:
            for alert in data['alerts']:
                status = alert.get('status', 'unknown')
                alert_name = alert.get('labels', {}).get('alertname', 'Unknown')
                severity = alert.get('labels', {}).get('severity', 'unknown')
                instance = alert.get('labels', {}).get('instance', 'unknown')
                summary = alert.get('annotations', {}).get('summary', 'No summary')
                description = alert.get('annotations', {}).get('description', 'No description')
                
                logger.info(f"  Alert: {alert_name}")
                logger.info(f"  Status: {status}")
                logger.info(f"  Severity: {severity}")
                logger.info(f"  Instance: {instance}")
                logger.info(f"  Summary: {summary}")
                logger.info(f"  Description: {description}")
                logger.info(f"  ---")
        
        # In a real implementation, you would:
        # - Send notifications to Slack, Teams, email, etc.
        # - Store alerts in a database
        # - Trigger automated responses
        # - Update incident management systems
        
        return jsonify({"status": "ok", "message": "Alert received"}), 200
        
    except Exception as e:
        logger.error(f"Error processing alert: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "webhook-receiver"}), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "service": "LMA AlertManager Webhook Receiver",
        "version": "1.0.0",
        "endpoints": {
            "/alerts": "POST - Receive AlertManager notifications",
            "/health": "GET - Health check"
        }
    }), 200

if __name__ == '__main__':
    logger.info("Starting LMA AlertManager Webhook Receiver on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=True) 