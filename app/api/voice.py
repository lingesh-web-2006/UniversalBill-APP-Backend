"""
Voice API — POST /api/voice/process
Accepts a voice transcript, returns AI-parsed invoice preview.
"""
from flask import Blueprint, request, jsonify
from ..services.ai_service import ai_service
from ..services.invoice_service import invoice_service
from ..utils.auth import require_auth
from ..utils.validators import validate_required

voice_bp = Blueprint("voice", __name__)


@voice_bp.route("/process", methods=["POST"])
def process_voice():
    """
    Parse a voice transcript into a structured invoice preview.
    
    Body:
        transcript: str  — raw voice transcript
        company_id: str  — UUID of the company to invoice for
    
    Returns:
        invoice preview dict (not yet saved)
    """
    data = request.get_json(force=True)

    # Validate required fields
    error = validate_required(data, ["transcript", "company_id"])
    if error:
        return jsonify({"error": error}), 400

    transcript = data["transcript"].strip()
    company_id = data["company_id"]

    if len(transcript) < 5:
        return jsonify({"error": "Transcript too short"}), 400

    # Step 1: AI parses transcript into structured data
    try:
        parse_result = ai_service.parse_voice_transcript(transcript)
        if not parse_result["success"]:
            error_msg = parse_result["error"]
            status_code = 422
            
            # Specifically check for rate limits to provide better user feedback
            if "429" in error_msg or "Too Many Requests" in error_msg:
                error_msg = "AI Service is currently overloaded (Rate Limit). Please wait a few seconds and try again."
                status_code = 429
                
            return jsonify({"error": error_msg}), status_code

        ai_response = parse_result["data"]
        mode = ai_response.get("mode", "invoice")
        reply = ai_response.get("reply", "")

        # Handle CHAT mode
        if mode == "chat":
            return jsonify({
                "success": True,
                "mode": "chat",
                "reply": reply,
                "transcript": transcript
            }), 200

        # Handle INVOICE mode
        parsed_data = ai_response.get("data", ai_response) # Fallback to top-level if "data" wrapper missing

        # Step 2: Resolve products, compute taxes, estimate unknown prices
        invoice_result = invoice_service.build_invoice_from_ai(company_id, parsed_data)
        if not invoice_result["success"]:
            return jsonify({"error": invoice_result["error"]}), 422

        return jsonify({
            "success": True,
            "mode": "invoice",
            "reply": reply,
            "transcript": transcript,
            "parsed_data": parsed_data,
            "invoice_preview": invoice_result["preview"],
        }), 200
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR in process_voice: {e}")
        print(traceback.format_exc())
        return jsonify({"error": "Internal Processing Error", "message": str(e)}), 500
