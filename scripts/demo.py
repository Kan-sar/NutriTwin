"""Automated local HTTP demonstration of the manual core workflow."""

from datetime import UTC, date, datetime
from typing import Any, cast

import httpx

BASE_URL = "http://127.0.0.1:8000"


def expect(response: httpx.Response) -> dict[str, Any] | list[Any]:
    response.raise_for_status()
    return cast("dict[str, Any] | list[Any]", response.json())


def main() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=20) as client:
        tokens = expect(
            client.post(
                "/api/v1/auth/login",
                json={
                    "email": "student@example.com",
                    # pragma: allowlist nextline secret
                    "password": "StudentDemo!2026",
                },
            )
        )
        assert isinstance(tokens, dict)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        expect(
            client.put(
                "/api/v1/profiles/me",
                headers=headers,
                json={
                    "birth_date": "2000-01-01",
                    "dietary_pattern": "vegetarian",
                    "allergens": ["milk"],
                },
            )
        )
        foods = expect(client.get("/api/v1/foods", params={"query": "lentils"}, headers=headers))
        assert isinstance(foods, list) and foods
        today = date.today().isoformat()
        meal = expect(
            client.post(
                "/api/v1/meals",
                headers=headers,
                json={
                    "name": "Automated demo meal",
                    "eaten_at": datetime.now(UTC).isoformat(),
                    "local_date": today,
                    "ingredients": [{"food_id": foods[0]["id"], "quantity_g": "100"}],
                },
            )
        )
        assert isinstance(meal, dict)
        summary = expect(
            client.get("/api/v1/twin/summary", params={"as_of": today}, headers=headers)
        )
        recommendations = expect(
            client.get("/api/v1/recommendations", params={"as_of": today}, headers=headers)
        )
        assert isinstance(summary, dict) and isinstance(recommendations, dict)
        print(
            "demo passed: "
            f"nutrients={len(summary['nutrients'])}, "
            f"recommendations={len(recommendations['recommendations'])}, "
            "llm_used=false"
        )
        client.delete(f"/api/v1/meals/{meal['id']}", headers=headers).raise_for_status()


if __name__ == "__main__":
    main()
