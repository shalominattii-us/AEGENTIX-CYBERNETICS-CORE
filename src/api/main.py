from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, status

from src.kernels.runtime import KernelRuntime, TelemetrySwarm
from src.kernels.ledger import LedgerAnchorWriter

app = FastAPI(title="EagleShield CBDC Infrastructure Gateway", version="1.0.0")

runtime = KernelRuntime()
runtime.bootstrap()
telemetry_swarm = TelemetrySwarm(runtime)

@app.on_event("startup")
async def startup_event():
    await telemetry_swarm.start()

@app.on_event("shutdown")
async def shutdown_event():
    await telemetry_swarm.stop()

class AttestationRequest(BaseModel):
    wallet: str

class IntentPayload(BaseModel):
    route_key: str = Field(default="us_treasury_fed")
    sender: str
    receiver: str
    amount: float
    circuit_override: bool = Field(default=False)
    auth_nonce: str
    auth_signature: str

@app.get("/health")
def health_check():
    return {
        "status": "ACTIVE",
        "swarm": "ONLINE",
        "node_role": runtime.replay.node_role,
        "block_height": runtime.ledger.block_height,
        "state_root": runtime.ledger.last_state_root
    }

@app.post("/api/v1/sov/attest")
async def request_sovereign_challenge(payload: AttestationRequest):
    try:
        nonce = runtime.sovereign.issue_challenge(payload.wallet)
        return {"nonce": nonce, "ttl_seconds": 60}
    except PermissionError as p:
        raise HTTPException(status_code=403, detail=str(p))

@app.post("/api/v1/intent", status_code=status.HTTP_202_ACCEPTED)
async def process_helm_intent(payload: IntentPayload):
    try:
        tx_footprint = f"{payload.sender}:{payload.receiver}:{payload.amount}".encode('utf-8')

        is_authentic = runtime.sovereign.verify_assertion(
            wallet=payload.sender,
            nonce=payload.auth_nonce,
            signature_hex=payload.auth_signature,
            message_bytes=tx_footprint
        )

        if not is_authentic:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid Hardware Token Signature or Challenge Expired."
            )

        if runtime.aegis.is_sanctioned(payload.sender) or runtime.aegis.is_sanctioned(payload.receiver):
            raise HTTPException(status_code=403, detail="OFAC Sanctions Triggered via AEGIS Kernel.")

        tx_receipt = runtime.janus.process_intent_route(
            route_key=payload.route_key,
            sender=payload.sender,
            receiver=payload.receiver,
            amount=payload.amount,
            metadata={"hardware_verified": True}
        )

        anchor = runtime.ledger.anchor_state_root(tx_receipt)
        
        block_entry = {
            "block_height": anchor["block_index"],
            "state_root": anchor["state_root"],
            "tx_receipt": tx_receipt,
            "signature_proof": anchor["signature_proof"],
            "timestamp": anchor["timestamp"]
        }
        runtime.replay.log_block(block_entry)

        await telemetry_swarm.submit(tx_receipt)

        return {
            "status": "SETTLED",
            "block_height": anchor["block_index"],
            "state_root": anchor["state_root"],
            "proof": anchor["signature_proof"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Core Spine Error: {str(e)}")

@app.post("/api/v1/failover/replay")
async def trigger_state_replay():
    try:
        fresh_ledger = LedgerAnchorWriter()
        res = runtime.replay.replay_from_genesis(fresh_ledger)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replay Verification Failed: {str(e)}")

@app.post("/api/v1/failover/promote")
async def promote_standby_node():
    return runtime.replay.promote_to_active()
