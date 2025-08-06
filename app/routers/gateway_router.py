# In app/routers/gateway_router.py

from fastapi import APIRouter, HTTPException, status
# Import our new schemas and the new service
from app.schemas import GatewayRequest, GatewayResponse
from app.services import gateway_service

router = APIRouter(
    prefix="/v1/gateway",
    tags=["Gateway Chat"]
)

@router.post("/", response_model=GatewayResponse)
async def handle_gateway_chat(request: GatewayRequest):
    """
    Accepts a simple user request and acts as a gateway to a complex
    external AI service. History is currently a placeholder.
    """
    try:
        # Call our new gateway service, passing the user's input
        external_response = await gateway_service.call_external_api(
            message=request.message,
            sub_content=request.sub_content,
            history=request.history # Passing the placeholder
        )

        # --- PLACEHOLDER for history logic ---
        # In the future, we would build the updated history here.
        # For now, we return an empty list as defined in the schema.
        updated_history = []
        # ------------------------------------

        # Prepare and return the final, user-friendly response
        return GatewayResponse(
            response_text=external_response.response,
            suggested_prompts=external_response.follow_up_questions,
            history=updated_history
        )

    except Exception as e:
        # Catch errors from the service (e.g., bad API key from external server, network issues)
        # and return a proper HTTP error to our client.
        # We can add more specific error checks here if needed.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while communicating with the external AI service: {e}"
        )