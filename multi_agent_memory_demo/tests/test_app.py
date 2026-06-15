from fastapi.testclient import TestClient

from app import app, store


client = TestClient(app)


def clear_data() -> None:
    with store._connect() as conn:
        conn.execute("DELETE FROM runs")
        conn.execute("DELETE FROM memories")


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_task_run_and_memory_hit() -> None:
    clear_data()
    first = client.post(
        "/api/tasks",
        json={"task": "整理一份微服务架构设计文档", "use_memory": True},
    )
    assert first.status_code == 200
    first_data = first.json()
    assert first_data["memory_hit"] is False
    assert len(first_data["subtasks"]) >= 3

    second = client.post(
        "/api/tasks",
        json={"task": "帮我整理微服务架构文档目录", "use_memory": True},
    )
    assert second.status_code == 200
    second_data = second.json()
    assert second_data["memory_hit"] is True
    assert second_data["metrics"]["saved_steps"] > 0


def test_assignment_task_memory_hit() -> None:
    clear_data()
    first = client.post(
        "/api/tasks",
        json={"task": "制定一次前后端开发分工方案", "use_memory": True},
    )
    assert first.status_code == 200
    assert first.json()["memory_hit"] is False

    second = client.post(
        "/api/tasks",
        json={"task": "帮我整理前后端开发任务安排", "use_memory": True},
    )
    assert second.status_code == 200
    second_data = second.json()
    assert second_data["memory_hit"] is True
    assert second_data["metrics"]["saved_steps"] > 0
