def test_get_metrics(client):
    r = client.get("/api/v1/stats/metrics")
    assert r.status_code == 200
    data = r.json()
    assert "random_forest" in data
    assert "clustering" in data


def test_get_clusters(client):
    r = client.get("/api/v1/stats/clusters")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_quality(client):
    r = client.get("/api/v1/stats/quality")
    assert r.status_code == 200
    data = r.json()
    assert "total_rows" in data
