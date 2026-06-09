import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.policy import Policy, PolicyCondition, PolicyReply


pytestmark = pytest.mark.anyio


async def test_v2_policy_list_notfound(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/policy",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_v2_policy_list(db: AsyncSession, ext_client: AsyncClient) -> None:
    policy = Policy(
        name="Policy 1",
        description="Test policy 1",
        conditions=[
            PolicyCondition(attribute="attribute1", operator="EQUALS", value="value1")
        ],
        replies=[PolicyReply(attribute="attribute1", value="value1")],
    )
    db.add(policy)
    await db.commit()

    response = await ext_client.get(
        "/api/v2/policy",
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Policy 1"


async def test_v2_policy_get(db: AsyncSession, ext_client: AsyncClient) -> None:
    policy = Policy(
        name="Policy 1",
        description="Test policy 1",
        conditions=[
            PolicyCondition(attribute="attribute1", operator="EQUALS", value="value1")
        ],
        replies=[PolicyReply(attribute="attribute1", value="value1")],
    )
    db.add(policy)
    await db.commit()

    response = await ext_client.get(
        f"/api/v2/policy/{policy.id}",
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Policy 1"


async def test_v2_policy_get_not_found(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/policy/99999",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_policy_post(ext_client: AsyncClient) -> None:
    response = await ext_client.post(
        "/api/v2/policy",
        json={
            "name": "New Policy",
            "enabled": True,
            "description": "This is a new policy",
            "conditions": [
                {"attribute": "attribute1", "operator": "==", "value": "value1"}
            ],
            "replies": [{"attribute": "attribute1", "value": "value1"}],
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "New Policy"
    assert data["description"] == "This is a new policy"
    assert len(data["conditions"]) == 1
    assert data["conditions"][0]["attribute"] == "attribute1"
    assert data["conditions"][0]["operator"] == "=="
    assert data["conditions"][0]["value"] == "value1"
    assert len(data["replies"]) == 1
    assert data["replies"][0]["attribute"] == "attribute1"
    assert data["replies"][0]["value"] == "value1"


async def test_v2_policy_post_duplicate(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    db.add(Policy(name="DuplicatePolicy"))

    await db.commit()

    response = await ext_client.post(
        "/api/v2/policy",
        json={
            "name": "DuplicatePolicy",
            "enabled": True,
            "description": "This is a new policy",
            "conditions": [
                {"attribute": "attribute1", "operator": "==", "value": "value1"}
            ],
            "replies": [{"attribute": "attribute1", "value": "value1"}],
        },
    )

    data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert data["errors"]["name"] == "A Policy with that name already exists."


async def test_v2_policy_delete(db: AsyncSession, ext_client: AsyncClient) -> None:
    policy = Policy(name="Policy to delete", description="This policy will be deleted")
    db.add(policy)
    await db.commit()

    response = await ext_client.delete(
        f"/api/v2/policy/{policy.id}",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_v2_policy_delete_notfound(ext_client: AsyncClient) -> None:
    response = await ext_client.delete(
        "/api/v2/policy/9999",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_policy_put(db: AsyncSession, ext_client: AsyncClient) -> None:
    policy = Policy(name="Policy to update", description="This policy will be updated")
    db.add(policy)
    await db.commit()

    response = await ext_client.put(
        f"/api/v2/policy/{policy.id}",
        json={
            "name": "Updated Policy",
            "enabled": False,
            "description": "This policy has been updated",
            "conditions": [
                {"attribute": "attribute1", "operator": "==", "value": "value1"}
            ],
            "replies": [{"attribute": "attribute1", "value": "value1"}],
        },
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Policy"
    assert data["description"] == "This policy has been updated"
