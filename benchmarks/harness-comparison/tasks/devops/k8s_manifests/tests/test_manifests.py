import os

import pytest
import yaml


def load_manifests():
    """Load all YAML manifests from k8s.yaml or k8s/ directory."""
    docs = []
    if os.path.exists("k8s.yaml"):
        with open("k8s.yaml") as f:
            docs = list(yaml.safe_load_all(f))
    elif os.path.isdir("k8s"):
        for fn in sorted(os.listdir("k8s")):
            if fn.endswith((".yaml", ".yml")):
                with open(f"k8s/{fn}") as f:
                    docs.extend(list(yaml.safe_load_all(f)))
    else:
        pytest.fail("No k8s.yaml or k8s/ directory found")
    return [d for d in docs if d is not None]


def find_resource(docs, kind, name=None):
    for d in docs:
        if d.get("kind") == kind:
            if name is None or d.get("metadata", {}).get("name") == name:
                return d
    return None


def test_deployment_exists():
    docs = load_manifests()
    dep = find_resource(docs, "Deployment", "web-app")
    assert dep is not None, "Deployment web-app not found"


def test_deployment_api_version():
    docs = load_manifests()
    dep = find_resource(docs, "Deployment", "web-app")
    assert dep["apiVersion"] == "apps/v1"


def test_deployment_replicas():
    docs = load_manifests()
    dep = find_resource(docs, "Deployment", "web-app")
    assert dep["spec"]["replicas"] == 3


def test_deployment_labels():
    docs = load_manifests()
    dep = find_resource(docs, "Deployment", "web-app")
    labels = dep["metadata"]["labels"]
    assert labels.get("app") == "web-app"
    assert labels.get("tier") == "frontend"


def test_deployment_resources():
    docs = load_manifests()
    dep = find_resource(docs, "Deployment", "web-app")
    container = dep["spec"]["template"]["spec"]["containers"][0]
    resources = container["resources"]
    assert resources["limits"]["cpu"] == "200m"
    assert resources["limits"]["memory"] == "256Mi"
    assert resources["requests"]["cpu"] == "100m"
    assert resources["requests"]["memory"] == "128Mi"


def test_deployment_probes():
    docs = load_manifests()
    dep = find_resource(docs, "Deployment", "web-app")
    container = dep["spec"]["template"]["spec"]["containers"][0]
    assert "livenessProbe" in container, "Missing livenessProbe"
    assert "readinessProbe" in container, "Missing readinessProbe"
    assert container["livenessProbe"]["httpGet"]["path"] == "/healthz"
    assert container["readinessProbe"]["httpGet"]["path"] == "/ready"


def test_deployment_strategy():
    docs = load_manifests()
    dep = find_resource(docs, "Deployment", "web-app")
    strategy = dep["spec"].get("strategy", {})
    assert strategy.get("type") == "RollingUpdate"
    rolling = strategy.get("rollingUpdate", {})
    assert rolling.get("maxSurge") == 1
    assert rolling.get("maxUnavailable") == 0


def test_service_exists():
    docs = load_manifests()
    svc = find_resource(docs, "Service", "web-app-service")
    assert svc is not None, "Service web-app-service not found"
    assert svc["spec"]["type"] == "ClusterIP"
    assert svc["spec"]["selector"]["app"] == "web-app"
    assert svc["spec"]["ports"][0]["port"] == 80


def test_ingress_exists():
    docs = load_manifests()
    ing = find_resource(docs, "Ingress", "web-app-ingress")
    assert ing is not None, "Ingress web-app-ingress not found"
    assert ing["apiVersion"] == "networking.k8s.io/v1"
    annotations = ing["metadata"].get("annotations", {})
    assert "nginx" in str(annotations.get("kubernetes.io/ingress.class", "")) or \
           ing["spec"].get("ingressClassName") == "nginx"


def test_ingress_rules():
    docs = load_manifests()
    ing = find_resource(docs, "Ingress", "web-app-ingress")
    rules = ing["spec"]["rules"]
    assert rules[0]["host"] == "app.example.com"
    path = rules[0]["http"]["paths"][0]
    assert path["path"] == "/"
    assert path["backend"]["service"]["name"] == "web-app-service"


def test_hpa_exists():
    docs = load_manifests()
    hpa = find_resource(docs, "HorizontalPodAutoscaler")
    assert hpa is not None, "HPA not found"
    assert hpa["apiVersion"] == "autoscaling/v2"
    assert hpa["spec"]["minReplicas"] == 2
    assert hpa["spec"]["maxReplicas"] == 10


def test_namespace():
    docs = load_manifests()
    for d in docs:
        ns = d.get("metadata", {}).get("namespace", "")
        assert ns == "production", f"Resource {d.get('kind')} missing namespace 'production'"
