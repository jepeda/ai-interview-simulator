"""Feature: lines for unknown claims go to suspense instead of rejecting the whole ERA."""

from remits_testkit import era, get_claim, get_remittances, line, post_era


def get_suspense(client) -> list[dict]:
    response = client.get("/suspense")
    assert response.status_code == 200, response.text
    return response.json()


def match(client, suspense_id: int, claim_number: str):
    return client.post(f"/suspense/{suspense_id}/match", json={"claim_number": claim_number})


def test_unknown_claim_is_parked_and_the_rest_posts(client, make_claim):
    make_claim("HW-1")
    payload = era(line("HW-1", "200.00", "100.00"), line("HW-l2", "200.00", "120.00"), trace="1000738214")

    posted = post_era(client, payload)

    assert get_claim(client, "HW-1")["paid_cents"] == 10000
    [parked] = get_suspense(client)
    assert parked["claim_number"] == "HW-l2"  # exactly as the payer sent it
    assert parked["remittance_id"] == posted["id"]
    assert (parked["payer"], parked["trace_number"], parked["paid_on"]) == ("Aetna", "1000738214", "2026-10-09")
    assert (parked["billed_cents"], parked["paid_cents"]) == (20000, 12000)
    assert [u["claim_number"] for u in posted["unmatched_lines"]] == ["HW-l2"]


def test_remittance_with_parked_money_still_balances(client, make_claim):
    make_claim("HW-1")
    posted = post_era(client, era(line("HW-1", "200.00", "100.00"), line("HW-404", "200.00", "120.00")))

    assert posted["total_paid_cents"] == 22000
    assert posted["posted_cents"] == 10000
    assert posted["suspense_cents"] == 12000
    assert posted["out_of_balance_cents"] == 0
    assert posted["claim_count"] == 1


def test_file_with_only_unknown_claims_is_accepted(client):
    post_era(client, era(line("HW-404", "200.00", "120.00")))

    assert len(get_remittances(client)) == 1
    assert len(get_suspense(client)) == 1


def test_matching_posts_the_line_to_the_claim(client, make_claim):
    make_claim("HW-1")
    make_claim("HW-12")
    posted = post_era(
        client,
        era(
            line("HW-1", "200.00", "100.00"),
            line("HW-l2", "200.00", "138.17", ("CO", "45", "31.83"), ("PR", "3", "30.00")),
            trace="1000738214",
        ),
    )
    [parked] = get_suspense(client)

    response = match(client, parked["id"], "HW-12")

    assert response.status_code == 200, response.text
    claim = response.json()
    assert claim["claim_number"] == "HW-12"
    assert (claim["paid_cents"], claim["patient_resp_cents"], claim["balance_cents"]) == (13817, 3000, 0)
    assert claim["payments"][0]["trace_number"] == "1000738214"
    assert get_suspense(client) == []
    remit = client.get(f"/remittances/{posted['id']}").json()
    assert (remit["posted_cents"], remit["suspense_cents"], remit["out_of_balance_cents"]) == (23817, 0, 0)
    assert remit["unmatched_lines"] == []
    assert remit["claim_count"] == 2


def test_match_errors(client, make_claim):
    make_claim("HW-1")
    make_claim("HW-CIGNA", payer="Cigna")
    post_era(client, era(line("HW-404", "200.00", "120.00")))
    [parked] = get_suspense(client)

    assert match(client, 9999, "HW-1").status_code == 404
    assert match(client, parked["id"], "HW-NOPE").status_code == 404
    assert match(client, parked["id"], "HW-CIGNA").status_code == 422  # it's Aetna's money
    assert match(client, parked["id"], "HW-1").status_code == 200
    assert match(client, parked["id"], "HW-1").status_code == 409  # already matched
    assert get_claim(client, "HW-1")["paid_cents"] == 12000


def test_redelivery_does_not_park_the_line_twice(client, make_claim):
    make_claim("HW-1")
    payload = era(line("HW-1", "200.00", "100.00"), line("HW-404", "200.00", "120.00"))

    post_era(client, payload)
    client.post("/remittances", json=payload)

    assert len(get_suspense(client)) == 1
    assert get_claim(client, "HW-1")["paid_cents"] == 10000
