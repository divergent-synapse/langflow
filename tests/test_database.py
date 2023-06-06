from uuid import UUID, uuid4
from langflow.api.v1.schemas import FlowListCreate
from langflow.database.models.flow import FlowCreate
import json
from sqlalchemy.orm import Session
from langflow.database.models.flow import Flow
from fastapi.testclient import TestClient

from langflow.database.models.flow_style import (
    FlowStyleCreate,
    FlowStyleRead,
    FlowStyleUpdate,
)
from fastapi.encoders import jsonable_encoder

import pytest

import threading


@pytest.fixture(scope="module")
def json_style():
    # class FlowStyleBase(SQLModel):
    # color: str = Field(index=True)
    # emoji: str = Field(index=False)
    # flow_id: UUID = Field(default=None, foreign_key="flow.id")
    return json.dumps(
        {
            "color": "red",
            "emoji": "👍",
        }
    )


def test_create_flow(client: TestClient, json_flow: str):
    flow = FlowCreate(name="Test Flow", flow=json.loads(json_flow))
    response = client.post("api/v1/flows/", json=flow.dict())
    assert response.status_code == 200
    assert response.json()["name"] == flow.name
    assert response.json()["flow"] == flow.flow


def test_read_flows(client: TestClient, json_flow: str):
    flow = FlowCreate(name="Test Flow", flow=json.loads(json_flow))
    response = client.post("api/v1/flows/", json=flow.dict())
    assert response.status_code == 200
    assert response.json()["name"] == flow.name
    assert response.json()["flow"] == flow.flow

    flow_style = FlowStyleCreate(color="red", emoji="👍", flow_id=response.json()["id"])
    response = client.post(
        "api/v1/flow_styles/", json=jsonable_encoder(flow_style.dict())
    )
    assert response.status_code == 200
    assert response.json()["color"] == flow_style.color
    assert response.json()["emoji"] == flow_style.emoji
    assert response.json()["flow_id"] == str(flow_style.flow_id)

    flow = FlowCreate(name="Test Flow", flow=json.loads(json_flow))
    response = client.post("api/v1/flows/", json=flow.dict())
    assert response.status_code == 200
    assert response.json()["name"] == flow.name
    assert response.json()["flow"] == flow.flow

    # Now we need to create FlowStyle objects for each Flow
    flow_style = FlowStyleCreate(
        color="green", emoji="👍", flow_id=response.json()["id"]
    )
    response = client.post(
        "api/v1/flow_styles/", json=jsonable_encoder(flow_style.dict())
    )
    assert response.status_code == 200
    assert response.json()["color"] == flow_style.color
    assert response.json()["emoji"] == flow_style.emoji
    assert response.json()["flow_id"] == str(flow_style.flow_id)

    response = client.get("api/v1/flows/")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_read_flow(client: TestClient, json_flow: str):
    flow = FlowCreate(name="Test Flow", flow=json.loads(json_flow))
    response = client.post("api/v1/flows/", json=flow.dict())
    flow_id = response.json()["id"]  # flow_id should be a UUID but is a string
    # turn it into a UUID
    flow_id = UUID(flow_id)

    flow_style = FlowStyleCreate(color="green", emoji="👍", flow_id=flow_id)
    response = client.post(
        "api/v1/flow_styles/", json=jsonable_encoder(flow_style.dict())
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["color"] == flow_style.color
    assert response_json["emoji"] == flow_style.emoji
    assert response_json["flow_id"] == str(flow_style.flow_id)

    response = client.get(f"api/v1/flows/{flow_id}")
    assert response.status_code == 200
    assert response.json()["name"] == flow.name
    assert response.json()["flow"] == flow.flow
    assert response.json()["style"]["color"] == flow_style.color


def test_update_flow(client: TestClient, json_flow: str):
    flow = FlowCreate(name="Test Flow", flow=json.loads(json_flow))
    response = client.post("api/v1/flows/", json=flow.dict())
    flow_id = response.json()["id"]
    updated_flow = FlowCreate(
        name="Updated Flow",
        flow=json.loads(json_flow.replace("BasicExample", "Updated Flow")),
    )
    response = client.patch(f"api/v1/flows/{flow_id}", json=updated_flow.dict())
    assert response.status_code == 200
    assert response.json()["name"] == updated_flow.name
    assert response.json()["flow"] == updated_flow.flow


def test_delete_flow(client: TestClient, json_flow: str):
    flow = FlowCreate(name="Test Flow", flow=json.loads(json_flow))
    response = client.post("api/v1/flows/", json=flow.dict())
    flow_id = response.json()["id"]
    response = client.delete(f"api/v1/flows/{flow_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Flow deleted successfully"


def test_create_flows(client: TestClient, session: Session, json_flow: str):
    # Create test data
    flow_list = FlowListCreate(
        flows=[
            FlowCreate(name="Flow 1", flow=json.loads(json_flow)),
            FlowCreate(name="Flow 2", flow=json.loads(json_flow)),
        ]
    )
    # Make request to endpoint
    response = client.post("api/v1/flows/batch/", json=flow_list.dict())
    # Check response status code
    assert response.status_code == 200
    # Check response data
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["name"] == "Flow 1"
    assert response_data[0]["flow"] == json.loads(json_flow)
    assert response_data[1]["name"] == "Flow 2"
    assert response_data[1]["flow"] == json.loads(json_flow)


def test_upload_file(client: TestClient, session: Session, json_flow: str):
    # Create test data
    flow_list = FlowListCreate(
        flows=[
            FlowCreate(name="Flow 1", flow=json.loads(json_flow)),
            FlowCreate(name="Flow 2", flow=json.loads(json_flow)),
        ]
    )
    file_contents = json.dumps(flow_list.dict())
    response = client.post(
        "api/v1/flows/upload/",
        files={"file": ("examples.json", file_contents, "application/json")},
    )
    # Check response status code
    assert response.status_code == 200
    # Check response data
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["name"] == "Flow 1"
    assert response_data[0]["flow"] == json.loads(json_flow)
    assert response_data[1]["name"] == "Flow 2"
    assert response_data[1]["flow"] == json.loads(json_flow)


def test_download_file(client: TestClient, session: Session, json_flow):
    # Create test data
    flow_list = FlowListCreate(
        flows=[
            FlowCreate(name="Flow 1", flow=json.loads(json_flow)),
            FlowCreate(name="Flow 2", flow=json.loads(json_flow)),
        ]
    )
    for flow in flow_list.flows:
        db_flow = Flow.from_orm(flow)
        session.add(db_flow)
    session.commit()
    # Make request to endpoint
    response = client.get("api/v1/flows/download/")
    # Check response status code
    assert response.status_code == 200
    # Check response data
    response_data = response.json()["flows"]
    assert len(response_data) == 2
    assert response_data[0]["name"] == "Flow 1"
    assert response_data[0]["flow"] == json.loads(json_flow)
    assert response_data[1]["name"] == "Flow 2"
    assert response_data[1]["flow"] == json.loads(json_flow)


def test_create_flow_with_invalid_data(client: TestClient):
    flow = {"name": "a" * 256, "flow": "Invalid flow data"}
    response = client.post("api/v1/flows/", json=flow)
    assert response.status_code == 422


def test_get_nonexistent_flow(client: TestClient):
    # uuid4 generates a random UUID
    uuid = uuid4()
    response = client.get(f"api/v1/flows/{uuid}")
    assert response.status_code == 404


def test_update_flow_idempotency(client: TestClient, json_flow: str):
    flow = FlowCreate(name="Test Flow", flow=json.loads(json_flow))
    response = client.post("api/v1/flows/", json=flow.dict())
    flow_id = response.json()["id"]
    updated_flow = FlowCreate(name="Updated Flow", flow=json.loads(json_flow))
    response1 = client.put(f"api/v1/flows/{flow_id}", json=updated_flow.dict())
    response2 = client.put(f"api/v1/flows/{flow_id}", json=updated_flow.dict())
    assert response1.json() == response2.json()


def test_update_nonexistent_flow(client: TestClient, json_flow: str):
    uuid = uuid4()
    updated_flow = FlowCreate(
        name="Updated Flow",
        flow=json.loads(json_flow.replace("BasicExample", "Updated Flow")),
    )
    response = client.patch(f"api/v1/flows/{uuid}", json=updated_flow.dict())
    assert response.status_code == 404


def test_delete_nonexistent_flow(client: TestClient):
    uuid = uuid4()
    response = client.delete(f"api/v1/flows/{uuid}")
    assert response.status_code == 404


def test_read_empty_flows(client: TestClient):
    response = client.get("api/v1/flows/")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_stress_create_flow(client: TestClient, json_flow: str):
    flow = FlowCreate(name="Test Flow", flow=json.loads(json_flow))

    def create_flow():
        response = client.post("api/v1/flows/", json=flow.dict())
        assert response.status_code == 200

    threads = []
    for i in range(100):
        t = threading.Thread(target=create_flow)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()


def test_create_flow_style(client: TestClient):
    flow_style = FlowStyleCreate(color="red", emoji="🔴")
    response = client.post("api/v1/flow_styles/", json=flow_style.dict())
    assert response.status_code == 200
    created_flow_style = FlowStyleRead(**response.json())
    assert created_flow_style.color == flow_style.color
    assert created_flow_style.emoji == flow_style.emoji


def test_read_flow_styles(client: TestClient):
    response = client.get("api/v1/flow_styles/")
    assert response.status_code == 200
    flow_styles = [FlowStyleRead(**flow_style) for flow_style in response.json()]
    assert not flow_styles
    # Create test data
    flow_style = FlowStyleCreate(color="red", emoji="🔴")
    response = client.post("api/v1/flow_styles/", json=flow_style.dict())
    assert response.status_code == 200
    # Check response data
    response = client.get("api/v1/flow_styles/")
    assert response.status_code == 200
    flow_styles = [FlowStyleRead(**flow_style) for flow_style in response.json()]
    assert len(flow_styles) == 1
    assert flow_styles[0].color == flow_style.color
    assert flow_styles[0].emoji == flow_style.emoji


def test_read_flow_style(client: TestClient):
    flow_style = FlowStyleCreate(color="red", emoji="🔴")
    response = client.post("api/v1/flow_styles/", json=flow_style.dict())
    created_flow_style = FlowStyleRead(**response.json())
    response = client.get(f"api/v1/flow_styles/{created_flow_style.id}")
    assert response.status_code == 200
    read_flow_style = FlowStyleRead(**response.json())
    assert read_flow_style == created_flow_style


def test_update_flow_style(client: TestClient):
    flow_style = FlowStyleCreate(color="red", emoji="🔴")
    response = client.post("api/v1/flow_styles/", json=flow_style.dict())
    created_flow_style = FlowStyleRead(**response.json())
    to_update_flow_style = FlowStyleUpdate(color="blue")
    response = client.patch(
        f"api/v1/flow_styles/{created_flow_style.id}", json=to_update_flow_style.dict()
    )
    assert response.status_code == 200
    updated_flow_style = FlowStyleRead(**response.json())
    assert updated_flow_style.color == "blue"
    assert updated_flow_style.emoji == flow_style.emoji


def test_delete_flow_style(client: TestClient):
    flow_style = FlowStyleCreate(color="red", emoji="🔴")
    response = client.post("api/v1/flow_styles/", json=flow_style.dict())
    created_flow_style = FlowStyleRead(**response.json())
    response = client.delete(f"api/v1/flow_styles/{created_flow_style.id}")
    assert response.status_code == 200
    assert response.json() == {"message": "FlowStyle deleted successfully"}
    response = client.get(f"api/v1/flow_styles/{created_flow_style.id}")
    assert response.status_code == 404