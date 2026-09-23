from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from .auth import issue_token
from .models import DemandHistory, Product, Profile, PurchaseOrder, PurchasePlan, Supplier


class DemandPlanningApiTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user("manager@example.com", "manager@example.com", "demo123")
        self.manager.profile.role = "manager"
        self.manager.profile.save(update_fields=["role"])
        self.store = User.objects.create_user("store@example.com", "store@example.com", "demo123")
        self.store.profile.role = "store"
        self.store.profile.save(update_fields=["role"])
        self.supplier = Supplier.objects.create(name="Test Components", lead_time_days=3, rating=4.5)
        self.product = Product.objects.create(
            sku="TEST-001", name="Test Filter", brand="TestBrand", category="auto", supplier=self.supplier,
            price=100, cost_price=60, stock_qty=2, reorder_level=10, reorder_qty=20,
        )
        for days_ago, quantity in ((60, 30), (30, 30), (0, 30)):
            DemandHistory.objects.create(product=self.product, period_start=date.today() - timedelta(days=days_ago), quantity=quantity)

    def auth_headers(self, user):
        return {"HTTP_AUTHORIZATION": f"Bearer {issue_token(user)}"}

    def test_forecast_returns_risk_and_recommendation(self):
        response = self.client.get("/api/demand-planning/", **self.auth_headers(self.manager))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["window_days"], 90)
        self.assertEqual(payload["summary"]["at_risk"], 1)
        self.assertEqual(payload["items"][0]["sku"], "TEST-001")
        self.assertGreater(payload["items"][0]["recommended_qty"], 0)
        self.assertEqual(payload["items"][0]["risk"], "urgent")

    def test_store_requests_and_manager_approves_purchase_plan(self):
        request_response = self.client.post(
            "/api/demand-planning/",
            data={"action": "request", "sku": "TEST-001"},
            content_type="application/json",
            **self.auth_headers(self.store),
        )

        self.assertEqual(request_response.status_code, 201)
        plan_id = request_response.json()["item"]["id"]
        self.assertEqual(PurchasePlan.objects.get(id=plan_id).status, "pending")

        approve_response = self.client.post(
            "/api/demand-planning/",
            data={"action": "approve", "id": plan_id},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )

        self.assertEqual(approve_response.status_code, 200)
        plan = PurchasePlan.objects.get(id=plan_id)
        self.assertEqual(plan.status, "ordered")
        self.assertIsNotNone(plan.purchase_order_id)
        self.assertEqual(PurchaseOrder.objects.count(), 1)

    def test_store_cannot_approve_purchase_plan(self):
        plan = PurchasePlan.objects.create(
            product=self.product, supplier=self.supplier, recommended_qty=20, unit_cost=60,
            estimated_cost=1200, expected_date=date.today() + timedelta(days=3), requested_by=self.store,
        )

        response = self.client.post(
            "/api/demand-planning/",
            data={"action": "approve", "id": plan.id},
            content_type="application/json",
            **self.auth_headers(self.store),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(PurchaseOrder.objects.count(), 0)
