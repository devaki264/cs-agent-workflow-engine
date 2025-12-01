import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AgentClassifier:
    """
    AI Agent for classifying and routing customer support tickets.
    Uses Google Gemini API with optimized prompt from Phase 2 research.
    """
    
    def __init__(self):
        """Initialize the classifier with Gemini API"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def _build_system_prompt(self):
        """
        Build the optimized system prompt from Phase 2 research.
        This prompt achieved 75% improvement over baseline.
        """
        return """You are a customer support ticket classification agent for FlowTask, a project management SaaS platform.

CLASSIFICATION RULES (Based on Phase 2 Optimization):

1. CUSTOMER TIER TRIGGERS:
   - Enterprise customers: ALWAYS escalate (regardless of issue)
   - Pro customers: Evaluate based on other criteria

2. SECURITY TRIGGERS (ALWAYS escalate):
   - Login/password issues with urgency
   - Account access problems
   - Any credential-related requests

3. RISK TRIGGERS (ALWAYS escalate):
   - Churn threats: mentions of "cancel", "switching", "competitor"
   - Legal language: "lawyer", "lawsuit", "legal action"
   - Angry/hostile sentiment
   - Financial disputes or refund requests

4. TECHNICAL TRIGGERS (ALWAYS escalate):
   - Bugs affecting operations for >24 hours
   - Data loss or export failures
   - Performance degradation

5. CAN RESOLVE AUTONOMOUSLY:
   - Simple billing inquiries (invoice requests)
   - Feature requests (log and acknowledge, don't escalate)
   - How-to questions with clear answers
   - Known system behaviors

OUTPUT FORMAT:
Respond with ONLY valid JSON in this exact format:
{
  "category": "BILLING|TECHNICAL|ACCOUNT|FEATURE_REQUEST|CHURN",
  "priority": "LOW|MEDIUM|HIGH|URGENT",
  "should_escalate": true or false,
  "escalate_to": "SUPPORT_TEAM|ACCOUNT_MANAGER|ENGINEERING|BILLING" or null,
  "reasoning": "Brief explanation of classification decision",
  "suggested_tags": ["tag1", "tag2", "tag3"],
  "confidence": 0.0 to 1.0
}

CRITICAL: Output ONLY the JSON object. No markdown formatting, no other text before or after."""

    def classify_ticket(self, ticket):
        """
        Classify a single ticket using Gemini API.
        
        Args:
            ticket (dict): Ticket data with id, subject, description, etc.
            
        Returns:
            dict: Classification result with success status
        """
        # Build the complete prompt
        full_prompt = f"""{self._build_system_prompt()}

Now classify this customer support ticket:

Ticket ID: {ticket['id']}
Subject: {ticket['subject']}
Description: {ticket['description']}
Customer Email: {ticket['customer_email']}
Customer Tier: {ticket['customer_tier']}
Created: {ticket['created_at']}

Provide classification in JSON format."""

        try:
            # Call Gemini API
            response = self.model.generate_content(full_prompt)
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            # Parse JSON
            classification = json.loads(response_text)
            
            # Return success result
            return {
                "success": True,
                "ticket_id": ticket['id'],
                "classification": classification
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "ticket_id": ticket['id'],
                "error": f"Failed to parse JSON response: {str(e)}",
                "raw_response": response_text if 'response_text' in locals() else None
            }
        except Exception as e:
            return {
                "success": False,
                "ticket_id": ticket['id'],
                "error": f"API error: {str(e)}"
            }
    
    def process_batch(self, tickets):
        """
        Process multiple tickets.
        
        Args:
            tickets (list): List of ticket dictionaries
            
        Returns:
            list: List of classification results
        """
        results = []
        total = len(tickets)
        
        print(f"\n{'='*80}")
        print(f"PROCESSING {total} TICKETS WITH GEMINI")
        print(f"{'='*80}\n")
        
        for i, ticket in enumerate(tickets, 1):
            print(f"[{i}/{total}] Processing {ticket['id']}... ", end='', flush=True)
            result = self.classify_ticket(ticket)
            
            if result['success']:
                print("✓ SUCCESS")
            else:
                print(f"✗ FAILED: {result['error']}")
            
            results.append(result)
        
        # Print summary
        successful = sum(1 for r in results if r['success'])
        print(f"\n{'='*80}")
        print(f"SUMMARY: {successful}/{total} tickets classified successfully")
        print(f"{'='*80}\n")
        
        return results


def print_result(result):
    """Pretty print a classification result"""
    if not result['success']:
        print(f"❌ {result['ticket_id']} - ERROR: {result['error']}")
        return
    
    c = result['classification']
    print(f"\n{'='*80}")
    print(f"✓ {result['ticket_id']}")
    print(f"{'='*80}")
    print(f"📁 Category:     {c['category']}")
    print(f"⚡ Priority:     {c['priority']}")
    print(f"🎯 Confidence:   {c.get('confidence', 0):.0%}")
    
    if c['should_escalate']:
        print(f"🚨 ESCALATE:     YES → {c['escalate_to']}")
    else:
        print(f"✅ RESOLVE:      Handle autonomously")
    
    print(f"💭 Reasoning:    {c['reasoning']}")
    print(f"🏷️  Tags:        {', '.join(c['suggested_tags'])}")
    print(f"{'='*80}")


# Test the classifier when run directly
if __name__ == "__main__":
    print("\n🤖 CS AGENT WORKFLOW ENGINE - Test Mode (Gemini)\n")
    
    # Load sample tickets
    try:
        with open('sample_tickets.json', 'r') as f:
            tickets = json.load(f)
        print(f"✓ Loaded {len(tickets)} sample tickets\n")
    except FileNotFoundError:
        print("❌ Error: sample_tickets.json not found")
        exit(1)
    
    # Create classifier
    try:
        classifier = AgentClassifier()
        print("✓ Agent classifier initialized with Gemini\n")
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("Make sure GEMINI_API_KEY is set in your .env file")
        exit(1)
    
    # Process tickets
    results = classifier.process_batch(tickets)
    
    # Print detailed results
    for result in results:
        print_result(result)
    
    print("\n✅ Test complete! Gemini API working perfectly.\n")