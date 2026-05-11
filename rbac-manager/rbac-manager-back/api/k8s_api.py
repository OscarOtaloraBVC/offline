# api/users_api.py
from fastapi import APIRouter, HTTPException, status
from typing import List
import services.k8s_service as k8s_service

router = APIRouter(
    prefix="/k8s_service",
    tags=["K8s"]
)

@router.get("/ns")
def list_ns():
    return k8s_service.get_kubernetes_namespaces()

@router.get("/api-resources")
def api_rs():
    return k8s_service.get_kubernetes_apiresources()

@router.get("/{user_id}/generate-kubeconfig")
def gen_kubeconfig(user_id: int):
    return k8s_service.generate_kubeconfig(user_id)

@router.get("/{user_id}/last-kubeconfig")
def get_last_kubeconfig(user_id: int):
    return k8s_service.get_last_kubeconfig(user_id)

