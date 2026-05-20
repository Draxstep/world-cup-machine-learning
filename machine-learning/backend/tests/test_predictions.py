def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_teams(client):
    r = client.get("/api/v1/predict/teams")
    assert r.status_code == 200
    data = r.json()
    assert "teams" in data
    assert len(data["teams"]) > 0
    assert "brazil" in data["teams"]


def test_risk_map_brazil(client):
    r = client.post("/api/v1/predict/risk-map", json={
        "team_name": "brazil",
        "is_knockout": 1,
        "is_home": 1,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["team"] == "brazil"
    assert len(data["intervals"]) == 7
    assert len(data["probabilities"]) == 7
    assert all(0.0 <= p <= 1.0 for p in data["probabilities"])


def test_risk_map_case_insensitive(client):
    r = client.post("/api/v1/predict/risk-map", json={
        "team_name": "BRAZIL",
        "is_knockout": 0,
        "is_home": 0,
    })
    assert r.status_code == 200


def test_risk_map_team_not_found(client):
    r = client.post("/api/v1/predict/risk-map", json={
        "team_name": "equipo_inventado_xyz",
        "is_knockout": 0,
        "is_home": 1,
    })
    assert r.status_code == 404


def test_team_profile(client):
    r = client.get("/api/v1/predict/profile/argentina")
    assert r.status_code == 200
    data = r.json()
    assert "cluster" in data
    assert "similar_teams" in data
    assert isinstance(data["similar_teams"], list)
