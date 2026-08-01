import uuid


async def test_create_task_runs_through_real_scheduler(client):
    r = await client.post("/tasks/create", json={
        "task_type": "email_campaign",
        "priority": "high",
        "payload": {"campaign_id": "c1"},
        "queue_name": "default",
    })
    assert r.status_code == 200, r.text
    task = r.json()
    assert task["status"] == "pending"
    assert task["scheduling_decision"]["scheduled"] is True
    # priority "high" -> score 8 -> WeightedScheduler routes it to high_priority
    assert task["queue_name"] == "high_priority"


async def test_create_task_with_unmet_dependency_is_blocked(client):
    r = await client.post("/tasks/create", json={
        "task_type": "report",
        "priority": "low",
        "payload": {},
        "depends_on": ["some-other-task"],
    })
    assert r.status_code == 200
    decision = r.json()["scheduling_decision"]
    assert decision["scheduled"] is False
    assert decision["blocked"] is True


async def test_get_task_roundtrip(client):
    created = await client.post("/tasks/create", json={
        "task_type": "email_campaign", "priority": "medium", "payload": {},
    })
    task_id = created.json()["id"]

    r = await client.get(f"/tasks/{task_id}")
    assert r.status_code == 200
    assert r.json()["id"] == task_id


async def test_get_nonexistent_task_returns_404(client):
    r = await client.get(f"/tasks/{uuid.uuid4()}")
    assert r.status_code == 404


async def test_list_tasks_reflects_whats_actually_in_the_db(client):
    for _ in range(3):
        await client.post("/tasks/create", json={
            "task_type": "email_campaign", "priority": "medium", "payload": {},
        })

    r = await client.get("/tasks/")
    assert r.status_code == 200
    assert r.json()["total"] == 3
    assert len(r.json()["tasks"]) == 3


async def test_list_tasks_filters_by_status(client):
    created = await client.post("/tasks/create", json={
        "task_type": "email_campaign", "priority": "medium", "payload": {},
    })
    task_id = created.json()["id"]
    await client.post(f"/tasks/{task_id}/cancel")

    r = await client.get("/tasks/", params={"status": "cancelled"})
    assert r.json()["total"] == 1

    r = await client.get("/tasks/", params={"status": "pending"})
    assert r.json()["total"] == 0


async def test_retry_increments_count_and_respects_max_retries(client):
    created = await client.post("/tasks/create", json={
        "task_type": "email_campaign", "priority": "medium", "payload": {},
    })
    task_id = created.json()["id"]
    assert created.json()["max_retries"] == 3

    for expected_count in (1, 2, 3):
        r = await client.post(f"/tasks/{task_id}/retry")
        assert r.status_code == 200
        assert r.json()["retry_count"] == expected_count
        assert r.json()["status"] == "retrying"

    # 4th retry exceeds max_retries=3
    r = await client.post(f"/tasks/{task_id}/retry")
    assert r.status_code == 400


async def test_cancel_task(client):
    created = await client.post("/tasks/create", json={
        "task_type": "email_campaign", "priority": "medium", "payload": {},
    })
    task_id = created.json()["id"]

    r = await client.post(f"/tasks/{task_id}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"
