async def test_queue_is_auto_created_when_a_task_references_it(client):
    r = await client.get("/queues/status")
    assert r.json()["total"] == 0

    await client.post("/tasks/create", json={
        "task_type": "email_campaign", "priority": "high", "payload": {},
    })

    r = await client.get("/queues/status")
    names = [q["name"] for q in r.json()["queues"]]
    assert "high_priority" in names


async def test_queue_current_size_reflects_real_active_tasks(client):
    await client.post("/tasks/create", json={
        "task_type": "a", "priority": "high", "payload": {}, "queue_name": "default",
    })
    await client.post("/tasks/create", json={
        "task_type": "b", "priority": "high", "payload": {}, "queue_name": "default",
    })

    r = await client.get("/queues/status")
    high_priority = next(q for q in r.json()["queues"] if q["name"] == "high_priority")
    assert high_priority["current_size"] == 2


async def test_pause_and_resume_queue(client):
    await client.post("/tasks/create", json={
        "task_type": "a", "priority": "high", "payload": {},
    })

    r = await client.post("/queues/high_priority/pause")
    assert r.status_code == 200
    assert r.json()["status"] == "paused"

    r = await client.post("/queues/high_priority/resume")
    assert r.status_code == 200
    assert r.json()["status"] == "active"


async def test_pause_nonexistent_queue_returns_404(client):
    r = await client.post("/queues/does-not-exist/pause")
    assert r.status_code == 404
