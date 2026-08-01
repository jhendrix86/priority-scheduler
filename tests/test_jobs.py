async def test_schedule_job(client):
    r = await client.post("/jobs/schedule", json={
        "name": "Daily Report",
        "job_type": "report_generation",
        "cron_expression": "0 9 * * *",
        "payload": {},
    })
    assert r.status_code == 200
    job = r.json()
    assert job["status"] == "active"
    assert job["run_count"] == 0


async def test_get_job_roundtrip(client):
    created = await client.post("/jobs/schedule", json={
        "name": "Weekly Cleanup", "job_type": "maintenance",
        "cron_expression": "0 2 * * 0", "payload": {},
    })
    job_id = created.json()["id"]

    r = await client.get(f"/jobs/{job_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "Weekly Cleanup"


async def test_get_nonexistent_job_returns_404(client):
    import uuid
    r = await client.get(f"/jobs/{uuid.uuid4()}")
    assert r.status_code == 404


async def test_list_jobs(client):
    await client.post("/jobs/schedule", json={
        "name": "A", "job_type": "t", "cron_expression": "* * * * *", "payload": {},
    })
    await client.post("/jobs/schedule", json={
        "name": "B", "job_type": "t", "cron_expression": "* * * * *", "payload": {},
    })

    r = await client.get("/jobs/")
    assert r.json()["total"] == 2


async def test_unschedule_job(client):
    created = await client.post("/jobs/schedule", json={
        "name": "A", "job_type": "t", "cron_expression": "* * * * *", "payload": {},
    })
    job_id = created.json()["id"]

    r = await client.post(f"/jobs/{job_id}/unschedule")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"
