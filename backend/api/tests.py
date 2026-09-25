from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from .auth import issue_token
from .models import AutomationRule, DemandHistory, FleetVehicle, GoodsReceipt, IntegrationConnection, Product, Profile, PurchaseOrder, PurchasePlan, RFQ, RFQOffer, SupportTicket, Supplier, SupplierContract, SupplierInvoice, VehicleFitment


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

    def test_rfq_compares_quotes_and_manager_selects_offer_into_po(self):
        second_supplier = Supplier.objects.create(name="Alternate Components", lead_time_days=2, rating=4.2)
        create_response = self.client.post(
            "/api/rfq/",
            data={"action": "create", "sku": "TEST-001", "quantity": 20, "suppliers": [str(self.supplier.id), str(second_supplier.id)]},
            content_type="application/json",
            **self.auth_headers(self.store),
        )

        self.assertEqual(create_response.status_code, 201)
        rfq = RFQ.objects.get(id=create_response.json()["item"]["id"])
        offers = list(rfq.offers.order_by("id"))
        self.assertEqual(len(offers), 2)

        for offer, price in zip(offers, (60, 58)):
            response = self.client.post(
                "/api/rfq/",
                data={"action": "quote", "offer_id": offer.id, "unit_price": price, "lead_time_days": offer.supplier.lead_time_days, "moq": 5, "available_qty": 50, "payment_terms": "Net 30"},
                content_type="application/json",
                **self.auth_headers(self.store),
            )
            self.assertEqual(response.status_code, 200)

        select_response = self.client.post(
            "/api/rfq/",
            data={"action": "select", "offer_id": offers[1].id},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )

        self.assertEqual(select_response.status_code, 200)
        rfq.refresh_from_db()
        self.assertEqual(rfq.status, "selected")
        self.assertEqual(PurchaseOrder.objects.count(), 1)
        self.assertEqual(rfq.offers.get(status="selected").supplier_id, second_supplier.id)
        self.assertEqual(rfq.offers.filter(status="rejected").count(), 1)

    def test_receiving_updates_stock_and_three_way_matches_supplier_invoice(self):
        po = PurchaseOrder.objects.create(
            po_no="PO-TEST-001", supplier=self.supplier, status="ordered", total=1000,
            created_by=self.manager,
        )
        from .models import PurchaseOrderItem
        line = PurchaseOrderItem.objects.create(purchase_order=po, product=self.product, quantity=10, unit_cost=100)

        receipt_response = self.client.post(
            "/api/receiving/",
            data={"action": "receive", "po_id": po.id, "lines": [{"item_id": line.id, "accepted_qty": 8, "damaged_qty": 1}]},
            content_type="application/json",
            **self.auth_headers(self.store),
        )

        self.assertEqual(receipt_response.status_code, 201)
        po.refresh_from_db(); self.product.refresh_from_db()
        self.assertEqual(po.status, "partial")
        self.assertEqual(po.items.get().received_qty, 9)
        self.assertEqual(self.product.stock_qty, 10)
        self.assertEqual(GoodsReceipt.objects.count(), 1)

        invoice_response = self.client.post(
            "/api/receiving/",
            data={"action": "invoice", "po_id": po.id, "invoice_no": "SUP-INV-001", "invoice_qty": 8, "subtotal": 800, "total": 800},
            content_type="application/json",
            **self.auth_headers(self.store),
        )

        self.assertEqual(invoice_response.status_code, 201)
        invoice = SupplierInvoice.objects.get(invoice_no="SUP-INV-001")
        self.assertEqual(invoice.status, "matched")

        approve_response = self.client.post(
            "/api/receiving/",
            data={"action": "approve", "invoice_id": invoice.id},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )

        self.assertEqual(approve_response.status_code, 200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "approved")

    def test_vin_decode_returns_compatible_stock_aware_parts(self):
        VehicleFitment.objects.create(product=self.product, make="Maruti Suzuki", model="Swift", year_from=2018, year_to=2026, variant="Petrol / AMT", engine="1.2L", oem_number="OEM-TEST-001")

        response = self.client.post(
            "/api/fitments/",
            data={"action": "decode_vin", "vin": "MA3EJKD1S00A12345"},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )

        self.assertEqual(response.status_code, 200)
        item = response.json()["item"]
        self.assertEqual(item["vehicle"]["model"], "Swift")
        self.assertEqual(item["matches"][0]["sku"], "TEST-001")
        self.assertEqual(item["matches"][0]["stock_status"], "low")

    def test_supplier_intelligence_returns_contract_watchlist(self):
        SupplierContract.objects.create(contract_no="TEST-CONTRACT-001", supplier=self.supplier, expires_on=date.today() + timedelta(days=30), payment_terms="Net 30", annual_value=50000, status="expiring")

        response = self.client.get("/api/supplier-performance/", **self.auth_headers(self.manager))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["contracts"][0]["contract_no"], "TEST-CONTRACT-001")

    def test_client_demo_operations_endpoints_are_available(self):
        for path in ("/api/mobile-warehouse/", "/api/notifications/", "/api/finance/", "/api/warranty/"):
            response = self.client.get(path, **self.auth_headers(self.manager))
            self.assertEqual(response.status_code, 200, path)

        response = self.client.post(
            "/api/copilot/",
            data={"question": "Which parts may stock out this week?"},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("RLY-24V4", response.json()["item"]["answer"])

    def test_deployability_suite_endpoints_are_available(self):
        for path, key in (
            ("/api/integrations/", "connections"),
            ("/api/pwa-admin/", "devices"),
            ("/api/tenancy/", "branches"),
            ("/api/automation/", "rules"),
            ("/api/fleet/", "vehicles"),
        ):
            response = self.client.get(path, **self.auth_headers(self.manager))
            self.assertEqual(response.status_code, 200, path)
            self.assertIn(key, response.json())

    def test_security_ai_delivery_partner_and_predictive_endpoints_are_available(self):
        for path, key in (
            ("/api/security/", "users"),
            ("/api/documents/", "documents"),
            ("/api/delivery/", "shipments"),
            ("/api/partner-api/", "keys"),
            ("/api/predictive-fleet/", "vehicles"),
        ):
            response = self.client.get(path, **self.auth_headers(self.manager))
            self.assertEqual(response.status_code, 200, path)
            self.assertIn(key, response.json())

    def test_customer_service_sla_endpoint_is_available(self):
        response = self.client.get("/api/customer-service/", **self.auth_headers(self.manager))
        self.assertEqual(response.status_code, 200)
        self.assertIn("tickets", response.json())

    def test_saas_billing_endpoint_is_available(self):
        response = self.client.get("/api/saas-billing/", **self.auth_headers(self.manager))
        self.assertEqual(response.status_code, 200)
        self.assertIn("tenants", response.json())

    def test_observability_endpoint_is_available(self):
        response = self.client.get("/api/observability/", **self.auth_headers(self.manager))
        self.assertEqual(response.status_code, 200)
        self.assertIn("services", response.json())

    def test_inventory_network_endpoint_is_available(self):
        response = self.client.get("/api/inventory-network/", **self.auth_headers(self.manager))
        self.assertEqual(response.status_code, 200)
        self.assertIn("recommendations", response.json())

    def test_enterprise_actions_persist_after_reload(self):
        integration_response = self.client.post(
            "/api/integrations/",
            data={"action": "connect", "name": "Test ERP", "type": "accounting"},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )
        self.assertEqual(integration_response.status_code, 201)
        self.assertTrue(IntegrationConnection.objects.filter(name="Test ERP").exists())
        self.assertTrue(any(item["name"] == "Test ERP" for item in self.client.get("/api/integrations/", **self.auth_headers(self.manager)).json()["connections"]))

        fleet_response = self.client.post(
            "/api/fleet/",
            data={"action": "vehicle", "registration": "TEST 0001", "customer": "Test Fleet", "make": "Test", "model": "Van", "year": 2024, "mileage": 1000, "next_service": "2030-01-01"},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )
        self.assertEqual(fleet_response.status_code, 201)
        self.assertTrue(FleetVehicle.objects.filter(registration="TEST 0001").exists())

        ticket_response = self.client.post(
            "/api/customer-service/",
            data={"action": "ticket", "customer": "Test Fleet", "subject": "Test support request", "sla_due": "2030-01-01 12:00"},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )
        self.assertEqual(ticket_response.status_code, 201)
        self.assertTrue(SupportTicket.objects.filter(subject="Test support request").exists())

        rule_response = self.client.post(
            "/api/automation/",
            data={"action": "rule", "name": "Test rule", "trigger": "test.event", "rule_action": "Send test notification"},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )
        self.assertEqual(rule_response.status_code, 201)
        self.assertTrue(AutomationRule.objects.filter(name="Test rule").exists())
