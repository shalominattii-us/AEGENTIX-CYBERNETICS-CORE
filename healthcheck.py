#!/usr/bin/env python3
"""CyberCore gRPC Health Check Script"""
import grpc
import sys

sys.path.insert(0, '.')

try:
    from cybercore.oracle import service_pb2, service_pb2_grpc
    channel = grpc.insecure_channel('localhost:50051')
    stub = service_pb2_grpc.SigningOracleStub(channel)
    resp = stub.Health(service_pb2.HealthRequest())
    assert resp.healthy
    print('OK')
    sys.exit(0)
except Exception as e:
    print(f'FAIL: {e}')
    sys.exit(1)