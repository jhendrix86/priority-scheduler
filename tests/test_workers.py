async def test_worker_status_starts_empty(client):
    r = await client.get("/workers/status")
    assert r.json()["total"] == 0


async def test_scale_up_creates_idle_workers(client):
    r = await client.post("/workers/scale", params={"target_count": 3})
    assert r.status_code == 200
    assert r.json()["previous_count"] == 0
    assert r.json()["target_count"] == 3
    assert r.json()["scaling"] is True

    r = await client.get("/workers/status")
    assert r.json()["total"] == 3
    assert all(w["status"] == "idle" for w in r.json()["workers"])


async def test_scale_down_retires_idle_workers_first(client):
    await client.post("/workers/scale", params={"target_count": 3})

    r = await client.post("/workers/scale", params={"target_count": 1})
    assert r.status_code == 200
    assert r.json()["previous_count"] == 3
    assert r.json()["target_count"] == 1

    r = await client.get("/workers/status")
    statuses = [w["status"] for w in r.json()["workers"]]
    assert statuses.count("offline") == 2
    assert statuses.count("idle") == 1


async def test_scale_rejects_negative_target(client):
    r = await client.post("/workers/scale", params={"target_count": -1})
    assert r.status_code == 400
