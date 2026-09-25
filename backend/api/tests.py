from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .auth import issue_token
from .models import AutomationRule, Customer, CustomerPortalToken, DemandHistory, FinanceTaxRule, FleetVehicle, GoodsReceipt, IntegrationConnection, Invoice, MobileTask, Organization, OrganizationInvitation, OrganizationMembership, Payment, PermissionDefinition, PortalAccessLog, Product, Profile, PurchaseOrder, PurchaseOrderStatusEvent, PurchasePlan, PwaDevice, QuotationItem, Quotation, RFQ, RFQOffer, RolePermission, SalesOrder, SalesOrderItem, StockLedgerEntry, StockReservation, SupportTicket, Supplier, SupplierContract, SupplierInvoice, SyncConflict, VehicleFitment, Warehouse, WebhookDelivery, WebhookSubscription


class DemandPlanningApiTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user("manager@example.com", "manager@example.com", "demo123")
        self.manager.profile.role = "manager"
        self.manager.profile.save(update_fields=["role"])
        self.store = User.objects.create_user("store@example.com", "store@example.com", "demo123")
        self.store.profile.role = "store"
        self.store.profile.save(update_fields=["role"])
        self.admin = User.objects.create_user("admin@example.com", "admin@example.com", "demo123")
        self.admin.profile.role = "admin"
        self.admin.profile.save(update_fields=["role"])
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
            response = self.client.get(path, **self.auth_headers(self.admin))
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
            response = self.client.get(path, **self.auth_headers(self.admin))
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
            response = self.client.get(path, **self.auth_headers(self.admin))
            self.assertEqual(response.status_code, 200, path)
            self.assertIn(key, response.json())

    def test_customer_service_sla_endpoint_is_available(self):
        response = self.client.get("/api/customer-service/", **self.auth_headers(self.manager))
        self.assertEqual(response.status_code, 200)
        self.assertIn("tickets", response.json())

    def test_saas_billing_endpoint_is_available(self):
        response = self.client.get("/api/saas-billing/", **self.auth_headers(self.admin))
        self.assertEqual(response.status_code, 200)
        self.assertIn("tenants", response.json())

    def test_observability_endpoint_is_available(self):
        response = self.client.get("/api/observability/", **self.auth_headers(self.admin))
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

    def test_tenant_scope_and_invitation_are_persistent(self):
        tenant_response = self.client.get("/api/tenancy/", **self.auth_headers(self.manager))
        self.assertEqual(tenant_response.status_code, 200)
        organization = Organization.objects.get(slug="default")

        invite_response = self.client.post(
            "/api/tenancy/",
            data={"action": "invite", "email": "newuser@example.com", "role": "store", "approval_limit": 25000},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )
        self.assertEqual(invite_response.status_code, 201)
        self.assertTrue(OrganizationInvitation.objects.filter(organization=organization, email="newuser@example.com").exists())

        other = Organization.objects.create(name="Other Org", slug="other-org")
        other_user = User.objects.create_user("other@example.com", "other@example.com", "demo123")
        other_user.profile.role = "manager"
        other_user.profile.save(update_fields=["role"])
        OrganizationMembership.objects.create(organization=other, user=other_user, role="manager")
        self.client.post(
            "/api/fleet/",
            data={"action": "vehicle", "registration": "OTHER 0001", "customer": "Other Customer", "make": "Other", "model": "Van", "next_service": "2030-01-01"},
            content_type="application/json",
            **self.auth_headers(other_user),
        )
        visible = self.client.get("/api/fleet/", **self.auth_headers(self.manager)).json()["vehicles"]
        self.assertFalse(any(item["registration"] == "OTHER 0001" for item in visible))

    def test_stock_ledger_is_idempotent_and_reservation_is_not_double_counted(self):
        response = self.client.post(
            "/api/stock/",
            data={"sku": "TEST-001", "type": "in", "quantity": 4, "reference": "RECEIPT-1", "idempotency_key": "stock-key-1"},
            content_type="application/json",
            **self.auth_headers(self.store),
        )
        self.assertEqual(response.status_code, 201)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 6)
        repeat = self.client.post(
            "/api/stock/",
            data={"sku": "TEST-001", "type": "in", "quantity": 4, "reference": "RECEIPT-1", "idempotency_key": "stock-key-1"},
            content_type="application/json",
            **self.auth_headers(self.store),
        )
        self.assertEqual(repeat.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 6)
        self.assertEqual(StockLedgerEntry.objects.filter(idempotency_key="stock-key-1").count(), 1)

        order = SalesOrder.objects.create(order_no="SO-TEST-001", customer_name="Test Customer", total=100, created_by=self.manager)
        SalesOrderItem.objects.create(sales_order=order, product=self.product, quantity=1, unit_price=100, line_total=100)
        for _ in range(2):
            reserve = self.client.post(
                "/api/fulfillment/",
                data={"action": "reserve", "order_id": order.id, "idempotency_key": "reserve-key-1"},
                content_type="application/json",
                **self.auth_headers(self.manager),
            )
            self.assertEqual(reserve.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.reserved_qty, 1)
        self.assertEqual(StockReservation.objects.filter(sales_order=order, status="active").count(), 1)

    def test_quote_line_items_calculate_tax_and_convert_to_order(self):
        response = self.client.post(
            "/api/quotations/",
            data={"customer_name": "Line Customer", "customer_company": "Line Co", "valid_until": "2030-01-01", "status": "approved", "tax_rate": 18, "items": [{"sku": "TEST-001", "quantity": 2, "unit_price": 100}]},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )
        self.assertEqual(response.status_code, 201)
        quote = response.json()["item"]
        self.assertEqual(quote["subtotal"], 200.0)
        self.assertEqual(quote["tax_total"], 36.0)
        self.assertEqual(quote["total"], 236.0)
        self.assertEqual(QuotationItem.objects.filter(quotation_id=quote["id"]).count(), 1)

        converted = self.client.post(
            "/api/sales-flow/",
            data={"action": "convert_quote", "quote_id": quote["id"]},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )
        self.assertEqual(converted.status_code, 201)
        self.assertEqual(converted.json()["item"]["items"][0]["sku"], "TEST-001")

    def test_customer_portal_cannot_access_another_customer_record(self):
        customer = Customer.objects.create(name="Portal Customer", company="Portal Co", email="portal@example.com")
        token = CustomerPortalToken.objects.create(token="portal-test-token", customer=customer, expires_at=timezone.now() + timedelta(days=1), created_by=self.manager)
        quote = Quotation.objects.create(quote_no="QT-PORTAL-001", customer_name="Other Customer", customer_company="Other Co", total=100, valid_until=date.today() + timedelta(days=7), created_by=self.manager)
        response = self.client.post(
            "/api/portal/",
            data={"token": token.token, "action": "approve_quote", "quote_id": quote.id},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        quote.refresh_from_db()
        self.assertEqual(quote.status, "draft")
        self.assertFalse(PortalAccessLog.objects.filter(portal_token=token, action="approve_quote").exists())

    def test_inventory_search_pagination_and_csv_import(self):
        search = self.client.get("/api/inventory/?q=TEST&page=1&page_size=1", **self.auth_headers(self.manager))
        self.assertEqual(search.status_code, 200)
        self.assertEqual(search.json()["items"][0]["sku"], "TEST-001")
        self.assertEqual(search.json()["page_size"], 1)
        imported = self.client.post(
            "/api/inventory/",
            data={"action": "import", "rows": "sku,name,brand,category,price,stock_qty\nIMP-001,Imported Relay,VoltEdge,electrical,180,4"},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )
        self.assertEqual(imported.status_code, 201)
        self.assertEqual(imported.json()["summary"]["created"], 1)
        self.assertTrue(Product.objects.filter(sku="IMP-001", stock_qty=4).exists())

    def test_purchase_order_reports_progress_and_status_history(self):
        response = self.client.post(
            "/api/purchase-orders/",
            data={"supplier": self.supplier.name, "sku": self.product.sku, "quantity": 10, "unit_cost": 60, "status": "ordered"},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )
        self.assertEqual(response.status_code, 201)
        po_id = response.json()["item"]["id"]
        self.assertEqual(PurchaseOrderStatusEvent.objects.filter(purchase_order_id=po_id).count(), 1)

        receive = self.client.post(
            "/api/purchase-orders/",
            data={"action": "receive", "id": po_id},
            content_type="application/json",
            **self.auth_headers(self.store),
        )
        self.assertEqual(receive.status_code, 200)
        item = self.client.get("/api/purchase-orders/", **self.auth_headers(self.manager)).json()["items"][0]
        self.assertEqual(item["progress"], 100)
        self.assertEqual(len(item["events"]), 2)

    def test_integration_health_check_and_signed_webhook_delivery(self):
        connection = self.client.post(
            "/api/integrations/",
            data={"action": "connect", "name": "Test ERP", "type": "accounting", "secret": "credential-value"},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )
        self.assertEqual(connection.status_code, 201)
        integration = IntegrationConnection.objects.get(name="Test ERP")
        self.assertNotEqual(integration.credential_digest, "credential-value")

        health = self.client.post(
            "/api/integrations/",
            data={"action": "test", "id": integration.id},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["item"]["status"], "connected")

        webhook = self.client.post(
            "/api/integrations/",
            data={"action": "webhook", "event": "invoice.paid", "target": "https://example.test/hook", "secret": "webhook-secret"},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )
        self.assertEqual(webhook.status_code, 201)
        subscription = WebhookSubscription.objects.get(id=webhook.json()["item"]["id"])
        delivered = self.client.post(
            "/api/integrations/",
            data={"action": "deliver", "webhook_id": subscription.id, "payload": {"invoice": "INV-1"}},
            content_type="application/json",
            **self.auth_headers(self.manager),
        )
        self.assertEqual(delivered.status_code, 200)
        self.assertEqual(WebhookDelivery.objects.filter(subscription=subscription, status="delivered").count(), 1)
        self.assertEqual(subscription.__class__.objects.get(id=subscription.id).deliveries, 1)

    def test_mobile_queue_is_durable_idempotent_and_cursor_based(self):
        payload = {"action": "scan", "device_key": "scanner-01", "device_name": "Receiving scanner", "type": "count", "sku": "TEST-001", "quantity": 3, "idempotency_key": "mobile-key-1"}
        first = self.client.post("/api/mobile-warehouse/", data=payload, content_type="application/json", **self.auth_headers(self.store))
        repeat = self.client.post("/api/mobile-warehouse/", data=payload, content_type="application/json", **self.auth_headers(self.store))
        self.assertEqual(first.status_code, 201)
        self.assertEqual(repeat.status_code, 200)
        self.assertEqual(MobileTask.objects.filter(idempotency_key="mobile-key-1").count(), 1)

        sync = self.client.post("/api/mobile-warehouse/", data={"action": "sync", "device_key": "scanner-01"}, content_type="application/json", **self.auth_headers(self.store))
        self.assertEqual(sync.status_code, 200)
        self.assertEqual(sync.json()["item"]["synced_count"], 1)
        self.assertEqual(PwaDevice.objects.get(device_key="scanner-01").sync_cursor, 1)

        conflict = self.client.post("/api/mobile-warehouse/", data={"action": "conflict", "device_key": "scanner-01", "reference": "COUNT-1", "field": "quantity", "local_value": "4", "server_value": "3"}, content_type="application/json", **self.auth_headers(self.store))
        self.assertEqual(conflict.status_code, 201)
        self.assertTrue(SyncConflict.objects.filter(reference="COUNT-1", status="needs_review").exists())

    def test_finance_date_filter_aging_tax_rules_and_reconciliation(self):
        FinanceTaxRule.objects.create(name="GST 18", rate=18, effective_from=date.today() - timedelta(days=30))
        order = SalesOrder.objects.create(order_no="SO-FIN-001", customer_name="Finance Customer", total=1180, created_by=self.manager)
        invoice = Invoice.objects.create(invoice_no="INV-FIN-001", sales_order=order, total=1180, tax_rate=18, due_date=date.today() - timedelta(days=40))
        Payment.objects.create(invoice=invoice, amount=100, method="bank", reference="BANK-001", created_by=self.manager)
        response = self.client.get(f"/api/finance/?from={date.today().isoformat()}&to={date.today().isoformat()}", **self.auth_headers(self.manager))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["invoices"]), 1)
        self.assertEqual(payload["invoices"][0]["gst"], 180.0)
        self.assertEqual(payload["aging"]["31_60"], 1080.0)
        self.assertEqual(payload["tax_rules"][0]["rate"], 18.0)
        export = self.client.post("/api/finance/", data={"action": "export"}, content_type="application/json", **self.auth_headers(self.manager))
        self.assertEqual(export.status_code, 200)
        self.assertIn("INV-FIN-001", export.json()["item"]["rows"][1])

    def test_role_matrix_limits_workspaces_and_admin_role_changes(self):
        sales_login = self.client.post("/api/auth/login/", data={"email": "manager@example.com", "password": "demo123"}, content_type="application/json")
        self.assertEqual(sales_login.status_code, 200)
        self.assertIn("integrations", sales_login.json()["modules"])
        self.assertNotIn("security", sales_login.json()["modules"])

        self.assertEqual(self.client.get("/api/security/", **self.auth_headers(self.manager)).status_code, 403)
        self.assertEqual(self.client.get("/api/stock/", **self.auth_headers(self.manager)).status_code, 200)
        self.assertEqual(self.client.get("/api/quotations/", **self.auth_headers(self.store)).status_code, 403)

        change = self.client.post("/api/tenancy/", data={"action": "role", "user_id": self.store.id, "role": "sales"}, content_type="application/json", **self.auth_headers(self.admin))
        self.assertEqual(change.status_code, 200)
        self.assertEqual(self.store.organization_memberships.first().role, "sales")

    def test_permission_matrix_is_returned_and_can_be_overridden(self):
        response = self.client.post("/api/auth/login/", data={"email": "manager@example.com", "password": "demo123"}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["permissions"]["finance:approve"])
        self.assertFalse(response.json()["permissions"]["security:view"])
        self.assertTrue(PermissionDefinition.objects.filter(module="finance", action="approve").exists())
        self.assertTrue(RolePermission.objects.filter(role="manager", permission__module="finance", allowed=True).exists())

    def test_admin_can_edit_permission_matrix_but_manager_cannot(self):
        denied = self.client.post("/api/permissions/", data={"action": "update", "role": "sales", "module": "finance", "permission": "export", "allowed": True}, content_type="application/json", **self.auth_headers(self.manager))
        self.assertEqual(denied.status_code, 403)
        allowed = self.client.post("/api/permissions/", data={"action": "update", "role": "sales", "module": "finance", "permission": "export", "allowed": True}, content_type="application/json", **self.auth_headers(self.admin))
        self.assertEqual(allowed.status_code, 200)
        self.assertTrue(allowed.json()["item"]["allowed"])

    def test_membership_branch_scope_is_enforced(self):
        self.client.get("/api/warehouses/", **self.auth_headers(self.store))
        organization = self.store.organization_memberships.first().organization
        primary = Warehouse.objects.create(code="DEL-BRANCH", name="Delhi Branch", organization=organization)
        other = Warehouse.objects.create(code="GUR-BRANCH", name="Gurugram Branch", organization=organization)
        membership = self.store.organization_memberships.first()
        membership.primary_branch = primary
        membership.all_branches = False
        membership.save(update_fields=["primary_branch", "all_branches"])
        allowed = self.client.get("/api/warehouses/", HTTP_X_PARTORA_BRANCH="DEL-BRANCH", **self.auth_headers(self.store))
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual([item["code"] for item in allowed.json()["warehouses"]], ["DEL-BRANCH"])
        denied = self.client.get("/api/warehouses/", HTTP_X_PARTORA_BRANCH="GUR-BRANCH", **self.auth_headers(self.store))
        self.assertEqual(denied.status_code, 403)
