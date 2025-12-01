from flask import Flask, render_template, request, jsonify
import json
from agent_classifier import AgentClassifier

app = Flask(__name__)

# Initialize classifier once at startup
try:
    classifier = AgentClassifier()
    print("✓ Agent classifier initialized")
except Exception as e:
    print(f"✗ Failed to initialize classifier: {e}")
    classifier = None


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/classify', methods=['POST'])
def classify():
    """API endpoint to classify a single ticket"""
    if not classifier:
        return jsonify({
            'success': False,
            'error': 'Classifier not initialized'
        }), 500
    
    ticket_data = request.json
    result = classifier.classify_ticket(ticket_data)
    return jsonify(result)


@app.route('/process-batch', methods=['POST'])
def process_batch():
    """Process all sample tickets"""
    if not classifier:
        return jsonify({
            'success': False,
            'error': 'Classifier not initialized'
        }), 500
    
    try:
        with open('sample_tickets.json', 'r') as f:
            tickets = json.load(f)
        
        results = classifier.process_batch(tickets)
        return jsonify(results)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'classifier_ready': classifier is not None
    })


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🤖 CS AGENT WORKFLOW ENGINE - Web Interface")
    print("="*80)
    print("\n✓ Starting Flask server...")
    print("✓ Open your browser to: http://localhost:5000")
    print("\nPress CTRL+C to stop the server\n")
    
    app.run(debug=True, port=5000, host='127.0.0.1')